from typing import List

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..dependencies import get_db, get_model_service, require_permissions
from ..schemas.common import ApiResponse
from ..schemas.diagnosis import DiagnosisDraftOut
from ..schemas.prediction import PredictResponse
from ..services import advice_service, case_service, history_service, knowledge_service, upload_service
from ..services.model_service import ModelService
from ..utils.label_parser import parse_label
from ..utils.errors import bad_request

router = APIRouter(prefix="/api/predict", tags=["predict"])


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
    upload_service.cleanup_expired_uploads(
        subdir="drafts",
        expire_minutes=settings.DIAGNOSIS_DRAFT_EXPIRE_MINUTES,
    )
    top_k = _validate_top_k(top_k)
    saved = await upload_service.save_image_upload(file, subdir="drafts")
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
        upload_service.cleanup_saved_uploads([saved])
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
    saved = await upload_service.save_image_upload(file)
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
        upload_service.cleanup_saved_uploads([saved])
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

    saved_uploads: List[upload_service.SavedUpload] = []
    total_size = 0
    try:
        for file in files:
            saved = await upload_service.save_image_upload(file)
            saved_uploads.append(saved)
            total_size += saved.size_bytes
            if total_size > settings.max_batch_total_size_bytes:
                raise upload_service.payload_too_large(
                    f"批量上传总大小不能超过 {settings.MAX_BATCH_TOTAL_SIZE_MB}MB"
                )
    except Exception:
        upload_service.cleanup_saved_uploads(saved_uploads)
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
        upload_service.cleanup_saved_uploads(saved_uploads[created_count:])
        raise
    finally:
        for saved in saved_uploads:
            saved.image.close()

    return ApiResponse(data=results)
