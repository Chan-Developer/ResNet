from datetime import datetime

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .user import Base


ID_TYPE = BigInteger().with_variant(Integer, "sqlite")


class ModelVersion(Base):
    __tablename__ = "model_version"

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    version_code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(String(500), default="")
    model_path: Mapped[str] = mapped_column(String(500), nullable=False)
    class_names_path: Mapped[str] = mapped_column(String(500), default="")
    metrics_json: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
