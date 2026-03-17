import uuid
from pathlib import Path
from typing import List

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..dependencies import get_current_user, get_db, get_model_service
from ..schemas.common import ApiResponse
from ..schemas.prediction import PredictResponse
from ..services import history_service
from ..services.model_service import ModelService
from ..utils.errors import bad_request

router = APIRouter(prefix="/api/predict", tags=["predict"])


async def _save_upload(file: UploadFile) -> tuple[str, str, Image.Image]:
    """Save uploaded file, return (filename, url, PIL Image)."""
    content = await file.read()
    ext = Path(file.filename).suffix or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"

    upload_dir = settings.upload_dir
    upload_dir.mkdir(parents=True, exist_ok=True)
    filepath = upload_dir / filename

    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)

    try:
        image = Image.open(filepath).convert("RGB")
    except (UnidentifiedImageError, Exception):
        filepath.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="上传文件不是有效图片")

    url = f"/api/static/uploads/{filename}"
    return filename, url, image


def _validate_top_k(top_k: int) -> int:
    if top_k < 1 or top_k > settings.MAX_TOP_K:
        raise bad_request(f"top_k 必须在 1~{settings.MAX_TOP_K} 范围内")
    return top_k


@router.post("", response_model=ApiResponse[PredictResponse])
async def predict_single(
    file: UploadFile = File(...),
    top_k: int = settings.TOP_K,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
    svc: ModelService = Depends(get_model_service),
):
    top_k = _validate_top_k(top_k)
    filename, url, image = await _save_upload(file)
    result = svc.predict(image, top_k)

    await history_service.create_record(
        db,
        user_id=user.id,
        image_filename=filename,
        image_url=url,
        top1_class=result.best_prediction.class_name if result.best_prediction else "",
        top1_confidence=result.best_prediction.confidence if result.best_prediction else 0,
        top_k=result.top_k,
        results_json=[p.model_dump() for p in result.predictions],
    )
    return ApiResponse(data=result)


@router.post("/batch", response_model=ApiResponse[List[PredictResponse]])
async def predict_batch(
    files: List[UploadFile] = File(...),
    top_k: int = settings.TOP_K,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
    svc: ModelService = Depends(get_model_service),
):
    top_k = _validate_top_k(top_k)
    if len(files) < 1:
        raise bad_request("请至少上传 1 张图片")
    if len(files) > settings.MAX_BATCH_SIZE:
        raise bad_request(f"最多同时上传 {settings.MAX_BATCH_SIZE} 张图片")

    results: List[PredictResponse] = []
    for file in files:
        filename, url, image = await _save_upload(file)
        result = svc.predict(image, top_k)
        await history_service.create_record(
            db,
            user_id=user.id,
            image_filename=filename,
            image_url=url,
            top1_class=result.best_prediction.class_name if result.best_prediction else "",
            top1_confidence=result.best_prediction.confidence if result.best_prediction else 0,
            top_k=result.top_k,
            results_json=[p.model_dump() for p in result.predictions],
        )
        results.append(result)

    return ApiResponse(data=results)
