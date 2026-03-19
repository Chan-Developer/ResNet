from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import ROLE_ADMIN, User
from ..services import rbac_service
from ..schemas.user import UserManageUpdate
from ..utils.errors import bad_request, not_found


async def list_users(db: AsyncSession) -> list[User]:
    result = await db.execute(select(User).order_by(User.created_at.desc(), User.id.desc()))
    return list(result.scalars().all())


async def count_active_admins(db: AsyncSession) -> int:
    return int(
        await db.scalar(
            select(func.count())
            .select_from(User)
            .where(func.lower(User.role) == ROLE_ADMIN, User.is_active.is_(True))
        )
        or 0
    )


async def update_user_permissions(
    db: AsyncSession,
    *,
    target_user_id: int,
    operator_user_id: int,
    payload: UserManageUpdate,
) -> User:
    user = await db.get(User, target_user_id)
    if user is None:
        raise not_found("用户不存在")

    if payload.role is None and payload.is_active is None:
        raise bad_request("至少需要更新一个字段")

    change_role = payload.role is not None and payload.role != user.role
    change_active = payload.is_active is not None and payload.is_active != user.is_active
    if not change_role and not change_active:
        return user

    if user.id == operator_user_id and (change_role or change_active):
        raise bad_request("不能修改自己的角色或停用自己的账号")

    current_role = rbac_service.normalize_role_code(user.role)
    next_role = rbac_service.normalize_role_code(payload.role) if payload.role is not None else current_role

    removing_admin = current_role == ROLE_ADMIN and (
        next_role != ROLE_ADMIN
        or payload.is_active is False
    )
    if (
        removing_admin and user.is_active and await count_active_admins(db) <= 1
    ):
        raise bad_request("系统至少需要保留一个启用中的管理员")

    if change_role and payload.role is not None:
        user.role = rbac_service.normalize_role_code(payload.role)
    if change_active and payload.is_active is not None:
        user.is_active = payload.is_active

    await db.commit()
    await db.refresh(user)
    return user
