from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_user, get_db
from ..schemas.common import ApiResponse, PageData
from ..schemas.prediction import HistoryOut
from ..services import history_service
from ..utils.errors import bad_request

router = APIRouter(prefix="/api/history", tags=["history"])
MAX_PAGE_SIZE = 100


@router.get("", response_model=ApiResponse[PageData[HistoryOut]])
async def list_history(
    page: int = 1,
    size: int = 20,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    if page < 1:
        raise bad_request("page 必须大于等于 1")
    if size < 1 or size > MAX_PAGE_SIZE:
        raise bad_request(f"size 必须在 1~{MAX_PAGE_SIZE} 范围内")
    data = await history_service.get_history(db, user.id, page, size)
    return ApiResponse(data=data)


@router.delete("/{record_id}", response_model=ApiResponse)
async def delete_history(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    ok = await history_service.delete_record(db, record_id, user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="记录不存在")
    return ApiResponse(message="删除成功")
