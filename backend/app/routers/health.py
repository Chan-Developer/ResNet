from fastapi import APIRouter

from ..config import settings
from ..schemas.common import ApiResponse
from ..services.model_service import model_service

router = APIRouter(tags=["health"])


@router.get("/api/health", response_model=ApiResponse)
async def health():
    return ApiResponse(data={
        "status": "ok",
        "device": str(model_service.device),
        "model_path": str(settings.model_path),
        "class_names_source": model_service.class_names_source,
        "dataset_available": settings.dataset_dir.exists(),
        "num_classes": len(model_service.class_names),
    })
