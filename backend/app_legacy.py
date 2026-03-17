import os
from pathlib import Path
from typing import List

import torch
import torch.nn as nn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError
from torchvision import models, transforms


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_MODEL_PATH = BASE_DIR / "resnet50_阶段二_(全局微调)_best.pth"
DEFAULT_DATASET_DIR = BASE_DIR / "datasets" / "color"

MODEL_PATH = Path(os.getenv("MODEL_PATH", str(DEFAULT_MODEL_PATH)))
DATASET_DIR = Path(os.getenv("DATASET_DIR", str(DEFAULT_DATASET_DIR)))
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_class_names(dataset_dir: Path) -> List[str]:
    if not dataset_dir.exists():
        raise FileNotFoundError(f"数据集目录不存在: {dataset_dir}")
    class_names = sorted([p.name for p in dataset_dir.iterdir() if p.is_dir()])
    if not class_names:
        raise ValueError(f"数据集目录下未找到类别子目录: {dataset_dir}")
    return class_names


def build_model(num_classes: int) -> nn.Module:
    model = models.resnet50(weights=None)
    in_features = model.fc.in_features
    model.fc = nn.Sequential(
        nn.Dropout(0.5),
        nn.Linear(in_features, num_classes),
    )
    return model


class_names = load_class_names(DATASET_DIR)
model = build_model(num_classes=len(class_names))

if not MODEL_PATH.exists():
    raise FileNotFoundError(f"模型权重文件不存在: {MODEL_PATH}")

state_dict = torch.load(MODEL_PATH, map_location=DEVICE)
model.load_state_dict(state_dict)
model.to(DEVICE)
model.eval()


preprocess = transforms.Compose(
    [
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]
)


app = FastAPI(title="ResNet Inference API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "device": str(DEVICE),
        "model_path": str(MODEL_PATH),
        "num_classes": len(class_names),
    }


@app.get("/classes")
def classes():
    return {
        "num_classes": len(class_names),
        "classes": class_names,
    }


@app.post("/predict")
async def predict(file: UploadFile = File(...), top_k: int = 5):
    if top_k <= 0:
        raise HTTPException(status_code=400, detail="top_k 必须大于 0")

    try:
        image = Image.open(file.file).convert("RGB")
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="上传文件不是有效图片")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"读取图片失败: {exc}")

    input_tensor = preprocess(image).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        logits = model(input_tensor)
        probs = torch.softmax(logits, dim=1)

    top_k = min(top_k, len(class_names))
    values, indices = torch.topk(probs, k=top_k, dim=1)

    predictions = []
    for score, idx in zip(values[0].tolist(), indices[0].tolist()):
        predictions.append(
            {
                "class_index": idx,
                "class_name": class_names[idx],
                "display_name": class_names[idx].replace("___", " - "),
                "confidence": score,
            }
        )

    return {
        "top_k": top_k,
        "predictions": predictions,
        "best_prediction": predictions[0] if predictions else None,
    }
