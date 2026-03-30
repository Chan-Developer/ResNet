from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db, require_permissions
from ..schemas.admin_manage import (
    KnowledgeChunkCreate,
    KnowledgeChunkManageInfo,
    KnowledgeChunkUpdate,
    ModelRuntimeInfo,
    ModelVersionCreate,
    ModelVersionInfo,
    ModelVersionUpdate,
)
from ..schemas.common import ApiResponse
from ..schemas.user import (
    PermissionCatalogItem,
    RolePermissionInfo,
    RolePermissionUpdate,
    UserManageInfo,
    UserManageUpdate,
)
from ..services import admin_service, knowledge_service, model_registry_service, rbac_service

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


@router.get("/knowledge", response_model=ApiResponse[list[KnowledgeChunkManageInfo]])
async def list_knowledge_chunks(
    keyword: str | None = Query(default=None),
    label_key: str | None = Query(default=None),
    crop_name: str | None = Query(default=None),
    disease_family: str | None = Query(default=None),
    health_status: str | None = Query(default=None),
    limit: int = Query(default=300, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permissions("admin:knowledge")),
):
    chunks = await knowledge_service.list_knowledge_chunks(
        db,
        keyword=keyword,
        label_key=label_key,
        crop_name=crop_name,
        disease_family=disease_family,
        health_status=health_status,
        limit=limit,
    )
    return ApiResponse(data=[KnowledgeChunkManageInfo(**item) for item in chunks])


@router.post("/knowledge", response_model=ApiResponse[KnowledgeChunkManageInfo])
async def create_knowledge_chunk(
    payload: KnowledgeChunkCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permissions("admin:knowledge")),
):
    item = await knowledge_service.create_knowledge_chunk(db, payload)
    return ApiResponse(data=KnowledgeChunkManageInfo(**item))


@router.patch("/knowledge/{chunk_id}", response_model=ApiResponse[KnowledgeChunkManageInfo])
async def update_knowledge_chunk(
    chunk_id: int,
    payload: KnowledgeChunkUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permissions("admin:knowledge")),
):
    item = await knowledge_service.update_knowledge_chunk(db, chunk_id, payload)
    return ApiResponse(data=KnowledgeChunkManageInfo(**item))


@router.delete("/knowledge/{chunk_id}", response_model=ApiResponse[dict[str, bool]])
async def delete_knowledge_chunk(
    chunk_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permissions("admin:knowledge")),
):
    await knowledge_service.delete_knowledge_chunk(db, chunk_id)
    return ApiResponse(data={"deleted": True})


@router.get("/model-versions", response_model=ApiResponse[list[ModelVersionInfo]])
async def list_model_versions(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permissions("admin:model")),
):
    versions = await model_registry_service.list_model_versions(db)
    return ApiResponse(data=[ModelVersionInfo(**item) for item in versions])


@router.post("/model-versions", response_model=ApiResponse[ModelVersionInfo])
async def create_model_version(
    payload: ModelVersionCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permissions("admin:model")),
):
    item = await model_registry_service.create_model_version(db, payload)
    return ApiResponse(data=ModelVersionInfo(**item))


@router.patch("/model-versions/{version_id}", response_model=ApiResponse[ModelVersionInfo])
async def update_model_version(
    version_id: int,
    payload: ModelVersionUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permissions("admin:model")),
):
    item = await model_registry_service.update_model_version(db, version_id, payload)
    return ApiResponse(data=ModelVersionInfo(**item))


@router.delete("/model-versions/{version_id}", response_model=ApiResponse[dict[str, bool]])
async def delete_model_version(
    version_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permissions("admin:model")),
):
    await model_registry_service.delete_model_version(db, version_id)
    return ApiResponse(data={"deleted": True})


@router.post("/model-versions/{version_id}/activate", response_model=ApiResponse[ModelVersionInfo])
async def activate_model_version(
    version_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permissions("admin:model")),
):
    item = await model_registry_service.activate_model_version(db, version_id)
    return ApiResponse(data=ModelVersionInfo(**item))


@router.get("/model-versions/runtime", response_model=ApiResponse[ModelRuntimeInfo])
async def get_model_runtime_info(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permissions("admin:model")),
):
    runtime = await model_registry_service.get_model_runtime_info(db)
    return ApiResponse(data=ModelRuntimeInfo(**runtime))
