from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field

UserRole = Literal["admin", "expert", "user"]


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserInfo(BaseModel):
    id: int
    username: str
    email: str
    role: UserRole
    is_active: bool
    permissions: list[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserManageUpdate(BaseModel):
    role: UserRole | None = None
    is_active: bool | None = None


class UserManageInfo(UserInfo):
    updated_at: Optional[datetime] = None


class PermissionCatalogItem(BaseModel):
    code: str
    name: str
    description: str


class RolePermissionInfo(BaseModel):
    role: UserRole
    label: str
    permissions: list[str]
    editable: bool = True


class RolePermissionUpdate(BaseModel):
    permissions: list[str]
