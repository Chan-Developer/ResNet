import math
from pathlib import Path
from typing import List

from ..config import settings
from ..schemas.dataset import CategoryImageOut, CategoryOut

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}


def get_categories() -> List[CategoryOut]:
    dataset_dir = settings.dataset_dir
    if not dataset_dir.exists():
        return []
    categories = []
    for p in sorted(dataset_dir.iterdir()):
        if not p.is_dir():
            continue
        count = sum(1 for f in p.iterdir() if f.suffix.lower() in IMAGE_EXTENSIONS)
        categories.append(CategoryOut(
            name=p.name,
            display_name=p.name.replace("___", " - ").replace("_", " "),
            count=count,
        ))
    return categories


def get_category_images(
    name: str, page: int = 1, size: int = 20
) -> dict:
    category_dir = settings.dataset_dir / name
    if not category_dir.exists() or not category_dir.is_dir():
        return None

    all_images = sorted(
        [f.name for f in category_dir.iterdir() if f.suffix.lower() in IMAGE_EXTENSIONS]
    )
    total = len(all_images)
    pages = math.ceil(total / size) if total > 0 else 0
    start = (page - 1) * size
    page_images = all_images[start : start + size]

    items = [
        CategoryImageOut(
            filename=fname,
            url=f"/api/static/datasets/{name}/{fname}",
        )
        for fname in page_images
    ]
    return {"items": items, "total": total, "page": page, "size": size, "pages": pages}
