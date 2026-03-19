from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_user, get_db
from ..schemas.common import ApiResponse
from ..schemas.user import TokenOut, UserCreate, UserInfo, UserLogin
from ..services import auth_service, rbac_service
from ..utils.security import create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=ApiResponse[UserInfo])
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    if await auth_service.get_user_by_username(db, data.username):
        raise HTTPException(status_code=400, detail="用户名已存在")
    if await auth_service.get_user_by_email(db, data.email):
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    try:
        user = await auth_service.create_user(db, data)
    except IntegrityError:
        if await auth_service.get_user_by_username(db, data.username):
            raise HTTPException(status_code=400, detail="用户名已存在")
        if await auth_service.get_user_by_email(db, data.email):
            raise HTTPException(status_code=400, detail="邮箱已被注册")
        raise HTTPException(status_code=400, detail="注册失败，请重试")
    permissions = await rbac_service.get_role_permissions(db, user.role)
    return ApiResponse(
        data=UserInfo(
            id=user.id,
            username=user.username,
            email=user.email,
            role=rbac_service.normalize_role_code(user.role),
            is_active=user.is_active,
            permissions=permissions,
            created_at=user.created_at,
        )
    )


@router.post("/login", response_model=ApiResponse[TokenOut])
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await auth_service.authenticate_user(db, data.username, data.password)
    if user is None:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return ApiResponse(data=TokenOut(access_token=token))


@router.get("/me", response_model=ApiResponse[UserInfo])
async def me(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    permissions = await rbac_service.get_role_permissions(db, user.role)
    return ApiResponse(
        data=UserInfo(
            id=user.id,
            username=user.username,
            email=user.email,
            role=rbac_service.normalize_role_code(user.role),
            is_active=user.is_active,
            permissions=permissions,
            created_at=user.created_at,
        )
    )
