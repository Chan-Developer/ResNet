from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db, require_permissions
from ..schemas.common import ApiResponse
from ..schemas.user import (
    PermissionCatalogItem,
    RolePermissionInfo,
    RolePermissionUpdate,
    UserManageInfo,
    UserManageUpdate,
)
from ..services import admin_service, rbac_service

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users", response_model=ApiResponse[list[UserManageInfo]])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permissions("admin:user")),
):
    users = await admin_service.list_users(db)
    result: list[UserManageInfo] = []
    for user in users:
        normalized_role = rbac_service.normalize_role_code(user.role)
        permissions = await rbac_service.get_role_permissions(db, normalized_role)
        result.append(
            UserManageInfo(
                id=user.id,
                username=user.username,
                email=user.email,
                role=normalized_role,
                is_active=user.is_active,
                permissions=permissions,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
        )
    return ApiResponse(data=result)


@router.patch("/users/{user_id}", response_model=ApiResponse[UserManageInfo])
async def update_user(
    user_id: int,
    payload: UserManageUpdate,
    db: AsyncSession = Depends(get_db),
    operator=Depends(require_permissions("admin:user")),
):
    user = await admin_service.update_user_permissions(
        db,
        target_user_id=user_id,
        operator_user_id=operator.id,
        payload=payload,
    )
    normalized_role = rbac_service.normalize_role_code(user.role)
    permissions = await rbac_service.get_role_permissions(db, normalized_role)
    return ApiResponse(
        data=UserManageInfo(
            id=user.id,
            username=user.username,
            email=user.email,
            role=normalized_role,
            is_active=user.is_active,
            permissions=permissions,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
    )


@router.get("/permissions", response_model=ApiResponse[list[PermissionCatalogItem]])
async def list_permissions(
    _=Depends(require_permissions("admin:role")),
):
    return ApiResponse(data=[PermissionCatalogItem(**item) for item in rbac_service.list_permission_catalog()])


@router.get("/roles", response_model=ApiResponse[list[RolePermissionInfo]])
async def list_roles(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permissions("admin:role")),
):
    roles = await rbac_service.list_role_permission_entries(db)
    return ApiResponse(data=[RolePermissionInfo(**item) for item in roles])


@router.patch("/roles/{role}/permissions", response_model=ApiResponse[RolePermissionInfo])
async def update_role_permissions(
    role: str,
    payload: RolePermissionUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permissions("admin:role")),
):
    permissions = await rbac_service.update_role_permissions(db, role, payload.permissions)
    role_labels = rbac_service.list_role_labels()
    return ApiResponse(
        data=RolePermissionInfo(
            role=role,
            label=role_labels.get(role, role),
            permissions=permissions,
            editable=role != "admin",
        )
    )
