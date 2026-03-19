from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from .database import AsyncSessionLocal
from .models.user import ROLE_ADMIN
from .services import rbac_service
from .services.auth_service import get_user_by_id
from .utils.errors import forbidden, unauthorized
from .services.model_service import model_service as _model_service
from .utils.security import decode_access_token

bearer_scheme = HTTPBearer()


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise unauthorized("无效的令牌")
    user_id = payload.get("sub")
    if user_id is None:
        raise unauthorized("无效的令牌")
    user = await get_user_by_id(db, int(user_id))
    if user is None:
        raise unauthorized("用户不存在")
    if not user.is_active:
        raise forbidden("账号已被停用")
    return user


async def get_current_admin(user=Depends(get_current_user)):
    if rbac_service.normalize_role_code(user.role) != ROLE_ADMIN:
        raise forbidden("需要管理员权限")
    return user


async def get_current_user_permissions(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await rbac_service.get_role_permissions(db, user.role)


def require_permissions(*required_permissions: str):
    async def _checker(
        user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        user_permissions = await rbac_service.get_role_permissions(db, user.role)
        missing = [perm for perm in required_permissions if perm not in user_permissions]
        if missing:
            raise forbidden("当前角色无操作权限")
        return user

    return _checker


def get_model_service():
    return _model_service
