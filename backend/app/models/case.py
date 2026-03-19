from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, Float, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .user import Base


ID_TYPE = BigInteger().with_variant(Integer, "sqlite")


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunk"
    __table_args__ = (
        Index("idx_knowledge_label", "label_key"),
        Index("idx_knowledge_crop", "crop_name"),
        Index("idx_knowledge_family", "disease_family"),
    )

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    label_key: Mapped[str | None] = mapped_column(String(200), nullable=True)
    crop_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    disease_family: Mapped[str | None] = mapped_column(String(100), nullable=True)
    health_status: Mapped[str] = mapped_column(String(20), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), default="internal")
    source_name: Mapped[str] = mapped_column(String(120), default="PlantCare 知识库")
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(String(500), default="")
    tags_json: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class DiseaseCase(Base):
    __tablename__ = "disease_case"
    __table_args__ = (
        Index("idx_case_user_created", "user_id", "created_at"),
        Index("idx_case_label_created", "confirmed_label", "created_at"),
        Index("idx_case_region_label_created", "region_code", "confirmed_label", "created_at"),
    )

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ID_TYPE, nullable=False, index=True)
    prediction_record_id: Mapped[int] = mapped_column(ID_TYPE, nullable=False, index=True)
    image_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    predicted_label: Mapped[str] = mapped_column(String(200), nullable=False)
    confirmed_label: Mapped[str] = mapped_column(String(200), nullable=False)
    crop_name: Mapped[str] = mapped_column(String(100), nullable=False)
    disease_name: Mapped[str] = mapped_column(String(200), nullable=False)
    health_status: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="confirmed")
    province: Mapped[str | None] = mapped_column(String(50), nullable=True)
    city: Mapped[str | None] = mapped_column(String(50), nullable=True)
    district: Mapped[str | None] = mapped_column(String(50), nullable=True)
    region_code: Mapped[str] = mapped_column(String(120), default="未知区域", nullable=False)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    diagnostic_summary: Mapped[str] = mapped_column(String(500), nullable=False)
    advice_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    evidence_json: Mapped[list] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class RegionAlert(Base):
    __tablename__ = "region_alert"
    __table_args__ = (
        Index("idx_alert_region_label_created", "region_code", "confirmed_label", "created_at"),
        Index("idx_alert_status_created", "status", "created_at"),
    )

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    region_code: Mapped[str] = mapped_column(String(120), nullable=False)
    province: Mapped[str | None] = mapped_column(String(50), nullable=True)
    city: Mapped[str | None] = mapped_column(String(50), nullable=True)
    district: Mapped[str | None] = mapped_column(String(50), nullable=True)
    confirmed_label: Mapped[str] = mapped_column(String(200), nullable=False)
    current_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    previous_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    growth_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    window_days: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="unread")
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
