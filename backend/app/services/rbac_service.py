import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import ROLE_ADMIN, ROLE_EXPERT, ROLE_USER, RolePermission
from ..utils.errors import bad_request

PERMISSION_CATALOG: list[dict[str, str]] = [
    {"code": "predict:single", "name": "单张识别", "description": "执行单张图片病害识别"},
    {"code": "predict:batch", "name": "批量识别", "description": "执行批量图片病害识别"},
    {"code": "diagnosis:confirm", "name": "确认建档", "description": "确认诊断并写入病例库"},
    {"code": "history:view", "name": "查看历史", "description": "查看个人识别历史记录"},
    {"code": "history:delete", "name": "删除历史", "description": "删除个人识别历史记录"},
    {"code": "dataset:view", "name": "浏览数据集", "description": "浏览数据集类别和样本"},
    {"code": "admin:user", "name": "用户管理", "description": "管理用户角色和启用状态"},
    {"code": "admin:role", "name": "角色权限管理", "description": "配置角色可用权限"},
    {"code": "admin:alert", "name": "区域预警管理", "description": "查看和处理区域病害增长预警"},
]

ROLE_LABELS = {
    ROLE_ADMIN: "系统管理员",
    ROLE_EXPERT: "专家用户",
    ROLE_USER: "普通用户",
}

ROLE_ORDER = [ROLE_ADMIN, ROLE_EXPERT, ROLE_USER]

DEFAULT_ROLE_PERMISSIONS = {
    ROLE_ADMIN: [item["code"] for item in PERMISSION_CATALOG],
    ROLE_EXPERT: [
        "predict:single",
        "predict:batch",
        "diagnosis:confirm",
        "history:view",
        "history:delete",
        "dataset:view",
    ],
    ROLE_USER: [
        "predict:single",
        "diagnosis:confirm",
        "history:view",
        "dataset:view",
    ],
}


def list_permission_catalog() -> list[dict[str, str]]:
    return [dict(item) for item in PERMISSION_CATALOG]


def normalize_role_code(role: str | None) -> str:
    return (role or "").strip().lower()


def list_roles() -> list[str]:
    return ROLE_ORDER[:]


def list_role_labels() -> dict[str, str]:
    return dict(ROLE_LABELS)


def _permission_code_set() -> set[str]:
    return {item["code"] for item in PERMISSION_CATALOG}


def _normalize_permissions(values: list[str]) -> list[str]:
    valid_codes = _permission_code_set()
    unique_codes: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        if value not in valid_codes:
            continue
        seen.add(value)
        unique_codes.append(value)
    return unique_codes


def default_permissions_for_role(role: str) -> list[str]:
    normalized = normalize_role_code(role)
    return DEFAULT_ROLE_PERMISSIONS.get(normalized, DEFAULT_ROLE_PERMISSIONS[ROLE_USER])[:]


def _parse_permission_json(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        payload: Any = json.loads(raw)
    except Exception:
        return []
    if not isinstance(payload, list):
        return []
    text_values = [value for value in payload if isinstance(value, str)]
    return _normalize_permissions(text_values)


async def get_role_permissions(db: AsyncSession, role: str) -> list[str]:
    normalized_role = normalize_role_code(role)
    if normalized_role == ROLE_ADMIN:
        return default_permissions_for_role(normalized_role)
    result = await db.execute(select(RolePermission).where(RolePermission.role == normalized_role))
    row = result.scalar_one_or_none()
    if row is None:
        return default_permissions_for_role(normalized_role)
    parsed = _parse_permission_json(row.permissions_json)
    if parsed:
        return parsed
    return default_permissions_for_role(normalized_role)


async def list_role_permission_entries(db: AsyncSession) -> list[dict[str, Any]]:
    role_permissions: list[dict[str, Any]] = []
    for role in ROLE_ORDER:
        permissions = await get_role_permissions(db, role)
        role_permissions.append(
            {
                "role": role,
                "label": ROLE_LABELS.get(role, role),
                "permissions": permissions,
                "editable": role != ROLE_ADMIN,
            }
        )
    return role_permissions


async def update_role_permissions(db: AsyncSession, role: str, permissions: list[str]) -> list[str]:
    normalized_role = normalize_role_code(role)
    if normalized_role not in ROLE_ORDER:
        raise bad_request("不支持该角色")
    if normalized_role == ROLE_ADMIN:
        raise bad_request("管理员角色权限固定，不能修改")
    valid_codes = _permission_code_set()
    invalid = [item for item in permissions if item not in valid_codes]
    if invalid:
        raise bad_request(f"包含无效权限: {', '.join(invalid)}")
    normalized = _normalize_permissions(permissions)
    result = await db.execute(select(RolePermission).where(RolePermission.role == normalized_role))
    row = result.scalar_one_or_none()
    permissions_json = json.dumps(normalized, ensure_ascii=False)
    if row is None:
        row = RolePermission(role=normalized_role, permissions_json=permissions_json)
        db.add(row)
    else:
        row.permissions_json = permissions_json
    await db.commit()
    return normalized


async def ensure_role_permission_defaults(db: AsyncSession) -> None:
    for role in (ROLE_EXPERT, ROLE_USER):
        result = await db.execute(select(RolePermission).where(RolePermission.role == role))
        row = result.scalar_one_or_none()
        if row is not None:
            continue
        db.add(
            RolePermission(
                role=role,
                permissions_json=json.dumps(default_permissions_for_role(role), ensure_ascii=False),
            )
        )
    await db.commit()
