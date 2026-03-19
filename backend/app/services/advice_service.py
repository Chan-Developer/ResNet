import asyncio
import json
from typing import Optional
from urllib import error, request

from ..config import settings
from ..schemas.diagnosis import AdviceCitation, AdviceOut, EvidenceItem, SimilarCaseOut
from ..schemas.prediction import PredictionItem
from ..utils.label_parser import parse_label


def _build_uncertainty_notice(
    best_prediction: PredictionItem,
    predictions: list[PredictionItem],
    similar_cases: list[SimilarCaseOut],
) -> str:
    gap = 1.0
    if len(predictions) > 1:
        gap = round(best_prediction.confidence - predictions[1].confidence, 4)
    notes: list[str] = []
    if best_prediction.confidence < 0.75:
        notes.append("模型置信度偏低")
    if gap < 0.12:
        notes.append("Top1 与 Top2 差距较小")
    if not similar_cases:
        notes.append("暂无已确认相似病例可交叉参考")
    if not notes:
        notes.append("该建议基于单张图像和检索证据生成，仍建议结合田间环境复核")
    return "；".join(notes) + "。"


def _fallback_actions(profile_name: str, health_status: str) -> list[str]:
    if health_status == "healthy":
        return [
            "保持当前水肥和通风管理，不建议因为单次模型结果就大幅调整方案。",
            "保留本次图像，并在 3 到 7 天内从相同角度再拍一张做复查。",
            "若出现新斑点、卷叶、霉层或果实异常，应重新诊断并进行人工复核。",
        ]
    return [
        f"先把疑似 {profile_name} 的叶片或植株与周边健康植株隔离观察，减少交叉传播风险。",
        "短期内优先调整通风、湿度和灌溉方式，避免叶面长时间潮湿。",
        "保留病斑扩散记录与环境信息，必要时结合人工复核再决定具体用药或处理方案。",
    ]


def _build_fallback_advice(
    best_prediction: PredictionItem,
    predictions: list[PredictionItem],
    knowledge_evidence: list[EvidenceItem],
    similar_cases: list[SimilarCaseOut],
) -> AdviceOut:
    profile = parse_label(best_prediction.class_name)
    citations = [
        AdviceCitation(
            evidence_id=item.evidence_id,
            title=item.title,
            source_name=item.source_name,
        )
        for item in knowledge_evidence[:3]
    ]
    summary = (
        f"当前图像更接近 {profile.display_name}，模型置信度约 {best_prediction.confidence * 100:.1f}%。"
    )
    if profile.health_status == "healthy":
        condition_overview = (
            f"{profile.crop_name} 当前更接近健康状态，建议重点做持续监测，而不是直接按病害处置。"
        )
    else:
        condition_overview = (
            f"{profile.crop_name} 疑似出现 {profile.condition_name}，当前建议以隔离、环境控制和复查为主。"
        )
    if similar_cases:
        reference_case = similar_cases[0]
        reference_hint = (
            f"最近的相似病例为 #{reference_case.case_id}，可参考其已确认处置思路，但不要直接照搬。"
        )
    else:
        reference_hint = "当前暂无足够相似的已确认病例，建议缩短复查周期。"
    return AdviceOut(
        summary=summary,
        condition_overview=condition_overview,
        recommended_actions=_fallback_actions(profile.condition_name, profile.health_status),
        uncertainty_notice=_build_uncertainty_notice(best_prediction, predictions, similar_cases),
        follow_up=reference_hint,
        citations=citations,
    )


def _call_openai_chat(payload: dict) -> Optional[AdviceOut]:
    if not settings.OPENAI_API_KEY:
        return None

    system_prompt = (
        "你是农业植保助手。你必须只输出 JSON，字段包括：summary, condition_overview, "
        "recommended_actions, uncertainty_notice, follow_up, citations。"
        "recommended_actions 是字符串数组；citations 是数组，每项包含 evidence_id, title, source_name。"
        "输出必须保留证据引用，并明确不确定性提示。"
    )
    body = {
        "model": settings.OPENAI_MODEL,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
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
            content = json.loads(resp.read().decode("utf-8"))
        message = content["choices"][0]["message"]["content"]
        return AdviceOut.model_validate(json.loads(message))
    except (error.URLError, KeyError, ValueError, json.JSONDecodeError):
        return None


async def generate_advice(
    best_prediction: PredictionItem,
    predictions: list[PredictionItem],
    knowledge_evidence: list[EvidenceItem],
    similar_cases: list[SimilarCaseOut],
) -> AdviceOut:
    payload = {
        "diagnosis": best_prediction.class_name,
        "confidence": best_prediction.confidence,
        "predictions": [item.model_dump() for item in predictions],
        "evidences": [item.model_dump() for item in knowledge_evidence],
        "similar_cases": [item.model_dump(mode="json") for item in similar_cases],
    }
    llm_advice = await asyncio.to_thread(_call_openai_chat, payload)
    if llm_advice is not None:
        return llm_advice
    return _build_fallback_advice(best_prediction, predictions, knowledge_evidence, similar_cases)
