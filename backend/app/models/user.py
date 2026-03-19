from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


ID_TYPE = BigInteger().with_variant(Integer, "sqlite")
ROLE_ADMIN = "admin"
ROLE_EXPERT = "expert"
ROLE_USER = "user"


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    role: Mapped[str] = mapped_column(String(20), default=ROLE_USER, server_default=ROLE_USER)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class RolePermission(Base):
    __tablename__ = "role_permission"

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    role: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    permissions_json: Mapped[str] = mapped_column(String(2000), default="[]", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
