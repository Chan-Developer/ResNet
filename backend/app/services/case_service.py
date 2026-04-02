from pathlib import Path
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models.case import DiseaseCase
from ..models.prediction import PredictionRecord
from ..schemas.diagnosis import (
    CaseOut,
    EvidenceItem,
    SimilarCaseOut,
)
from ..schemas.prediction import PredictionItem
from ..services import advice_service, alert_service, knowledge_service
from ..utils.class_names import to_display_name
from ..utils.errors import bad_request, not_found, unauthorized
from ..utils.label_parser import parse_label
from ..utils.security import create_signed_token, decode_token


def create_draft_token(
    *,
    user_id: int,
    image_filename: str,
    image_url: str,
    top_k: int,
    predictions: list[PredictionItem],
) -> str:
    return create_signed_token(
        {
            "type": "diagnosis_draft",
            "user_id": user_id,
            "image_filename": image_filename,
            "image_url": image_url,
            "top_k": top_k,
            "predictions": [item.model_dump() for item in predictions],
        },
        settings.DIAGNOSIS_DRAFT_EXPIRE_MINUTES,
    )


def decode_draft_token(token: str, user_id: int) -> dict:
    payload = decode_token(token)
    if payload is None or payload.get("type") != "diagnosis_draft":
        raise unauthorized("诊断草稿已失效，请重新上传图片")
    if payload.get("user_id") != user_id:
        raise unauthorized("无权访问该诊断草稿")
    return payload


def _prediction_from_payload(payload: dict, confirmed_label: str | None) -> PredictionItem:
    predictions = [PredictionItem.model_validate(item) for item in payload["predictions"]]
    if confirmed_label:
        for item in predictions:
            if item.class_name == confirmed_label:
                return item
        raise bad_request("确认标签必须来自当前诊断候选结果")
    if not predictions:
        raise bad_request("诊断草稿缺少候选结果")
    return predictions[0]


def _promote_image(image_filename: str, image_url: str) -> tuple[str, str]:
    source_path = settings.upload_dir / image_filename
    if not source_path.exists():
        image_path = Path(image_filename)
        if image_path.parts and image_path.parts[0] == "drafts":
            promoted_candidate = settings.upload_dir / image_path.name
            if promoted_candidate.exists():
                raise bad_request("该诊断草稿已完成建档，请勿重复提交")
        raise bad_request("诊断图片已过期或不存在，请重新上传")
    image_path = Path(image_filename)
    if image_path.parts and image_path.parts[0] == "drafts":
        final_name = image_path.name
        final_path = settings.upload_dir / final_name
        if final_path.exists():
            final_name = f"{uuid.uuid4().hex}_{image_path.name}"
            final_path = settings.upload_dir / final_name
        final_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.replace(final_path)
        return final_name, f"/api/static/uploads/{final_name}"
    return image_filename, image_url


def _case_to_schema(case: DiseaseCase) -> CaseOut:
    return CaseOut(
        id=case.id,
        prediction_record_id=case.prediction_record_id,
        image_url=case.image_url,
        image_filename=case.image_filename,
        predicted_label=case.predicted_label,
        predicted_display_name=to_display_name(case.predicted_label),
        confirmed_label=case.confirmed_label,
        confirmed_display_name=to_display_name(case.confirmed_label),
        crop_name=case.crop_name,
        disease_name=case.disease_name,
        health_status=case.health_status,
        confidence=case.confidence,
        status=case.status,
        province=case.province,
        city=case.city,
        district=case.district,
        region_code=case.region_code,
        lat=case.lat,
        lng=case.lng,
        advice=case.advice_json,
        evidence=[EvidenceItem.model_validate(item) for item in case.evidence_json],
        created_at=case.created_at,
    )


def _case_to_similar(case: DiseaseCase, similarity: float) -> SimilarCaseOut:
    reference_actions = case.advice_json.get("recommended_actions", [])[:2]
    return SimilarCaseOut(
        case_id=case.id,
        similarity=round(similarity, 4),
        confirmed_label=case.confirmed_label,
        display_name=to_display_name(case.confirmed_label),
        summary=case.diagnostic_summary,
        reference_actions=reference_actions,
        created_at=case.created_at,
    )


