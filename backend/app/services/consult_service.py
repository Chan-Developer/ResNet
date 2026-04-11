from ..schemas.consult import ConsultMessageIn
from .llm_service import complete_text


def _fallback_answer(question: str, history: list[ConsultMessageIn]) -> str:
    context_hint = ""
    if history:
        last_user = next((item for item in reversed(history) if item.role == "user"), None)
        if last_user is not None and last_user.content.strip() != question.strip():
            context_hint = f"结合你上一轮提到的“{last_user.content[:60]}”，"

    return (
        f"{context_hint}建议先补充 4 类关键信息后再决策：1. 作物和生育期；2. 受害部位与症状变化；"
        "3. 近 7 天温湿度、降雨和通风情况；4. 已使用药剂名称、剂量、间隔和施药覆盖情况。"
        "如果已经连续用药两次仍无明显改善，优先复核是否存在误诊、抗药性、施药时机不对或环境条件未控制住。"
        "在确认前，不建议继续盲目加大剂量，应保留病株照片并结合人工复核。"
    )


async def generate_consult_answer(question: str, history: list[ConsultMessageIn]) -> str:
    instructions = (
        "你是农业病害咨询助手。请根据用户问题和上下文，输出中文、简洁、可执行的建议。"
        "优先给出分步排查与处理意见，避免空泛表述。"
        "如果信息不足，要明确指出还需要补充哪些田间信息。"
        "不要输出 Markdown 代码块，不要假装已经看到图片。"
    )
    payload = {
        "question": question,
        "history": [item.model_dump() for item in history[-8:]],
    }
    answer = complete_text(
        instructions=instructions,
        input_payload=payload,
        max_output_tokens=700,
    )
    if answer:
        return answer
    return _fallback_answer(question, history)
