import json
from typing import Any, Optional

from ..config import settings


def _get_ark_client():
    try:
        from volcenginesdkarkruntime import Ark
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency: volcengine-python-sdk[ark]. Run `pip install -r requirements.txt`."
        ) from exc
    return Ark


def _extract_response_text(response: Any) -> str:
    output = getattr(response, "output", None) or []
    texts: list[str] = []

    for item in output:
        contents = getattr(item, "content", None) or []
        for content in contents:
            if getattr(content, "type", None) == "output_text":
                text = getattr(content, "text", None)
                if text:
                    texts.append(text)

    if texts:
        return "\n".join(texts).strip()

    output_text = getattr(response, "output_text", None)
    if output_text:
        return output_text.strip()

    raise RuntimeError(f"Ark 响应中未找到文本内容: {response}")


def _strip_markdown_code_fence(text: str) -> str:
    cleaned = text.strip()
    if not cleaned.startswith("```"):
        return cleaned

    lines = cleaned.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _call_doubao(
    *,
    instructions: str,
    input_payload: Any,
    max_output_tokens: int = 800,
) -> Optional[str]:
    if not settings.ARK_API_KEY:
        return None

    try:
        Ark = _get_ark_client()
        client = Ark(
            api_key=settings.ARK_API_KEY,
            base_url=settings.ARK_BASE_URL.rstrip("/"),
        )
        input_text = (
            input_payload
            if isinstance(input_payload, str)
            else json.dumps(input_payload, ensure_ascii=False)
        )
        response = client.responses.create(
            model=settings.ARK_MODEL,
            instructions=instructions,
            input=input_text,
            max_output_tokens=max_output_tokens,
            temperature=0.2,
            thinking={"type": "disabled"},
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
        return _extract_response_text(response)
    except Exception:
        return None


def complete_text(
    *,
    instructions: str,
    input_payload: Any,
    max_output_tokens: int = 800,
) -> Optional[str]:
    provider = settings.LLM_PROVIDER.strip().lower()
    if provider in {"doubao", "ark", "volcengine"}:
        return _call_doubao(
            instructions=instructions,
            input_payload=input_payload,
            max_output_tokens=max_output_tokens,
        )
    return None


def complete_json_object(
    *,
    instructions: str,
    input_payload: Any,
    max_output_tokens: int = 800,
) -> Optional[dict[str, Any]]:
    text = complete_text(
        instructions=instructions,
        input_payload=input_payload,
        max_output_tokens=max_output_tokens,
    )
    if not text:
        return None

    try:
        parsed = json.loads(_strip_markdown_code_fence(text))
    except json.JSONDecodeError:
        return None

    if isinstance(parsed, dict):
        return parsed
    return None
