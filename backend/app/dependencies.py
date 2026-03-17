from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from .database import AsyncSessionLocal
from .services.auth_service import get_user_by_id
from .utils.errors import unauthorized
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
    return user


def get_model_service():
    return _model_service
