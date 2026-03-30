from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.case import KnowledgeChunk
from ..schemas.admin_manage import KnowledgeChunkCreate, KnowledgeChunkUpdate
from ..schemas.diagnosis import EvidenceItem
from ..utils.label_parser import LabelProfile, parse_label
from ..utils.errors import bad_request, not_found


def _family_title(profile: LabelProfile) -> str:
    if profile.disease_family == "healthy":
        return "健康管理"
    return {
        "virus": "病毒类病害",
        "bacterial": "细菌性病害",
        "mite": "虫螨危害",
        "mildew": "白粉病类病害",
        "mold": "霉层类病害",
        "rust": "锈病类病害",
        "blight": "疫病/枯萎类病害",
        "spot": "斑点类病害",
        "rot": "腐烂类病害",
        "scab": "疮痂类病害",
        "greening": "黄龙病类病害",
        "general": "病害通用处置",
    }.get(profile.disease_family, "病害通用处置")


def _build_exact_chunks(label: str) -> list[KnowledgeChunk]:
    profile = parse_label(label)
    source_name = "PlantCare 农业知识库"
    common_tags = [profile.crop_key, profile.disease_family, profile.health_status]
    if profile.health_status == "healthy":
        return [
            KnowledgeChunk(
                label_key=label,
                crop_name=profile.crop_name,
                disease_family=profile.disease_family,
                health_status=profile.health_status,
                source_name=source_name,
                title=f"{profile.display_name} 养护提示",
                content=(
                    f"{profile.crop_name} 当前更接近健康状态。建议保持通风、稳定水肥与叶面清洁，"
                    "继续观察新叶和叶背，避免在高湿环境下长期闷棚。"
                ),
                tags_json=common_tags,
            ),
            KnowledgeChunk(
                label_key=label,
                crop_name=profile.crop_name,
                disease_family=profile.disease_family,
                health_status=profile.health_status,
                source_name=source_name,
                title=f"{profile.crop_name} 健康复查建议",
                content=(
                    "即使模型判为健康，也建议保留原图并在 3 到 7 天内复查一次；若后续出现卷叶、斑点、霉层或"
                    "颜色异常，应重新上传并结合田间环境进行判断。"
                ),
                tags_json=common_tags,
            ),
        ]

    return [
        KnowledgeChunk(
            label_key=label,
            crop_name=profile.crop_name,
            disease_family=profile.disease_family,
            health_status=profile.health_status,
            source_name=source_name,
            title=f"{profile.display_name} 识别要点",
            content=(
                f"{profile.crop_name} 出现 {profile.condition_name} 时，通常需要重点检查病斑扩展速度、"
                "是否伴随叶缘坏死、叶背霉层、卷曲或颜色失真，并与近期湿度、温度和灌溉情况一起判断。"
            ),
            tags_json=common_tags,
        ),
        KnowledgeChunk(
            label_key=label,
            crop_name=profile.crop_name,
            disease_family=profile.disease_family,
            health_status=profile.health_status,
            source_name=source_name,
            title=f"{profile.display_name} 初步处置",
            content=(
                "建议先隔离疑似叶片，降低叶面持续潮湿时间，暂停过度喷施叶面肥，"
                "并记录拍摄日期、地块条件和扩散范围，为后续复查或人工复核提供依据。"
            ),
            tags_json=common_tags,
        ),
    ]


def _build_generic_family_chunk(profile: LabelProfile) -> KnowledgeChunk:
    family_title = _family_title(profile)
    content_map = {
        "virus": "病毒类病害通常更依赖隔离、清除病株与媒介昆虫防控。若新叶持续卷曲、花果发育异常，应尽快线下复核。",
        "bacterial": "细菌性病害要重点控制水传播与工具传播。建议减少叶面喷水，修剪和操作后及时消毒工具。",
        "mite": "虫螨危害应检查叶背和嫩梢，关注点状失绿和网丝迹象，必要时结合田间虫情综合防控。",
        "mildew": "白粉和霉层类病害通常与通风不足和湿度偏高有关，优先改善通风并控制叶面长时间潮湿。",
        "mold": "霉层类问题常与高湿和郁闭环境相关，应同步处理病叶与环境条件，避免只处理单片叶片。",
        "rust": "锈病类病害需要关注病斑扩散和孢子传播，建议加强田间卫生并避免带露操作。",
        "blight": "疫病和枯萎类病害扩展可能较快，建议缩短复查间隔，必要时尽快进行人工诊断确认。",
        "spot": "斑点类病害要结合病斑颜色、边缘形态和扩散速度综合判断，避免仅凭单张叶片做绝对结论。",
        "rot": "腐烂类病害往往提示组织已经受损，建议及时移除严重病组织并检查水分管理与通风条件。",
        "scab": "疮痂类病害通常需要同步关注果面或嫩叶新发症状，复查时尽量固定拍摄角度便于对比。",
        "greening": "黄龙病等系统性病害具有较高风险，模型结果仅可作为筛查依据，建议优先做人工和现场综合确认。",
        "general": "模型识别仅是初筛，建议结合田间环境、扩散速度和多张图片复查，不建议直接将模型结果等同于最终诊断。",
        "healthy": "健康状态也应保留复查机制，若环境骤变或新叶异常，应重新识别并对比历史图像。",
    }
    return KnowledgeChunk(
        label_key=None,
        crop_name=None,
        disease_family=profile.disease_family,
        health_status=profile.health_status,
        source_name="PlantCare 农业知识库",
        title=f"{family_title} 通用建议",
        content=content_map[profile.disease_family],
        tags_json=[profile.disease_family, profile.health_status],
    )


