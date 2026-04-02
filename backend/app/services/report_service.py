from datetime import date, datetime, time, timedelta
from typing import Any
from xml.sax.saxutils import escape
import zipfile
import io

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.case import DiseaseCase, RegionAlert
from ..models.prediction import PredictionRecord
from ..schemas.report import (
    DashboardFilterOptionsOut,
    DashboardOverviewOut,
    DashboardSummary,
    DiseaseDistributionItem,
    RegionDistributionItem,
    TrendPoint,
)
from ..utils.class_names import to_display_name
from ..utils.errors import bad_request

SCOPE_ME = "me"
SCOPE_ALL = "all"


def _date_text(value: Any) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if value is None:
        return ""
    return str(value)


def _safe_ratio(part: int, whole: int) -> float:
    if whole <= 0:
        return 0.0
    return round(part / whole, 4)


def _safe_accuracy(correct_count: int, confirmed_count: int) -> float | None:
    if confirmed_count <= 0:
        return None
    return round(correct_count / confirmed_count, 4)


def _validate_days(days: int) -> int:
    if days < 7 or days > 365:
        raise bad_request("days 必须在 7~365 范围内")
    return days


def _normalize_scope(scope: str) -> str:
    normalized = (scope or "").strip().lower()
    if normalized not in {SCOPE_ME, SCOPE_ALL}:
        raise bad_request("scope 必须是 me 或 all")
    return normalized


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    return text or None


def _point_row(item: TrendPoint) -> list[str | int]:
    return [
        item.date,
        item.prediction_count,
        item.confirmed_count,
        "" if item.accuracy is None else f"{item.accuracy * 100:.2f}%",
    ]


def to_report_rows(overview: DashboardOverviewOut) -> list[list[str | int]]:
    rows: list[list[str | int]] = [
        ["植物病害诊断统计报表"],
        ["生成时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        ["统计范围", "全局" if overview.summary.scope == SCOPE_ALL else "个人"],
        ["统计周期(天)", overview.summary.period_days],
        ["开始日期", overview.summary.start_date],
        ["结束日期", overview.summary.end_date],
        ["作物筛选", overview.summary.crop_name or "全部"],
        ["病害筛选", overview.summary.label or "全部"],
        ["地区筛选", overview.summary.region_code or "全部"],
        ["识别总数", overview.summary.prediction_count],
        ["确认建档数", overview.summary.confirmed_count],
        [
            "诊断准确率",
            "" if overview.summary.accuracy is None else f"{overview.summary.accuracy * 100:.2f}%",
        ],
        [
            "平均置信度",
            "" if overview.summary.avg_confidence is None else f"{overview.summary.avg_confidence * 100:.2f}%",
        ],
        [],
        ["病害分布"],
        ["标签", "展示名称", "数量", "占比"],
    ]
    for item in overview.distribution:
        rows.append([item.label, item.display_name, item.count, f"{item.ratio * 100:.2f}%"])
    rows.append([])
    if overview.region_distribution:
        rows.append(["区域预警分布"])
        rows.append(["区域", "病例数量", "占比", "有无预警", "有无未读预警"])
        for region in overview.region_distribution:
            rows.append(
                [
                    region.region_code,
                    region.total_count,
                    f"{region.ratio * 100:.2f}%",
                    "有" if region.has_alert else "无",
                    "有" if region.has_unread_alert else "无",
                ]
            )
        rows.append([])
    rows.append(["趋势变化"])
    rows.append(["日期", "识别量", "建档量", "准确率"])
    rows.extend([_point_row(item) for item in overview.trend])
    return rows


def _col_name(index: int) -> str:
    value = index
    parts: list[str] = []
    while value > 0:
        value, mod = divmod(value - 1, 26)
        parts.append(chr(ord("A") + mod))
    return "".join(reversed(parts))


def _xlsx_cell(value: str | int | float, row_index: int, col_index: int) -> str:
    cell_ref = f"{_col_name(col_index)}{row_index}"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f'<c r="{cell_ref}"><v>{value}</v></c>'
    text = escape(str(value))
    return f'<c r="{cell_ref}" t="inlineStr"><is><t>{text}</t></is></c>'


def build_xlsx_bytes(rows: list[list[str | int | float]]) -> bytes:
    sheet_rows: list[str] = []
    for row_index, row in enumerate(rows, start=1):
        cells = "".join(_xlsx_cell(value, row_index, idx + 1) for idx, value in enumerate(row))
        sheet_rows.append(f'<row r="{row_index}">{cells}</row>')
    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        "<sheetData>"
        f'{"".join(sheet_rows)}'
        "</sheetData>"
        "</worksheet>"
    )

    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="report" sheetId="1" r:id="rId1"/></sheets>'
        "</workbook>"
    )
    workbook_rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        'Target="worksheets/sheet1.xml"/>'
        "</Relationships>"
    )
    rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/>'
        "</Relationships>"
    )
    content_types_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        "</Types>"
    )

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types_xml)
        zf.writestr("_rels/.rels", rels_xml)
        zf.writestr("xl/workbook.xml", workbook_xml)
        zf.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)
        zf.writestr("xl/worksheets/sheet1.xml", sheet_xml)
    return buffer.getvalue()


