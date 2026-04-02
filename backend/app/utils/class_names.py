from pathlib import Path
import re

from ..config import settings


def _read_class_names_file(path: Path) -> list[str]:
    if not path.exists() or not path.is_file():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _read_class_names_from_dataset(path: Path) -> list[str]:
    if not path.exists() or not path.is_dir():
        return []
    return sorted(p.name for p in path.iterdir() if p.is_dir())


def load_class_names(
    class_names_path: Path | None = None,
    dataset_dir: Path | None = None,
) -> tuple[list[str], Path]:
    resolved_class_names_path = class_names_path or settings.class_names_path
    resolved_dataset_dir = dataset_dir or settings.dataset_dir

    class_names = _read_class_names_file(resolved_class_names_path)
    if class_names:
        return class_names, resolved_class_names_path

    class_names = _read_class_names_from_dataset(resolved_dataset_dir)
    if class_names:
        return class_names, resolved_dataset_dir

    raise FileNotFoundError(
        "未找到类别标签。请提供 class_names.txt 或有效的数据集目录。"
    )


_CROP_CN_MAP = {
    "apple": "苹果",
    "blueberry": "蓝莓",
    "cherry including sour": "樱桃",
    "corn maize": "玉米",
    "grape": "葡萄",
    "orange": "柑橘",
    "peach": "桃",
    "pepper bell": "甜椒",
    "potato": "马铃薯",
    "raspberry": "覆盆子",
    "soybean": "大豆",
    "squash": "南瓜",
    "strawberry": "草莓",
    "tomato": "番茄",
}

_CONDITION_CN_MAP = {
    "apple scab": "苹果疮痂病",
    "black rot": "黑腐病",
    "cedar apple rust": "雪松苹果锈病",
    "healthy": "健康",
    "powdery mildew": "白粉病",
    "cercospora leaf spot gray leaf spot": "灰斑病",
    "common rust": "普通锈病",
    "northern leaf blight": "北方叶枯病",
    "esca black measles": "埃斯卡病（黑麻疹）",
    "leaf blight isariopsis leaf spot": "叶枯病（异孢叶斑）",
    "haunglongbing citrus greening": "黄龙病（柑橘黄化病）",
    "bacterial spot": "细菌性斑点病",
    "early blight": "早疫病",
    "late blight": "晚疫病",
    "leaf mold": "叶霉病",
    "septoria leaf spot": "斑枯病",
    "spider mites two spotted spider mite": "二斑叶螨",
    "target spot": "靶斑病",
    "tomato yellow leaf curl virus": "番茄黄化曲叶病毒病",
    "tomato mosaic virus": "番茄花叶病毒病",
    "leaf scorch": "叶焦病",
    "unknown": "未知",
}


def _normalize_key(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", value.lower())).strip()


def _to_readable_fallback(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("___", " - ").replace("_", " ")).strip()


def _translate_segment(value: str, mapping: dict[str, str]) -> str | None:
    if not value:
        return None
    return mapping.get(_normalize_key(value))


def to_display_name(name: str) -> str:
    text = (name or "").strip()
    if not text:
        return ""

    crop_raw, sep, condition_raw = text.partition("___")
    if sep:
        crop_display = _translate_segment(crop_raw, _CROP_CN_MAP) or _to_readable_fallback(crop_raw)
        condition_display = _translate_segment(condition_raw, _CONDITION_CN_MAP) or _to_readable_fallback(condition_raw)
        return f"{crop_display} - {condition_display}"

    direct = _translate_segment(text, _CROP_CN_MAP) or _translate_segment(text, _CONDITION_CN_MAP)
    if direct:
        return direct
    return _to_readable_fallback(text)
