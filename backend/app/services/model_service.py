from pathlib import Path
from typing import Any, List

import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms

from ..config import settings
from ..schemas.prediction import PredictionItem, PredictResponse
from ..utils.class_names import load_class_names, to_display_name


class ModelService:
    def __init__(self) -> None:
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.class_names: List[str] = []
        self.class_names_source: str = ""
        self.model_path: str = ""
        self.model: nn.Module | None = None
        self.preprocess = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def load(self, model_path: Path | None = None, class_names_path: Path | None = None) -> None:
        resolved_model_path = (model_path or settings.model_path).expanduser()
        if not resolved_model_path.is_absolute():
            resolved_model_path = settings.BASE_DIR / resolved_model_path
        resolved_model_path = resolved_model_path.resolve()

        resolved_class_names_path = class_names_path.expanduser().resolve() if class_names_path is not None else None
        class_names, source_path = load_class_names(class_names_path=resolved_class_names_path)

        if not resolved_model_path.exists():
            raise FileNotFoundError(f"模型权重文件不存在: {resolved_model_path}")

        model = models.resnet50(weights=None)
        in_features = model.fc.in_features
        model.fc = nn.Sequential(nn.Dropout(0.5), nn.Linear(in_features, len(class_names)))

        state_dict = torch.load(resolved_model_path, map_location=self.device)
        model.load_state_dict(state_dict)
        model.to(self.device)
        model.eval()

        self.class_names = class_names
        self.class_names_source = str(source_path)
        self.model_path = str(resolved_model_path)
        self.model = model

    def predict(self, image: Image.Image, top_k: int = 5) -> PredictResponse:
        if self.model is None or not self.class_names:
            raise RuntimeError("模型尚未加载，请检查模型权重与数据集目录")
        input_tensor = self.preprocess(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            logits = self.model(input_tensor)
            probs = torch.softmax(logits, dim=1)

        top_k = min(top_k, len(self.class_names))
        values, indices = torch.topk(probs, k=top_k, dim=1)

        predictions: List[PredictionItem] = []
        for score, idx in zip(values[0].tolist(), indices[0].tolist()):
            predictions.append(PredictionItem(
                class_index=idx,
                class_name=self.class_names[idx],
                display_name=to_display_name(self.class_names[idx]),
                confidence=round(score, 6),
            ))

        return PredictResponse(
            top_k=top_k,
            predictions=predictions,
            best_prediction=predictions[0] if predictions else None,
        )

    def runtime_info(self) -> dict[str, Any]:
        return {
            "model_path": self.model_path,
            "class_names_source": self.class_names_source,
            "class_count": len(self.class_names),
            "device": str(self.device),
            "loaded": self.model is not None and bool(self.class_names),
        }


model_service = ModelService()