async def get_dashboard_filter_options(
    db: AsyncSession,
    *,
    user_id: int | None = None,
) -> DashboardFilterOptionsOut:
    case_filters = []
    if user_id is not None:
        case_filters.append(DiseaseCase.user_id == user_id)

    crop_query = select(DiseaseCase.crop_name).where(*case_filters).group_by(DiseaseCase.crop_name)
    label_query = select(DiseaseCase.confirmed_label).where(*case_filters).group_by(DiseaseCase.confirmed_label)
    region_query = select(DiseaseCase.region_code).where(*case_filters).group_by(DiseaseCase.region_code)
    crops_result = await db.execute(crop_query)
    labels_result = await db.execute(label_query)
    regions_result = await db.execute(region_query)

    crops = sorted(
        [str(item[0]) for item in crops_result.all() if item[0] is not None and str(item[0]).strip()]
    )
    labels = sorted(
        [str(item[0]) for item in labels_result.all() if item[0] is not None and str(item[0]).strip()]
    )
    regions = sorted(
        [str(item[0]) for item in regions_result.all() if item[0] is not None and str(item[0]).strip()]
    )
    return DashboardFilterOptionsOut(
        crops=crops,
        labels=[{"label": label, "display_name": to_display_name(label)} for label in labels],
        regions=regions,
    )


