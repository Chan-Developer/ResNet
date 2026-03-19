import asyncio
import json
from datetime import date, timedelta
from typing import Any, Optional
from urllib import error, request

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models.case import DiseaseCase
from ..models.followup import (
    EFFECT_STATUS_IMPROVED,
    EFFECT_STATUS_STABLE,
    EFFECT_STATUS_UNKNOWN,
    EFFECT_STATUS_WORSE,
    PLAN_STATUS_ACTIVE,
    FollowUpCheckin,
    FollowUpPlan,
)
from ..schemas.followup import (
    FollowUpCheckinOut,
    FollowUpEvaluationOut,
    FollowUpEvaluationPoint,
    FollowUpPlanCreateIn,
    FollowUpPlanOut,
    FollowUpPlanUpdateIn,
)
from ..schemas.prediction import PredictionItem
from ..utils.class_names import to_display_name
from ..utils.errors import bad_request, not_found
from ..utils.label_parser import parse_label

VALID_PLAN_STATUS = {PLAN_STATUS_ACTIVE, "paused", "completed", "cancelled"}


def _strip_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    return text or None


def _round4(value: float) -> float:
    return round(float(value), 4)


def _clamp_01(value: float) -> float:
    return _round4(max(0.0, min(1.0, float(value))))


def _label_confidence(predictions: list[PredictionItem], label: str) -> float:
    for item in predictions:
        if item.class_name == label:
            return _round4(item.confidence)
    return 0.0


def _infer_effect_status(
    *,
    target_label: str,
    top1_label: str,
    target_confidence: float,
    target_delta: float,
) -> tuple[str, float]:
    target_profile = parse_label(target_label)
    top1_profile = parse_label(top1_label)

    if target_profile.health_status == "diseased":
        score = _clamp_01(1 - target_confidence)
        if top1_profile.health_status == "healthy" and target_confidence <= 0.2:
            return EFFECT_STATUS_IMPROVED, score
        if target_delta <= -0.08:
            return EFFECT_STATUS_IMPROVED, score
        if target_delta >= 0.08:
            return EFFECT_STATUS_WORSE, score
        return EFFECT_STATUS_STABLE, score

    score = _clamp_01(target_confidence)
    if top1_profile.health_status != "healthy":
        return EFFECT_STATUS_WORSE, score
    if target_delta >= 0.08:
        return EFFECT_STATUS_IMPROVED, score
    if target_delta <= -0.08:
        return EFFECT_STATUS_WORSE, score
    return EFFECT_STATUS_STABLE, score


def _fallback_change_summary(payload: dict[str, Any]) -> str:
    previous = payload["previous_target_confidence"] * 100
    current = payload["target_confidence"] * 100
    delta = payload["target_confidence_delta"] * 100
    sign = "+" if delta >= 0 else ""
    return (
        f"本次复查识别结果为 {payload['top1_display_name']}，目标病情标签为 "
        f"{payload['target_display_name']}。目标置信度由 {previous:.1f}% 变为 "
        f"{current:.1f}%（{sign}{delta:.1f}%），系统评估为「{payload['effect_status_text']}」。"
    )


