from datetime import datetime, timedelta

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.case import DiseaseCase, RegionAlert
from ..schemas.alert import RegionAlertSummaryOut
from ..utils.class_names import to_display_name
from ..utils.errors import bad_request, not_found

ALERT_STATUS_UNREAD = "unread"
ALERT_STATUS_READ = "read"
ALERT_STATUS_ALL = "all"
VALID_ALERT_STATUS = {ALERT_STATUS_UNREAD, ALERT_STATUS_READ, ALERT_STATUS_ALL}

DEFAULT_WINDOW_DAYS = 7
DEFAULT_GROWTH_THRESHOLD = 0.5
DEFAULT_MIN_CURRENT_COUNT = 3
DEFAULT_DEDUP_HOURS = 12


def normalize_region_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    return text or None


def build_region_code(
    province: str | None,
    city: str | None,
    district: str | None,
) -> str:
    parts = [normalize_region_text(province), normalize_region_text(city), normalize_region_text(district)]
    values = [item for item in parts if item]
    if not values:
        return "未知区域"
    return "/".join(values)


def calc_growth_rate(current_count: int, previous_count: int) -> float:
    if current_count <= 0:
        return 0.0
    if previous_count <= 0:
        return 1.0
    return round((current_count - previous_count) / previous_count, 4)


def should_trigger_alert(
    *,
    current_count: int,
    previous_count: int,
    growth_threshold: float = DEFAULT_GROWTH_THRESHOLD,
    min_current_count: int = DEFAULT_MIN_CURRENT_COUNT,
) -> tuple[bool, float]:
    growth_rate = calc_growth_rate(current_count, previous_count)
    triggered = current_count >= min_current_count and growth_rate >= growth_threshold
    return triggered, growth_rate


def _normalize_status(status: str | None) -> str:
    normalized = (status or ALERT_STATUS_ALL).strip().lower()
    if normalized not in VALID_ALERT_STATUS:
        raise bad_request("status 必须是 all、unread 或 read")
    return normalized


async def _count_cases(
    db: AsyncSession,
    *,
    region_code: str,
    label: str,
    start_time: datetime,
    end_time: datetime,
) -> int:
    count = await db.scalar(
        select(func.count())
        .select_from(DiseaseCase)
        .where(
            DiseaseCase.region_code == region_code,
            DiseaseCase.confirmed_label == label,
            DiseaseCase.created_at >= start_time,
            DiseaseCase.created_at < end_time,
        )
    )
    return int(count or 0)


async def evaluate_case_region_alert(
    db: AsyncSession,
    *,
    case: DiseaseCase,
    now: datetime | None = None,
    window_days: int = DEFAULT_WINDOW_DAYS,
    growth_threshold: float = DEFAULT_GROWTH_THRESHOLD,
    min_current_count: int = DEFAULT_MIN_CURRENT_COUNT,
    dedup_hours: int = DEFAULT_DEDUP_HOURS,
) -> RegionAlert | None:
    if window_days <= 0:
        raise bad_request("window_days 必须大于 0")
    if dedup_hours < 0:
        raise bad_request("dedup_hours 不能为负数")
    timestamp = now or datetime.now()
    region_code = case.region_code or build_region_code(case.province, case.city, case.district)
    label = case.confirmed_label
    if not label:
        return None

    current_start = timestamp - timedelta(days=window_days)
    previous_start = current_start - timedelta(days=window_days)

    current_count = await _count_cases(
        db,
        region_code=region_code,
        label=label,
        start_time=current_start,
        end_time=timestamp,
    )
    previous_count = await _count_cases(
        db,
        region_code=region_code,
        label=label,
        start_time=previous_start,
        end_time=current_start,
    )

    triggered, growth_rate = should_trigger_alert(
        current_count=current_count,
        previous_count=previous_count,
        growth_threshold=growth_threshold,
        min_current_count=min_current_count,
    )
    if not triggered:
        return None

    if dedup_hours > 0:
        dedup_start = timestamp - timedelta(hours=dedup_hours)
        duplicated = await db.scalar(
            select(func.count())
            .select_from(RegionAlert)
            .where(
                RegionAlert.region_code == region_code,
                RegionAlert.confirmed_label == label,
                RegionAlert.created_at >= dedup_start,
            )
        )
        if int(duplicated or 0) > 0:
            return None

    message = (
        f"区域 {region_code} 的病害 {to_display_name(label)} "
        f"近{window_days}天病例 {current_count} 例，较前期增长 {growth_rate * 100:.1f}%"
    )
    alert = RegionAlert(
        region_code=region_code,
        province=case.province,
        city=case.city,
        district=case.district,
        confirmed_label=label,
        current_count=current_count,
        previous_count=previous_count,
        growth_rate=growth_rate,
        threshold=growth_threshold,
        window_days=window_days,
        status=ALERT_STATUS_UNREAD,
        message=message,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert


async def list_region_alerts(
    db: AsyncSession,
    *,
    status: str | None = ALERT_STATUS_ALL,
    limit: int = 50,
) -> list[RegionAlert]:
    normalized_status = _normalize_status(status)
    bounded_limit = max(1, min(limit, 200))
    query = select(RegionAlert)
    if normalized_status != ALERT_STATUS_ALL:
        query = query.where(RegionAlert.status == normalized_status)
    query = query.order_by(
        RegionAlert.status.asc(),
        desc(RegionAlert.created_at),
        desc(RegionAlert.id),
    ).limit(bounded_limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def mark_region_alert_read(db: AsyncSession, alert_id: int) -> RegionAlert:
    alert = await db.get(RegionAlert, alert_id)
    if alert is None:
        raise not_found("预警记录不存在")
    if alert.status != ALERT_STATUS_READ:
        alert.status = ALERT_STATUS_READ
        await db.commit()
        await db.refresh(alert)
    return alert


async def get_region_alert_summary(db: AsyncSession) -> RegionAlertSummaryOut:
    unread_count = int(
        await db.scalar(
            select(func.count())
            .select_from(RegionAlert)
            .where(RegionAlert.status == ALERT_STATUS_UNREAD)
        )
        or 0
    )
    total_count = int(await db.scalar(select(func.count()).select_from(RegionAlert)) or 0)
    return RegionAlertSummaryOut(unread_count=unread_count, total_count=total_count)
