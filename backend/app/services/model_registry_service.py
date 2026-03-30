from pathlib import Path
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models.model_registry import ModelVersion
from ..schemas.admin_manage import ModelVersionCreate, ModelVersionUpdate
from ..services.model_service import model_service
from ..utils.errors import bad_request, not_found


def _normalize_text(value: str) -> str:
    return value.strip()


def _normalize_optional_text(value: str | None) -> str:
    if value is None:
        return ""
    return value.strip()


def _resolve_path(raw_path: str) -> Path:
    cleaned = raw_path.strip()
    if not cleaned:
        raise bad_request("路径不能为空")
    path = Path(cleaned).expanduser()
    if not path.is_absolute():
        path = settings.BASE_DIR / path
    return path.resolve()


def _path_to_string(path: Path) -> str:
    return str(path)


def _validate_model_path(path_text: str) -> str:
    resolved = _resolve_path(path_text)
    if not resolved.exists() or not resolved.is_file():
        raise bad_request(f"模型权重文件不存在: {resolved}")
    return _path_to_string(resolved)


def _validate_class_names_path(path_text: str | None) -> str:
    cleaned = _normalize_optional_text(path_text)
    if not cleaned:
        return ""
    resolved = _resolve_path(cleaned)
    if not resolved.exists() or not resolved.is_file():
        raise bad_request(f"类别文件不存在: {resolved}")
    return _path_to_string(resolved)


def _is_runtime_loaded(version: ModelVersion) -> bool:
    runtime_model_path = _normalize_optional_text(model_service.model_path)
    if not runtime_model_path:
        return False
    model_path = _normalize_optional_text(version.model_path)
    if runtime_model_path != model_path:
        return False

    runtime_class_source = _normalize_optional_text(model_service.class_names_source)
    version_class_source = _normalize_optional_text(version.class_names_path)
    if not version_class_source:
        return version.is_active and bool(runtime_model_path)
    return runtime_class_source == version_class_source


def _to_version_dict(version: ModelVersion) -> dict[str, Any]:
    metrics = version.metrics_json if isinstance(version.metrics_json, dict) else {}
    return {
        "id": version.id,
        "version_code": version.version_code,
        "display_name": version.display_name,
        "description": version.description or "",
        "model_path": version.model_path,
        "class_names_path": version.class_names_path or "",
        "metrics_json": metrics,
        "is_active": bool(version.is_active),
        "is_runtime_loaded": _is_runtime_loaded(version),
        "created_at": version.created_at,
        "updated_at": version.updated_at,
    }


async def bootstrap_default_model_version(db: AsyncSession) -> None:
    result = await db.execute(select(ModelVersion).order_by(ModelVersion.id.asc()))
    versions = list(result.scalars().all())
    if not versions:
        default_model_path = _path_to_string(settings.model_path.resolve())
        default_class_names_path = ""
        if settings.class_names_path.exists() and settings.class_names_path.is_file():
            default_class_names_path = _path_to_string(settings.class_names_path.resolve())
        db.add(
            ModelVersion(
                version_code="default",
                display_name="系统默认模型",
                description="由系统配置初始化的默认推理模型",
                model_path=default_model_path,
                class_names_path=default_class_names_path,
                metrics_json={},
                is_active=True,
            )
        )
        await db.commit()
        return

    if any(version.is_active for version in versions):
        return
    versions[0].is_active = True
    await db.commit()


async def list_model_versions(db: AsyncSession) -> list[dict[str, Any]]:
    result = await db.execute(
        select(ModelVersion).order_by(ModelVersion.is_active.desc(), ModelVersion.updated_at.desc(), ModelVersion.id.desc())
    )
    return [_to_version_dict(item) for item in result.scalars().all()]


async def get_active_model_version(db: AsyncSession) -> ModelVersion | None:
    result = await db.execute(
        select(ModelVersion).where(ModelVersion.is_active.is_(True)).order_by(ModelVersion.updated_at.desc(), ModelVersion.id.desc())
    )
    return result.scalar_one_or_none()


async def get_model_version(db: AsyncSession, version_id: int) -> ModelVersion:
    item = await db.get(ModelVersion, version_id)
    if item is None:
        raise not_found("模型版本不存在")
    return item


