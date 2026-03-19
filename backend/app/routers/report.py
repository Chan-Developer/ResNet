import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_user, get_db
from ..schemas.common import ApiResponse
from ..schemas.report import DashboardFilterOptionsOut, DashboardOverviewOut
from ..services import rbac_service, report_service
from ..utils.errors import forbidden

router = APIRouter(prefix="/api/report", tags=["report"])


def _scope_user_id(user, scope: str) -> int | None:
    normalized_scope = report_service._normalize_scope(scope)
    if normalized_scope == report_service.SCOPE_ALL:
        if rbac_service.normalize_role_code(user.role) != "admin":
            raise forbidden("仅管理员可查看全局看板")
        return None
    return user.id


@router.get("/overview", response_model=ApiResponse[DashboardOverviewOut])
async def get_overview(
    days: int = 30,
    scope: str = report_service.SCOPE_ME,
    crop_name: str | None = None,
    label: str | None = None,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    overview = await report_service.get_dashboard_overview(
        db,
        user_id=_scope_user_id(user, scope),
        days=days,
        scope=scope,
        crop_name=crop_name,
        label=label,
    )
    return ApiResponse(data=overview)


@router.get("/filters", response_model=ApiResponse[DashboardFilterOptionsOut])
async def get_filters(
    scope: str = report_service.SCOPE_ME,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    options = await report_service.get_dashboard_filter_options(
        db,
        user_id=_scope_user_id(user, scope),
    )
    return ApiResponse(data=options)


@router.get("/export.csv")
async def export_report_csv(
    days: int = 30,
    scope: str = report_service.SCOPE_ME,
    crop_name: str | None = None,
    label: str | None = None,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    overview = await report_service.get_dashboard_overview(
        db,
        user_id=_scope_user_id(user, scope),
        days=days,
        scope=scope,
        crop_name=crop_name,
        label=label,
    )
    stream = io.StringIO()
    writer = csv.writer(stream)
    for row in report_service.to_report_rows(overview):
        writer.writerow(row)

    content = "\ufeff" + stream.getvalue()
    stream.close()
    filename = f"diagnosis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([content]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export.xlsx")
async def export_report_xlsx(
    days: int = 30,
    scope: str = report_service.SCOPE_ME,
    crop_name: str | None = None,
    label: str | None = None,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    overview = await report_service.get_dashboard_overview(
        db,
        user_id=_scope_user_id(user, scope),
        days=days,
        scope=scope,
        crop_name=crop_name,
        label=label,
    )
    rows = report_service.to_report_rows(overview)
    xlsx_bytes = report_service.build_xlsx_bytes(rows)
    filename = f"diagnosis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return StreamingResponse(
        iter([xlsx_bytes]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
