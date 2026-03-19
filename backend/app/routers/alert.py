from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db, require_permissions
from ..schemas.alert import RegionAlertOut, RegionAlertSummaryOut
from ..schemas.common import ApiResponse
from ..services import alert_service
from ..utils.class_names import to_display_name

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


def _to_alert_schema(item) -> RegionAlertOut:
    return RegionAlertOut(
        id=item.id,
        region_code=item.region_code,
        province=item.province,
        city=item.city,
        district=item.district,
        confirmed_label=item.confirmed_label,
        display_name=to_display_name(item.confirmed_label),
        current_count=item.current_count,
        previous_count=item.previous_count,
        growth_rate=item.growth_rate,
        threshold=item.threshold,
        window_days=item.window_days,
        status=item.status,
        message=item.message,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.get("/region", response_model=ApiResponse[list[RegionAlertOut]])
async def list_region_alerts(
    status: str = alert_service.ALERT_STATUS_ALL,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permissions("admin:alert")),
):
    alerts = await alert_service.list_region_alerts(db, status=status, limit=limit)
    return ApiResponse(data=[_to_alert_schema(item) for item in alerts])


@router.patch("/region/{alert_id}/read", response_model=ApiResponse[RegionAlertOut])
async def mark_region_alert_read(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permissions("admin:alert")),
):
    alert = await alert_service.mark_region_alert_read(db, alert_id)
    return ApiResponse(data=_to_alert_schema(alert))


@router.get("/region/summary", response_model=ApiResponse[RegionAlertSummaryOut])
async def region_alert_summary(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permissions("admin:alert")),
):
    summary = await alert_service.get_region_alert_summary(db)
    return ApiResponse(data=summary)
