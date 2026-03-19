from dataclasses import dataclass
import re

from .class_names import to_display_name


FAMILY_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("virus", ("virus", "mosaic", "curl")),
    ("bacterial", ("bacterial",)),
    ("mite", ("mite", "mites")),
    ("mildew", ("mildew",)),
    ("mold", ("mold",)),
    ("rust", ("rust",)),
    ("blight", ("blight",)),
    ("spot", ("spot",)),
    ("rot", ("rot",)),
    ("scab", ("scab",)),
    ("greening", ("greening", "haunglongbing")),
]


@dataclass(frozen=True)
class LabelProfile:
    class_name: str
    display_name: str
    crop_name: str
    crop_key: str
    condition_name: str
    condition_key: str
    health_status: str
    disease_family: str


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _detect_family(condition_key: str, health_status: str) -> str:
    if health_status == "healthy":
        return "healthy"
    for family, keywords in FAMILY_RULES:
        if any(keyword in condition_key for keyword in keywords):
            return family
    return "general"


def parse_label(label: str) -> LabelProfile:
    crop_raw, _, condition_raw = label.partition("___")
    display_name = to_display_name(label)
    crop_name = to_display_name(crop_raw or label)
    condition_name = to_display_name(condition_raw or "Unknown")
    condition_key = _slugify(condition_raw or "unknown")
    health_status = "healthy" if condition_key == "healthy" else "diseased"
    return LabelProfile(
        class_name=label,
        display_name=display_name,
        crop_name=crop_name,
        crop_key=_slugify(crop_raw or label),
        condition_name=condition_name,
        condition_key=condition_key,
        health_status=health_status,
        disease_family=_detect_family(condition_key, health_status),
    )