async def create_model_version(db: AsyncSession, payload: ModelVersionCreate) -> dict[str, Any]:
    version_code = _normalize_text(payload.version_code)
    display_name = _normalize_text(payload.display_name)
    if not version_code:
        raise bad_request("version_code 不能为空")
    if not display_name:
        raise bad_request("display_name 不能为空")

    existing = await db.execute(select(ModelVersion).where(ModelVersion.version_code == version_code))
    if existing.scalar_one_or_none() is not None:
        raise bad_request("version_code 已存在")

    item = ModelVersion(
        version_code=version_code,
        display_name=display_name,
        description=_normalize_optional_text(payload.description),
        model_path=_validate_model_path(payload.model_path),
        class_names_path=_validate_class_names_path(payload.class_names_path),
        metrics_json=payload.metrics_json if isinstance(payload.metrics_json, dict) else {},
        is_active=False,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return _to_version_dict(item)


async def update_model_version(db: AsyncSession, version_id: int, payload: ModelVersionUpdate) -> dict[str, Any]:
    item = await get_model_version(db, version_id)
    touched = False
    reload_runtime = False

    if payload.version_code is not None:
        next_code = _normalize_text(payload.version_code)
        if not next_code:
            raise bad_request("version_code 不能为空")
        if next_code != item.version_code:
            existing = await db.execute(
                select(ModelVersion).where(ModelVersion.version_code == next_code, ModelVersion.id != version_id)
            )
            if existing.scalar_one_or_none() is not None:
                raise bad_request("version_code 已存在")
            item.version_code = next_code
            touched = True
    if payload.display_name is not None:
        name = _normalize_text(payload.display_name)
        if not name:
            raise bad_request("display_name 不能为空")
        item.display_name = name
        touched = True
    if payload.description is not None:
        item.description = _normalize_optional_text(payload.description)
        touched = True
    if payload.model_path is not None:
        item.model_path = _validate_model_path(payload.model_path)
        touched = True
        reload_runtime = True
    if payload.class_names_path is not None:
        item.class_names_path = _validate_class_names_path(payload.class_names_path)
        touched = True
        reload_runtime = True
    if payload.metrics_json is not None:
        item.metrics_json = payload.metrics_json if isinstance(payload.metrics_json, dict) else {}
        touched = True

    if not touched:
        raise bad_request("至少需要更新一个字段")

    if item.is_active and reload_runtime:
        model_path = _resolve_path(item.model_path)
        class_names_path = _resolve_path(item.class_names_path) if item.class_names_path else None
        try:
            model_service.load(model_path=model_path, class_names_path=class_names_path)
        except Exception as exc:
            raise bad_request(f"模型加载失败: {exc}") from exc

    await db.commit()
    await db.refresh(item)
    return _to_version_dict(item)


async def delete_model_version(db: AsyncSession, version_id: int) -> None:
    item = await get_model_version(db, version_id)
    if item.is_active:
        raise bad_request("激活中的模型版本不能删除")

    count = int(await db.scalar(select(func.count()).select_from(ModelVersion)) or 0)
    if count <= 1:
        raise bad_request("至少需要保留一个模型版本")

    await db.delete(item)
    await db.commit()


async def activate_model_version(db: AsyncSession, version_id: int) -> dict[str, Any]:
    item = await get_model_version(db, version_id)
    model_path = _resolve_path(item.model_path)
    if not model_path.exists() or not model_path.is_file():
        raise bad_request(f"模型权重文件不存在: {model_path}")
    class_names_path = _resolve_path(item.class_names_path) if item.class_names_path else None
    if class_names_path is not None and (not class_names_path.exists() or not class_names_path.is_file()):
        raise bad_request(f"类别文件不存在: {class_names_path}")

    try:
        model_service.load(model_path=model_path, class_names_path=class_names_path)
    except Exception as exc:
        raise bad_request(f"模型加载失败: {exc}") from exc

    await db.execute(update(ModelVersion).values(is_active=False))
    item.is_active = True
    await db.commit()
    await db.refresh(item)
    return _to_version_dict(item)


async def get_model_runtime_info(db: AsyncSession) -> dict[str, Any]:
    active = await get_active_model_version(db)
    runtime = model_service.runtime_info()
    return {
        "active_version_id": active.id if active else None,
        "active_version_code": active.version_code if active else None,
        **runtime,
    }