def _call_openai_change_summary(payload: dict[str, Any]) -> Optional[str]:
    if not settings.OPENAI_API_KEY:
        return None
    prompt = (
        "你是农业复查分析助手。请根据输入输出 JSON："
        "{\"summary\":\"...\"}。summary 需要中文、简洁、包含变化趋势与建议。"
    )
    body = {
        "model": settings.OPENAI_MODEL,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
    }
    req = request.Request(
        f"{settings.OPENAI_BASE_URL.rstrip('/')}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=20) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
        content = raw["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            return None
        summary = parsed.get("summary")
        if not isinstance(summary, str):
            return None
        summary_text = summary.strip()
        return summary_text or None
    except (error.URLError, KeyError, ValueError, json.JSONDecodeError):
        return None


async def _generate_change_summary(payload: dict[str, Any]) -> str:
    summary = await asyncio.to_thread(_call_openai_change_summary, payload)
    if summary:
        return summary
    return _fallback_change_summary(payload)


async def _get_owned_case(
    db: AsyncSession,
    *,
    user_id: int,
    case_id: int,
) -> DiseaseCase:
    result = await db.execute(
        select(DiseaseCase).where(DiseaseCase.id == case_id, DiseaseCase.user_id == user_id)
    )
    case = result.scalar_one_or_none()
    if case is None:
        raise not_found("关联病例不存在")
    return case


async def _get_latest_user_case(db: AsyncSession, *, user_id: int) -> DiseaseCase | None:
    result = await db.execute(
        select(DiseaseCase)
        .where(DiseaseCase.user_id == user_id)
        .order_by(DiseaseCase.created_at.desc(), DiseaseCase.id.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _get_owned_plan(db: AsyncSession, *, user_id: int, plan_id: int) -> FollowUpPlan:
    result = await db.execute(
        select(FollowUpPlan).where(FollowUpPlan.id == plan_id, FollowUpPlan.user_id == user_id)
    )
    plan = result.scalar_one_or_none()
    if plan is None:
        raise not_found("复查计划不存在")
    return plan


def _checkin_to_schema(row: FollowUpCheckin) -> FollowUpCheckinOut:
    raw_predictions = row.results_json if isinstance(row.results_json, list) else []
    predictions: list[PredictionItem] = []
    for item in raw_predictions:
        try:
            predictions.append(PredictionItem.model_validate(item))
        except Exception:
            continue
    return FollowUpCheckinOut(
        id=row.id,
        plan_id=row.plan_id,
        image_filename=row.image_filename,
        image_url=row.image_url,
        top1_label=row.top1_label,
        top1_display_name=to_display_name(row.top1_label),
        top1_confidence=row.top1_confidence,
        target_confidence=row.target_confidence,
        target_confidence_delta=row.target_confidence_delta,
        top1_confidence_delta=row.top1_confidence_delta,
        effect_status=row.effect_status,
        effect_score=row.effect_score,
        llm_summary=row.llm_summary,
        note=row.note,
        predictions=predictions,
        created_at=row.created_at,
    )


def _plan_to_schema(
    plan: FollowUpPlan,
    *,
    checkin_count: int = 0,
    last_checkin_at=None,
) -> FollowUpPlanOut:
    return FollowUpPlanOut(
        id=plan.id,
        user_id=plan.user_id,
        case_id=plan.case_id,
        title=plan.title,
        target_label=plan.target_label,
        target_display_name=to_display_name(plan.target_label),
        notes=plan.notes or "",
        frequency_days=plan.frequency_days,
        start_date=plan.start_date,
        next_review_date=plan.next_review_date,
        status=plan.status,
        latest_effect=plan.latest_effect,
        effect_score=plan.effect_score,
        checkin_count=int(checkin_count),
        last_checkin_at=last_checkin_at,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


async def create_followup_plan(
    db: AsyncSession,
    *,
    user_id: int,
    payload: FollowUpPlanCreateIn,
) -> FollowUpPlanOut:
    case_id = payload.case_id
    target_label = _strip_text(payload.target_label)
    case: DiseaseCase | None = None
    if case_id is not None:
        case = await _get_owned_case(db, user_id=user_id, case_id=case_id)
        if target_label is None:
            target_label = case.confirmed_label
    if case is None and target_label is None:
        latest_case = await _get_latest_user_case(db, user_id=user_id)
        if latest_case is not None:
            case = latest_case
            case_id = latest_case.id
            target_label = latest_case.confirmed_label

    if target_label is None:
        raise bad_request("请先完成一次确认建档，或手动填写目标标签")

    start_date = payload.start_date or date.today()
    frequency_days = int(payload.frequency_days)
    next_review_date = start_date + timedelta(days=frequency_days)
    plan = FollowUpPlan(
        user_id=user_id,
        case_id=case.id if case else case_id,
        title=_strip_text(payload.title) or f"{to_display_name(target_label)} 复查计划",
        target_label=target_label,
        notes=_strip_text(payload.notes) or "",
        frequency_days=frequency_days,
        start_date=start_date,
        next_review_date=next_review_date,
        status=PLAN_STATUS_ACTIVE,
        latest_effect=EFFECT_STATUS_UNKNOWN,
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return _plan_to_schema(plan)


async def list_followup_plans(
    db: AsyncSession,
    *,
    user_id: int,
    status: str | None = None,
) -> list[FollowUpPlanOut]:
    normalized_status = _strip_text(status)
    query = select(FollowUpPlan).where(FollowUpPlan.user_id == user_id)
    if normalized_status:
        if normalized_status not in VALID_PLAN_STATUS:
            raise bad_request("status 必须是 active/paused/completed/cancelled")
        query = query.where(FollowUpPlan.status == normalized_status)
    query = query.order_by(
        FollowUpPlan.status.asc(),
        FollowUpPlan.next_review_date.asc(),
        FollowUpPlan.updated_at.desc(),
    )
    plans = list((await db.execute(query)).scalars().all())
    if not plans:
        return []

    plan_ids = [plan.id for plan in plans]
    stats_rows = await db.execute(
        select(
            FollowUpCheckin.plan_id,
            func.count(FollowUpCheckin.id).label("checkin_count"),
            func.max(FollowUpCheckin.created_at).label("last_checkin_at"),
        )
        .where(FollowUpCheckin.plan_id.in_(plan_ids))
        .group_by(FollowUpCheckin.plan_id)
    )
    stats_map = {
        int(row.plan_id): (
            int(row.checkin_count or 0),
            row.last_checkin_at,
        )
        for row in stats_rows
    }
    return [
        _plan_to_schema(
            plan,
            checkin_count=stats_map.get(plan.id, (0, None))[0],
            last_checkin_at=stats_map.get(plan.id, (0, None))[1],
        )
        for plan in plans
    ]


async def get_followup_plan(
    db: AsyncSession,
    *,
    user_id: int,
    plan_id: int,
) -> FollowUpPlanOut:
    plan = await _get_owned_plan(db, user_id=user_id, plan_id=plan_id)
    rows = await db.execute(
        select(
            func.count(FollowUpCheckin.id).label("checkin_count"),
            func.max(FollowUpCheckin.created_at).label("last_checkin_at"),
        ).where(FollowUpCheckin.plan_id == plan.id)
    )
    stat = rows.first()
    return _plan_to_schema(
        plan,
        checkin_count=int(stat.checkin_count or 0) if stat else 0,
        last_checkin_at=stat.last_checkin_at if stat else None,
    )


async def update_followup_plan(
    db: AsyncSession,
    *,
    user_id: int,
    plan_id: int,
    payload: FollowUpPlanUpdateIn,
) -> FollowUpPlanOut:
    plan = await _get_owned_plan(db, user_id=user_id, plan_id=plan_id)
    if payload.status is None and payload.frequency_days is None and payload.notes is None:
        raise bad_request("至少更新一个字段")

    if payload.status is not None:
        if payload.status not in VALID_PLAN_STATUS:
            raise bad_request("不支持该计划状态")
        plan.status = payload.status
    if payload.frequency_days is not None:
        plan.frequency_days = int(payload.frequency_days)
        if plan.status == PLAN_STATUS_ACTIVE:
            plan.next_review_date = date.today() + timedelta(days=plan.frequency_days)
    if payload.notes is not None:
        plan.notes = _strip_text(payload.notes) or ""

    await db.commit()
    await db.refresh(plan)
    return await get_followup_plan(db, user_id=user_id, plan_id=plan.id)


async def list_followup_checkins(
    db: AsyncSession,
    *,
    user_id: int,
    plan_id: int,
    limit: int = 30,
) -> list[FollowUpCheckinOut]:
    plan = await _get_owned_plan(db, user_id=user_id, plan_id=plan_id)
    bounded_limit = max(1, min(limit, 100))
    result = await db.execute(
        select(FollowUpCheckin)
        .where(FollowUpCheckin.plan_id == plan.id)
        .order_by(FollowUpCheckin.created_at.desc(), FollowUpCheckin.id.desc())
        .limit(bounded_limit)
    )
    rows = list(result.scalars().all())
    return [_checkin_to_schema(item) for item in rows]


async def create_followup_checkin_from_prediction(
    db: AsyncSession,
    *,
    user_id: int,
    plan_id: int,
    image_filename: str,
    image_url: str,
    predictions: list[PredictionItem],
    note: str | None = None,
) -> FollowUpCheckinOut:
    if not predictions:
        raise bad_request("复查识别结果不能为空")
    plan = await _get_owned_plan(db, user_id=user_id, plan_id=plan_id)
    if plan.status != PLAN_STATUS_ACTIVE:
        raise bad_request("仅 active 状态计划可上传复查")

    top1 = predictions[0]
    target_confidence = _label_confidence(predictions, plan.target_label)

    previous_result = await db.execute(
        select(FollowUpCheckin)
        .where(FollowUpCheckin.plan_id == plan.id)
        .order_by(FollowUpCheckin.created_at.desc(), FollowUpCheckin.id.desc())
        .limit(1)
    )
    previous = previous_result.scalar_one_or_none()

    baseline_target_conf = target_confidence
    baseline_top1_conf: float | None = None
    if previous is not None:
        baseline_target_conf = previous.target_confidence
        baseline_top1_conf = previous.top1_confidence
    elif plan.case_id is not None:
        case = await db.get(DiseaseCase, plan.case_id)
        if case is not None and case.user_id == plan.user_id and case.confirmed_label == plan.target_label:
            baseline_target_conf = case.confidence

    target_delta = _round4(target_confidence - baseline_target_conf)
    top1_delta = _round4(top1.confidence - baseline_top1_conf) if baseline_top1_conf is not None else 0.0
    effect_status, effect_score = _infer_effect_status(
        target_label=plan.target_label,
        top1_label=top1.class_name,
        target_confidence=target_confidence,
        target_delta=target_delta,
    )

    effect_status_text = (
        "改善"
        if effect_status == EFFECT_STATUS_IMPROVED
        else "加重"
        if effect_status == EFFECT_STATUS_WORSE
        else "稳定"
    )
    llm_payload = {
        "plan_title": plan.title,
        "target_label": plan.target_label,
        "target_display_name": to_display_name(plan.target_label),
        "top1_label": top1.class_name,
        "top1_display_name": to_display_name(top1.class_name),
        "target_confidence": target_confidence,
        "previous_target_confidence": baseline_target_conf,
        "target_confidence_delta": target_delta,
        "top1_confidence": _round4(top1.confidence),
        "top1_confidence_delta": top1_delta,
        "effect_status": effect_status,
        "effect_status_text": effect_status_text,
        "note": _strip_text(note) or "",
    }
    llm_summary = await _generate_change_summary(llm_payload)

    row = FollowUpCheckin(
        plan_id=plan.id,
        user_id=plan.user_id,
        image_filename=image_filename,
        image_url=image_url,
        top1_label=top1.class_name,
        top1_confidence=_round4(top1.confidence),
        target_confidence=target_confidence,
        target_confidence_delta=target_delta,
        top1_confidence_delta=top1_delta,
        effect_status=effect_status,
        effect_score=effect_score,
        llm_summary=llm_summary,
        note=_strip_text(note) or "",
        results_json=[item.model_dump() for item in predictions],
    )
    db.add(row)

    plan.latest_effect = effect_status
    plan.effect_score = effect_score
    plan.next_review_date = date.today() + timedelta(days=plan.frequency_days)

    await db.commit()
    await db.refresh(row)
    return _checkin_to_schema(row)


async def get_followup_evaluation(
    db: AsyncSession,
    *,
    user_id: int,
    plan_id: int,
) -> FollowUpEvaluationOut:
    plan = await _get_owned_plan(db, user_id=user_id, plan_id=plan_id)
    result = await db.execute(
        select(FollowUpCheckin)
        .where(FollowUpCheckin.plan_id == plan.id)
        .order_by(FollowUpCheckin.created_at.asc(), FollowUpCheckin.id.asc())
    )
    rows = list(result.scalars().all())

    improved_count = sum(1 for row in rows if row.effect_status == EFFECT_STATUS_IMPROVED)
    stable_count = sum(1 for row in rows if row.effect_status == EFFECT_STATUS_STABLE)
    worse_count = sum(1 for row in rows if row.effect_status == EFFECT_STATUS_WORSE)

    if rows:
        avg_delta = _round4(
            sum(float(row.target_confidence_delta) for row in rows) / len(rows)
        )
    else:
        avg_delta = None

    trend = [
        FollowUpEvaluationPoint(
            date=(row.created_at.date().isoformat() if row.created_at else ""),
            target_confidence=row.target_confidence,
            effect_status=row.effect_status,
            top1_label=row.top1_label,
            top1_display_name=to_display_name(row.top1_label),
        )
        for row in rows
    ]
    return FollowUpEvaluationOut(
        total_checkins=len(rows),
        improved_count=improved_count,
        stable_count=stable_count,
        worse_count=worse_count,
        latest_effect=plan.latest_effect or EFFECT_STATUS_UNKNOWN,
        effect_score=plan.effect_score,
        avg_target_confidence_delta=avg_delta,
        trend=trend,
    )