async def get_dashboard_overview(
    db: AsyncSession,
    *,
    user_id: int | None,
    days: int = 30,
    crop_name: str | None = None,
    label: str | None = None,
    region_code: str | None = None,
    scope: str = SCOPE_ME,
) -> DashboardOverviewOut:
    days = _validate_days(days)
    scope = _normalize_scope(scope)
    crop_name = _normalize_optional_text(crop_name)
    label = _normalize_optional_text(label)
    region_code = _normalize_optional_text(region_code)

    end_day = date.today()
    start_day = end_day - timedelta(days=days - 1)
    range_start = datetime.combine(start_day, time.min)
    range_end = datetime.combine(end_day + timedelta(days=1), time.min)

    prediction_filters = [
        PredictionRecord.created_at >= range_start,
        PredictionRecord.created_at < range_end,
    ]
    case_filters = [
        DiseaseCase.created_at >= range_start,
        DiseaseCase.created_at < range_end,
    ]

    if user_id is not None:
        prediction_filters.append(PredictionRecord.user_id == user_id)
        case_filters.append(DiseaseCase.user_id == user_id)
    if label:
        prediction_filters.append(PredictionRecord.top1_class == label)
        case_filters.append(DiseaseCase.confirmed_label == label)
    if crop_name:
        case_filters.append(DiseaseCase.crop_name == crop_name)
    if region_code:
        case_filters.append(DiseaseCase.region_code == region_code)

    if region_code:
        prediction_query = (
            select(func.count(func.distinct(PredictionRecord.id)))
            .select_from(PredictionRecord)
            .join(DiseaseCase, DiseaseCase.prediction_record_id == PredictionRecord.id)
            .where(*case_filters)
        )
        if label:
            prediction_query = prediction_query.where(PredictionRecord.top1_class == label)
        prediction_count = int(await db.scalar(prediction_query) or 0)

        avg_confidence_query = (
            select(func.avg(PredictionRecord.top1_confidence))
            .select_from(PredictionRecord)
            .join(DiseaseCase, DiseaseCase.prediction_record_id == PredictionRecord.id)
            .where(*case_filters)
        )
        if label:
            avg_confidence_query = avg_confidence_query.where(PredictionRecord.top1_class == label)
        avg_confidence_raw = await db.scalar(avg_confidence_query)
    else:
        prediction_count = int(
            await db.scalar(
                select(func.count()).select_from(PredictionRecord).where(*prediction_filters)
            )
            or 0
        )
        avg_confidence_raw = await db.scalar(
            select(func.avg(PredictionRecord.top1_confidence)).where(*prediction_filters)
        )
    avg_confidence = round(float(avg_confidence_raw), 4) if avg_confidence_raw is not None else None

    confirmed_count = int(
        await db.scalar(
            select(func.count()).select_from(DiseaseCase).where(*case_filters)
        )
        or 0
    )
    correct_count = int(
        await db.scalar(
            select(func.count())
            .select_from(DiseaseCase)
            .where(*case_filters, DiseaseCase.predicted_label == DiseaseCase.confirmed_label)
        )
        or 0
    )
    accuracy = _safe_accuracy(correct_count, confirmed_count)

    distribution_rows = await db.execute(
        select(DiseaseCase.confirmed_label, func.count().label("count"))
        .where(*case_filters)
        .group_by(DiseaseCase.confirmed_label)
        .order_by(desc("count"))
        .limit(12)
    )
    distribution = [
        DiseaseDistributionItem(
            label=confirmed_label,
            display_name=to_display_name(confirmed_label),
            count=int(count),
            ratio=_safe_ratio(int(count), confirmed_count),
        )
        for confirmed_label, count in distribution_rows.all()
    ]

    if region_code:
        prediction_rows_query = (
            select(func.date(DiseaseCase.created_at).label("d"), func.count().label("count"))
            .select_from(PredictionRecord)
            .join(DiseaseCase, DiseaseCase.prediction_record_id == PredictionRecord.id)
            .where(*case_filters)
            .group_by("d")
            .order_by("d")
        )
        if label:
            prediction_rows_query = prediction_rows_query.where(PredictionRecord.top1_class == label)
        prediction_rows = await db.execute(prediction_rows_query)
    else:
        prediction_rows = await db.execute(
            select(func.date(PredictionRecord.created_at).label("d"), func.count().label("count"))
            .where(*prediction_filters)
            .group_by("d")
            .order_by("d")
        )
    predictions_by_day = {_date_text(row[0]): int(row[1]) for row in prediction_rows.all()}

    confirmed_rows = await db.execute(
        select(func.date(DiseaseCase.created_at).label("d"), func.count().label("count"))
        .where(*case_filters)
        .group_by("d")
        .order_by("d")
    )
    confirmed_by_day = {_date_text(row[0]): int(row[1]) for row in confirmed_rows.all()}

    correct_rows = await db.execute(
        select(func.date(DiseaseCase.created_at).label("d"), func.count().label("count"))
        .where(*case_filters, DiseaseCase.predicted_label == DiseaseCase.confirmed_label)
        .group_by("d")
        .order_by("d")
    )
    correct_by_day = {_date_text(row[0]): int(row[1]) for row in correct_rows.all()}

    trend: list[TrendPoint] = []
    for index in range(days):
        current_day = start_day + timedelta(days=index)
        day_text = current_day.isoformat()
        day_predictions = predictions_by_day.get(day_text, 0)
        day_confirmed = confirmed_by_day.get(day_text, 0)
        day_correct = correct_by_day.get(day_text, 0)
        trend.append(
            TrendPoint(
                date=day_text,
                prediction_count=day_predictions,
                confirmed_count=day_confirmed,
                accuracy=_safe_accuracy(day_correct, day_confirmed),
            )
        )

    region_distribution: list[RegionDistributionItem] = []
    region_rows = await db.execute(
        select(DiseaseCase.region_code, func.count().label("count"))
        .where(*case_filters)
        .group_by(DiseaseCase.region_code)
        .order_by(desc("count"))
        .limit(8)
    )
    top_regions = [(row[0], int(row[1])) for row in region_rows.all()]

    for region_code, region_count in top_regions:
        alert_total = int(
            await db.scalar(
                select(func.count()).select_from(RegionAlert).where(RegionAlert.region_code == region_code)
            )
            or 0
        )
        alert_unread = int(
            await db.scalar(
                select(func.count())
                .select_from(RegionAlert)
                .where(RegionAlert.region_code == region_code, RegionAlert.status == "unread")
            )
            or 0
        )

        region_distribution.append(
            RegionDistributionItem(
                region_code=region_code,
                total_count=region_count,
                ratio=_safe_ratio(region_count, confirmed_count),
                has_alert=alert_total > 0,
                has_unread_alert=alert_unread > 0,
            )
        )

    return DashboardOverviewOut(
        summary=DashboardSummary(
            scope=scope,
            period_days=days,
            start_date=start_day.isoformat(),
            end_date=end_day.isoformat(),
            crop_name=crop_name,
            label=label,
            region_code=region_code,
            prediction_count=prediction_count,
            confirmed_count=confirmed_count,
            avg_confidence=avg_confidence,
            accuracy=accuracy,
        ),
        distribution=distribution,
        trend=trend,
        region_distribution=region_distribution,
    )
