from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path
from typing import List
import uuid

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..dependencies import get_db, get_model_service, require_permissions
from ..schemas.common import ApiResponse
from ..schemas.diagnosis import DiagnosisDraftOut
from ..schemas.prediction import PredictResponse
from ..services import case_service, history_service, knowledge_service
from ..services import advice_service
from ..services.model_service import ModelService
from ..utils.label_parser import parse_label
from ..utils.errors import bad_request

router = APIRouter(prefix="/api/predict", tags=["predict"])


@dataclass
class SavedUpload:
    filename: str
    url: str
    image: Image.Image
    filepath: Path
    size_bytes: int


def _guess_url(subdir: str | None, filename: str) -> str:
    if subdir:
        return f"/api/static/uploads/{subdir}/{filename}"
    return f"/api/static/uploads/{filename}"


def _payload_too_large(message: str) -> HTTPException:
    return HTTPException(status_code=413, detail=message)


def _cleanup_file(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def _cleanup_saved_uploads(saved_uploads: List[SavedUpload]) -> None:
    for saved in saved_uploads:
        try:
            saved.image.close()
        except Exception:
            pass
        _cleanup_file(saved.filepath)


def _cleanup_expired_draft_uploads() -> None:
    drafts_dir = settings.upload_dir / "drafts"
    if not drafts_dir.exists():
        return
    expire_before = datetime.now() - timedelta(minutes=settings.DIAGNOSIS_DRAFT_EXPIRE_MINUTES)
    for path in drafts_dir.glob("*"):
        try:
            if path.is_file() and datetime.fromtimestamp(path.stat().st_mtime) < expire_before:
                path.unlink(missing_ok=True)
        except OSError:
            continue


async def _save_upload(file: UploadFile, *, subdir: str | None = None) -> SavedUpload:
    """Stream upload to disk, return validated image payload."""
    ext = Path(file.filename or "").suffix or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"

    upload_dir = settings.upload_dir
    if subdir:
        upload_dir = upload_dir / subdir
    upload_dir.mkdir(parents=True, exist_ok=True)
    filepath = upload_dir / filename
    size_bytes = 0

    try:
        async with aiofiles.open(filepath, "wb") as f:
            while True:
                chunk = await file.read(settings.UPLOAD_CHUNK_SIZE)
                if not chunk:
                    break
                size_bytes += len(chunk)
                if size_bytes > settings.max_upload_size_bytes:
                    raise _payload_too_large(
                        f"单个文件大小不能超过 {settings.MAX_UPLOAD_SIZE_MB}MB"
                    )
                await f.write(chunk)
    except Exception:
        _cleanup_file(filepath)
        raise
    finally:
        await file.close()

    try:
        with Image.open(filepath) as opened:
            image = opened.convert("RGB")
    except (UnidentifiedImageError, Exception):
        _cleanup_file(filepath)
        raise HTTPException(status_code=400, detail="上传文件不是有效图片")

    url = _guess_url(subdir, filename)
    return SavedUpload(
        filename=f"{subdir}/{filename}" if subdir else filename,
        url=url,
        image=image,
        filepath=filepath,
        size_bytes=size_bytes,
    )


def _validate_top_k(top_k: int) -> int:
    if top_k < 1 or top_k > settings.MAX_TOP_K:
        raise bad_request(f"top_k 必须在 1~{settings.MAX_TOP_K} 范围内")
    return top_k


@router.post("/diagnose", response_model=ApiResponse[DiagnosisDraftOut])
async def diagnose_single(
    file: UploadFile = File(...),
    top_k: int = settings.TOP_K,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permissions("predict:single")),
    svc: ModelService = Depends(get_model_service),
):
    _cleanup_expired_draft_uploads()
    top_k = _validate_top_k(top_k)
    saved = await _save_upload(file, subdir="drafts")
    try:
        result = svc.predict(saved.image, top_k)
        best_prediction = result.best_prediction
        if best_prediction is None:
            raise bad_request("模型未返回有效预测结果")
        knowledge_evidence = await knowledge_service.search_knowledge(
            db, best_prediction.class_name, settings.DIAGNOSIS_EVIDENCE_LIMIT
        )
        similar_cases = await case_service.search_similar_cases(
            db, best_prediction.class_name, settings.SIMILAR_CASE_LIMIT
        )
        advice = await advice_service.generate_advice(
            best_prediction,
            result.predictions,
            knowledge_evidence,
            similar_cases,
        )
        profile = parse_label(best_prediction.class_name)
        draft_token = case_service.create_draft_token(
            user_id=user.id,
            image_filename=saved.filename,
            image_url=saved.url,
            top_k=result.top_k,
            predictions=result.predictions,
        )
        response = DiagnosisDraftOut(
            draft_token=draft_token,
            image_url=saved.url,
            image_filename=saved.filename,
            crop_name=profile.crop_name,
            health_status=profile.health_status,
            top_k=result.top_k,
            predictions=result.predictions,
            best_prediction=best_prediction,
            knowledge_evidence=knowledge_evidence,
            similar_cases=similar_cases,
            advice=advice,
        )
    except Exception:
        _cleanup_saved_uploads([saved])
        raise
    finally:
        saved.image.close()

    return ApiResponse(data=response)


