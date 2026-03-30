from pathlib import Path

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


def to_display_name(name: str) -> str:
    return name.replace("___", " - ").replace("_", " ")