def _build_global_safety_chunk() -> KnowledgeChunk:
    return KnowledgeChunk(
        label_key=None,
        crop_name=None,
        disease_family="general",
        health_status="diseased",
        source_name="PlantCare 风险提示",
        title="线下复核与不确定性提示",
        content=(
            "若模型前两名置信度接近、症状分布不典型，或植株已经出现大面积黄化、萎蔫、果实异常，"
            "应把当前结果视为辅助判断，并尽快进行线下复核。"
        ),
        tags_json=["uncertainty", "safety"],
    )


async def bootstrap_knowledge(db: AsyncSession, class_names: list[str]) -> None:
    count_result = await db.execute(select(func.count()).select_from(KnowledgeChunk))
    if (count_result.scalar() or 0) > 0:
        return

    chunks: list[KnowledgeChunk] = []
    seen_families: set[tuple[str, str]] = set()
    for label in class_names:
        profile = parse_label(label)
        chunks.extend(_build_exact_chunks(label))
        family_key = (profile.disease_family, profile.health_status)
        if family_key not in seen_families:
            chunks.append(_build_generic_family_chunk(profile))
            seen_families.add(family_key)
    chunks.append(_build_global_safety_chunk())
    db.add_all(chunks)
    await db.commit()


def _normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_tags(values: list[str] | None) -> list[str]:
    if not values:
        return []
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = value.strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        result.append(cleaned)
    return result


def _to_manage_dict(chunk: KnowledgeChunk) -> dict:
    return {
        "id": chunk.id,
        "label_key": chunk.label_key,
        "crop_name": chunk.crop_name,
        "disease_family": chunk.disease_family,
        "health_status": chunk.health_status,
        "source_type": chunk.source_type,
        "source_name": chunk.source_name,
        "title": chunk.title,
        "content": chunk.content,
        "url": chunk.url or "",
        "tags_json": _normalize_tags(chunk.tags_json if isinstance(chunk.tags_json, list) else []),
        "created_at": chunk.created_at,
        "updated_at": chunk.updated_at,
    }


async def list_knowledge_chunks(
    db: AsyncSession,
    *,
    keyword: str | None = None,
    label_key: str | None = None,
    crop_name: str | None = None,
    disease_family: str | None = None,
    health_status: str | None = None,
    limit: int = 300,
) -> list[dict]:
    stmt = select(KnowledgeChunk).order_by(KnowledgeChunk.updated_at.desc(), KnowledgeChunk.id.desc())

    keyword_value = _normalize_optional(keyword)
    label_value = _normalize_optional(label_key)
    crop_value = _normalize_optional(crop_name)
    family_value = _normalize_optional(disease_family)
    status_value = _normalize_optional(health_status)

    if keyword_value:
        like_value = f"%{keyword_value}%"
        stmt = stmt.where(
            or_(
                KnowledgeChunk.title.ilike(like_value),
                KnowledgeChunk.content.ilike(like_value),
                KnowledgeChunk.source_name.ilike(like_value),
                KnowledgeChunk.label_key.ilike(like_value),
            )
        )
    if label_value:
        stmt = stmt.where(KnowledgeChunk.label_key == label_value)
    if crop_value:
        stmt = stmt.where(KnowledgeChunk.crop_name == crop_value)
    if family_value:
        stmt = stmt.where(KnowledgeChunk.disease_family == family_value)
    if status_value:
        stmt = stmt.where(KnowledgeChunk.health_status == status_value)

    limit = max(1, min(limit, 1000))
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    chunks = result.scalars().all()
    return [_to_manage_dict(chunk) for chunk in chunks]


