from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import uuid

import aiofiles
from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from ..config import settings


@dataclass
class SavedUpload:
    filename: str
    url: str
    image: Image.Image
    filepath: Path
    size_bytes: int


def guess_upload_url(subdir: str | None, filename: str) -> str:
    if subdir:
        return f"/api/static/uploads/{subdir}/{filename}"
    return f"/api/static/uploads/{filename}"


def payload_too_large(message: str) -> HTTPException:
    return HTTPException(status_code=413, detail=message)


def cleanup_file(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def cleanup_saved_uploads(saved_uploads: Iterable[SavedUpload]) -> None:
    for saved in saved_uploads:
        try:
            saved.image.close()
        except Exception:
            pass
        cleanup_file(saved.filepath)


def cleanup_expired_uploads(*, subdir: str, expire_minutes: int) -> None:
    target_dir = settings.upload_dir / subdir
    if not target_dir.exists():
        return
    from datetime import datetime, timedelta

    expire_before = datetime.now() - timedelta(minutes=expire_minutes)
    for path in target_dir.glob("*"):
        try:
            if path.is_file() and datetime.fromtimestamp(path.stat().st_mtime) < expire_before:
                path.unlink(missing_ok=True)
        except OSError:
            continue


async def save_image_upload(
    file: UploadFile,
    *,
    subdir: str | None = None,
    max_size_bytes: int | None = None,
) -> SavedUpload:
    ext = Path(file.filename or "").suffix or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    upload_dir = settings.upload_dir / subdir if subdir else settings.upload_dir
    upload_dir.mkdir(parents=True, exist_ok=True)
    filepath = upload_dir / filename
    size_bytes = 0
    size_limit = max_size_bytes if max_size_bytes is not None else settings.max_upload_size_bytes

    try:
        async with aiofiles.open(filepath, "wb") as handle:
            while True:
                chunk = await file.read(settings.UPLOAD_CHUNK_SIZE)
                if not chunk:
                    break
                size_bytes += len(chunk)
                if size_bytes > size_limit:
                    raise payload_too_large(f"单个文件大小不能超过 {settings.MAX_UPLOAD_SIZE_MB}MB")
                await handle.write(chunk)
    except Exception:
        cleanup_file(filepath)
        raise
    finally:
        await file.close()

    try:
        with Image.open(filepath) as opened:
            image = opened.convert("RGB")
    except (UnidentifiedImageError, Exception):
        cleanup_file(filepath)
        raise HTTPException(status_code=400, detail="上传文件不是有效图片")

    return SavedUpload(
        filename=f"{subdir}/{filename}" if subdir else filename,
        url=guess_upload_url(subdir, filename),
        image=image,
        filepath=filepath,
        size_bytes=size_bytes,
    )
