from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..dependencies import get_db, get_model_service, require_permissions
from ..schemas.common import ApiResponse
from ..schemas.followup import (
    FollowUpCheckinOut,
    FollowUpEvaluationOut,
    FollowUpPlanCreateIn,
    FollowUpPlanOut,
    FollowUpPlanUpdateIn,
)
from ..services import followup_service, upload_service
from ..services.model_service import ModelService
from ..utils.errors import bad_request

router = APIRouter(prefix="/api/followup", tags=["followup"])


def _validate_top_k(top_k: int) -> int:
    if top_k < 1 or top_k > settings.MAX_TOP_K:
        raise bad_request(f"top_k 必须在 1~{settings.MAX_TOP_K} 范围内")
    return top_k


@router.get("/plans", response_model=ApiResponse[list[FollowUpPlanOut]])
async def list_plans(
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permissions("followup:manage")),
):
    plans = await followup_service.list_followup_plans(db, user_id=user.id, status=status)
    return ApiResponse(data=plans)


@router.post("/plans", response_model=ApiResponse[FollowUpPlanOut])
async def create_plan(
    payload: FollowUpPlanCreateIn,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permissions("followup:manage")),
):
    plan = await followup_service.create_followup_plan(
        db,
        user_id=user.id,
        payload=payload,
    )
    return ApiResponse(data=plan)


@router.get("/plans/{plan_id}", response_model=ApiResponse[FollowUpPlanOut])
async def get_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permissions("followup:manage")),
):
    plan = await followup_service.get_followup_plan(db, user_id=user.id, plan_id=plan_id)
    return ApiResponse(data=plan)


@router.patch("/plans/{plan_id}", response_model=ApiResponse[FollowUpPlanOut])
async def update_plan(
    plan_id: int,
    payload: FollowUpPlanUpdateIn,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permissions("followup:manage")),
):
    plan = await followup_service.update_followup_plan(
        db,
        user_id=user.id,
        plan_id=plan_id,
        payload=payload,
    )
    return ApiResponse(data=plan)


@router.get("/plans/{plan_id}/checkins", response_model=ApiResponse[list[FollowUpCheckinOut]])
async def list_checkins(
    plan_id: int,
    limit: int = 30,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permissions("followup:manage")),
):
    rows = await followup_service.list_followup_checkins(
        db,
        user_id=user.id,
        plan_id=plan_id,
        limit=limit,
    )
    return ApiResponse(data=rows)


@router.post("/plans/{plan_id}/checkins", response_model=ApiResponse[FollowUpCheckinOut])
async def create_checkin(
    plan_id: int,
    file: UploadFile = File(...),
    top_k: int = Form(settings.TOP_K),
    note: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permissions("followup:manage")),
    svc: ModelService = Depends(get_model_service),
):
    top_k = _validate_top_k(top_k)
    saved = await upload_service.save_image_upload(file, subdir="followups")
    try:
        result = svc.predict(saved.image, top_k)
        checkin = await followup_service.create_followup_checkin_from_prediction(
            db,
            user_id=user.id,
            plan_id=plan_id,
            image_filename=saved.filename,
            image_url=saved.url,
            predictions=result.predictions,
            note=note,
        )
    except Exception:
        upload_service.cleanup_file(saved.filepath)
        raise
    finally:
        saved.image.close()
    return ApiResponse(data=checkin)


@router.get("/plans/{plan_id}/evaluation", response_model=ApiResponse[FollowUpEvaluationOut])
async def get_evaluation(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permissions("followup:manage")),
):
    data = await followup_service.get_followup_evaluation(db, user_id=user.id, plan_id=plan_id)
    return ApiResponse(data=data)