async def create_knowledge_chunk(db: AsyncSession, payload: KnowledgeChunkCreate) -> dict:
    title = payload.title.strip()
    content = payload.content.strip()
    if not title:
        raise bad_request("标题不能为空")
    if not content:
        raise bad_request("内容不能为空")

    chunk = KnowledgeChunk(
        label_key=_normalize_optional(payload.label_key),
        crop_name=_normalize_optional(payload.crop_name),
        disease_family=_normalize_optional(payload.disease_family),
        health_status=payload.health_status.strip() or "diseased",
        source_type=payload.source_type.strip() or "internal",
        source_name=payload.source_name.strip() or "PlantCare 知识库",
        title=title,
        content=content,
        url=payload.url.strip(),
        tags_json=_normalize_tags(payload.tags_json),
    )
    db.add(chunk)
    await db.commit()
    await db.refresh(chunk)
    return _to_manage_dict(chunk)


async def update_knowledge_chunk(db: AsyncSession, chunk_id: int, payload: KnowledgeChunkUpdate) -> dict:
    chunk = await db.get(KnowledgeChunk, chunk_id)
    if chunk is None:
        raise not_found("知识条目不存在")

    touched = False
    if payload.label_key is not None:
        chunk.label_key = _normalize_optional(payload.label_key)
        touched = True
    if payload.crop_name is not None:
        chunk.crop_name = _normalize_optional(payload.crop_name)
        touched = True
    if payload.disease_family is not None:
        chunk.disease_family = _normalize_optional(payload.disease_family)
        touched = True
    if payload.health_status is not None:
        status = payload.health_status.strip()
        if not status:
            raise bad_request("health_status 不能为空")
        chunk.health_status = status
        touched = True
    if payload.source_type is not None:
        source_type = payload.source_type.strip()
        if not source_type:
            raise bad_request("source_type 不能为空")
        chunk.source_type = source_type
        touched = True
    if payload.source_name is not None:
        source_name = payload.source_name.strip()
        if not source_name:
            raise bad_request("source_name 不能为空")
        chunk.source_name = source_name
        touched = True
    if payload.title is not None:
        title = payload.title.strip()
        if not title:
            raise bad_request("标题不能为空")
        chunk.title = title
        touched = True
    if payload.content is not None:
        content = payload.content.strip()
        if not content:
            raise bad_request("内容不能为空")
        chunk.content = content
        touched = True
    if payload.url is not None:
        chunk.url = payload.url.strip()
        touched = True
    if payload.tags_json is not None:
        chunk.tags_json = _normalize_tags(payload.tags_json)
        touched = True

    if not touched:
        raise bad_request("至少需要更新一个字段")

    await db.commit()
    await db.refresh(chunk)
    return _to_manage_dict(chunk)


async def delete_knowledge_chunk(db: AsyncSession, chunk_id: int) -> None:
    chunk = await db.get(KnowledgeChunk, chunk_id)
    if chunk is None:
        raise not_found("知识条目不存在")
    await db.delete(chunk)
    await db.commit()


async def search_knowledge(
    db: AsyncSession, label: str, limit: int = 4
) -> list[EvidenceItem]:
    profile = parse_label(label)
    result = await db.execute(
        select(KnowledgeChunk).where(
            or_(
                KnowledgeChunk.label_key == label,
                KnowledgeChunk.crop_name == profile.crop_name,
                KnowledgeChunk.disease_family == profile.disease_family,
                KnowledgeChunk.health_status == profile.health_status,
            )
        )
    )
    chunks = result.scalars().all()
    scored: list[tuple[float, KnowledgeChunk]] = []
    for chunk in chunks:
        score = 0.2
        if chunk.label_key == label:
            score += 0.5
        if chunk.crop_name and chunk.crop_name == profile.crop_name:
            score += 0.15
        if chunk.disease_family and chunk.disease_family == profile.disease_family:
            score += 0.1
        if chunk.health_status == profile.health_status:
            score += 0.1
        if chunk.source_name == "PlantCare 风险提示":
            score -= 0.05
        scored.append((round(score, 4), chunk))

    scored.sort(key=lambda item: item[0], reverse=True)
    evidences: list[EvidenceItem] = []
    seen_ids: set[int] = set()
    for score, chunk in scored:
        if chunk.id in seen_ids:
            continue
        seen_ids.add(chunk.id)
        evidences.append(EvidenceItem(
            evidence_id=f"K{chunk.id}",
            evidence_type="knowledge",
            title=chunk.title,
            source_name=chunk.source_name,
            snippet=chunk.content,
            score=score,
            url=chunk.url or "",
        ))
        if len(evidences) >= limit:
            break
    return evidences