async def search_similar_cases(
    db: AsyncSession,
    label: str,
    limit: int | None = None,
    *,
    exclude_case_id: int | None = None,
) -> list[SimilarCaseOut]:
    limit = limit or settings.SIMILAR_CASE_LIMIT
    profile = parse_label(label)
    result = await db.execute(
        select(DiseaseCase).order_by(DiseaseCase.created_at.desc()).limit(100)
    )
    candidates = result.scalars().all()
    scored: list[tuple[float, DiseaseCase]] = []
    for case in candidates:
        if exclude_case_id is not None and case.id == exclude_case_id:
            continue
        case_profile = parse_label(case.confirmed_label)
        score = 0.0
        if case.confirmed_label == label:
            score += 0.7
        if case_profile.crop_name == profile.crop_name:
            score += 0.15
        if case_profile.disease_family == profile.disease_family:
            score += 0.1
        if case.health_status == profile.health_status:
            score += 0.05
        if score > 0.2:
            scored.append((round(score, 4), case))

    scored.sort(
        key=lambda item: (
            item[0],
            item[1].created_at.timestamp() if item[1].created_at else 0.0,
        ),
        reverse=True,
    )
    return [_case_to_similar(case, score) for score, case in scored[:limit]]


async def create_case_from_draft(
    db: AsyncSession,
    *,
    user_id: int,
    draft_token: str,
    confirmed_label: str | None,
    province: str | None = None,
    city: str | None = None,
    district: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
) -> tuple[CaseOut, list[SimilarCaseOut]]:
    payload = decode_draft_token(draft_token, user_id)
    selected_prediction = _prediction_from_payload(payload, confirmed_label)
    predictions = [PredictionItem.model_validate(item) for item in payload["predictions"]]
    knowledge_evidence = await knowledge_service.search_knowledge(
        db, selected_prediction.class_name, settings.DIAGNOSIS_EVIDENCE_LIMIT
    )
    similar_cases = await search_similar_cases(db, selected_prediction.class_name)
    advice = await advice_service.generate_advice(
        selected_prediction, predictions, knowledge_evidence, similar_cases
    )

    final_filename = payload["image_filename"]
    final_url = payload["image_url"]
    promoted_path: Path | None = None
    try:
        final_filename, final_url = _promote_image(payload["image_filename"], payload["image_url"])
        if final_filename != payload["image_filename"]:
            promoted_path = settings.upload_dir / final_filename

        selected_profile = parse_label(selected_prediction.class_name)
        prediction_record = PredictionRecord(
            user_id=user_id,
            image_filename=final_filename,
            image_url=final_url,
            top1_class=predictions[0].class_name,
            top1_confidence=predictions[0].confidence,
            top_k=payload["top_k"],
            results_json=[item.model_dump() for item in predictions],
        )
        db.add(prediction_record)
        await db.flush()

        normalized_province = alert_service.normalize_region_text(province)
        if normalized_province not in VALID_REGION_CODES:
            raise bad_request("请选择有效区域（区域1~区域5）")
        normalized_city = alert_service.normalize_region_text(city)
        normalized_district = alert_service.normalize_region_text(district)
        region_code = alert_service.build_region_code(
            normalized_province,
            normalized_city,
            normalized_district,
        )

        case = DiseaseCase(
            user_id=user_id,
            prediction_record_id=prediction_record.id,
            image_filename=final_filename,
            image_url=final_url,
            predicted_label=predictions[0].class_name,
            confirmed_label=selected_prediction.class_name,
            crop_name=selected_profile.crop_name,
            disease_name=selected_profile.condition_name,
            health_status=selected_profile.health_status,
            confidence=selected_prediction.confidence,
            status="confirmed",
            province=normalized_province,
            city=normalized_city,
            district=normalized_district,
            region_code=region_code,
            lat=lat,
            lng=lng,
            diagnostic_summary=advice.summary,
            advice_json=advice.model_dump(),
            evidence_json=[item.model_dump() for item in knowledge_evidence],
        )
        db.add(case)
        await db.commit()
        await db.refresh(case)
    except Exception:
        await db.rollback()
        if promoted_path is not None:
            promoted_path.unlink(missing_ok=True)
        raise

    try:
        await alert_service.evaluate_case_region_alert(db, case=case)
    except Exception:
        await db.rollback()

    refreshed_similar = await search_similar_cases(
        db,
        selected_prediction.class_name,
        exclude_case_id=case.id,
    )
    return _case_to_schema(case), refreshed_similar


async def get_case(db: AsyncSession, case_id: int, user_id: int) -> CaseOut:
    result = await db.execute(
        select(DiseaseCase).where(DiseaseCase.id == case_id, DiseaseCase.user_id == user_id)
    )
    case = result.scalar_one_or_none()
    if case is None:
        raise not_found("病例不存在")
    return _case_to_schema(case)
VALID_REGION_CODES = {"区域1", "区域2", "区域3", "区域4", "区域5"}
