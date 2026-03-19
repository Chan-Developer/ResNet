from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import require_permissions
from ..schemas.common import ApiResponse, PageData
from ..schemas.dataset import CategoryImageOut, CategoryOut
from ..services import dataset_service
from ..utils.errors import bad_request

router = APIRouter(prefix="/api/dataset", tags=["dataset"])
MAX_PAGE_SIZE = 100


@router.get("/categories", response_model=ApiResponse[list[CategoryOut]])
async def list_categories(
    _=Depends(require_permissions("dataset:view")),
):
    categories = dataset_service.get_categories()
    return ApiResponse(data=categories)


@router.get("/categories/{name}/images", response_model=ApiResponse[PageData[CategoryImageOut]])
async def list_category_images(
    name: str,
    page: int = 1,
    size: int = 20,
    _=Depends(require_permissions("dataset:view")),
):
    if page < 1:
        raise bad_request("page 必须大于等于 1")
    if size < 1 or size > MAX_PAGE_SIZE:
        raise bad_request(f"size 必须在 1~{MAX_PAGE_SIZE} 范围内")
    result = dataset_service.get_category_images(name, page, size)
    if result is None:
        raise HTTPException(status_code=404, detail="类别不存在")
    return ApiResponse(data=result)