@router.post("", response_model=ApiResponse[PredictResponse])
async def predict_single(
    file: UploadFile = File(...),
    top_k: int = settings.TOP_K,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permissions("predict:single")),
    svc: ModelService = Depends(get_model_service),
):
    top_k = _validate_top_k(top_k)
    saved = await _save_upload(file)
    try:
        result = svc.predict(saved.image, top_k)
        await history_service.create_record(
            db,
            user_id=user.id,
            image_filename=saved.filename,
            image_url=saved.url,
            top1_class=result.best_prediction.class_name if result.best_prediction else "",
            top1_confidence=result.best_prediction.confidence if result.best_prediction else 0,
            top_k=result.top_k,
            results_json=[p.model_dump() for p in result.predictions],
        )
    except Exception:
        _cleanup_saved_uploads([saved])
        raise
    finally:
        saved.image.close()

    return ApiResponse(data=result)


@router.post("/batch", response_model=ApiResponse[List[PredictResponse]])
async def predict_batch(
    files: List[UploadFile] = File(...),
    top_k: int = settings.TOP_K,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permissions("predict:batch")),
    svc: ModelService = Depends(get_model_service),
):
    top_k = _validate_top_k(top_k)
    if len(files) < 1:
        raise bad_request("请至少上传 1 张图片")
    if len(files) > settings.MAX_BATCH_SIZE:
        raise bad_request(f"最多同时上传 {settings.MAX_BATCH_SIZE} 张图片")

    saved_uploads: List[SavedUpload] = []
    total_size = 0
    try:
        for file in files:
            saved = await _save_upload(file)
            saved_uploads.append(saved)
            total_size += saved.size_bytes
            if total_size > settings.max_batch_total_size_bytes:
                raise _payload_too_large(
                    f"批量上传总大小不能超过 {settings.MAX_BATCH_TOTAL_SIZE_MB}MB"
                )
    except Exception:
        _cleanup_saved_uploads(saved_uploads)
        raise

    results: List[PredictResponse] = []
    created_count = 0
    try:
        for saved in saved_uploads:
            result = svc.predict(saved.image, top_k)
            await history_service.create_record(
                db,
                user_id=user.id,
                image_filename=saved.filename,
                image_url=saved.url,
                top1_class=result.best_prediction.class_name if result.best_prediction else "",
                top1_confidence=result.best_prediction.confidence if result.best_prediction else 0,
                top_k=result.top_k,
                results_json=[p.model_dump() for p in result.predictions],
            )
            results.append(result)
            created_count += 1
    except Exception:
        _cleanup_saved_uploads(saved_uploads[created_count:])
        raise
    finally:
        for saved in saved_uploads:
            saved.image.close()

    return ApiResponse(data=results)
