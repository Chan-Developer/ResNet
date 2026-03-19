from datetime import date, datetime

from sqlalchemy import JSON, BigInteger, Date, DateTime, Float, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .user import Base


ID_TYPE = BigInteger().with_variant(Integer, "sqlite")

PLAN_STATUS_ACTIVE = "active"
PLAN_STATUS_PAUSED = "paused"
PLAN_STATUS_COMPLETED = "completed"
PLAN_STATUS_CANCELLED = "cancelled"

EFFECT_STATUS_IMPROVED = "improved"
EFFECT_STATUS_STABLE = "stable"
EFFECT_STATUS_WORSE = "worse"
EFFECT_STATUS_UNKNOWN = "unknown"


class FollowUpPlan(Base):
    __tablename__ = "followup_plan"
    __table_args__ = (
        Index("idx_followup_plan_user_status_next", "user_id", "status", "next_review_date"),
        Index("idx_followup_plan_case", "case_id"),
    )

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ID_TYPE, nullable=False, index=True)
    case_id: Mapped[int | None] = mapped_column(ID_TYPE, nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    target_label: Mapped[str] = mapped_column(String(200), nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    frequency_days: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    next_review_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=PLAN_STATUS_ACTIVE)
    latest_effect: Mapped[str] = mapped_column(
        String(20), nullable=False, default=EFFECT_STATUS_UNKNOWN
    )
    effect_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class FollowUpCheckin(Base):
    __tablename__ = "followup_checkin"
    __table_args__ = (
        Index("idx_followup_checkin_plan_created", "plan_id", "created_at"),
        Index("idx_followup_checkin_user_created", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    plan_id: Mapped[int] = mapped_column(ID_TYPE, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ID_TYPE, nullable=False, index=True)
    image_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    top1_label: Mapped[str] = mapped_column(String(200), nullable=False)
    top1_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    target_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    target_confidence_delta: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    top1_confidence_delta: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    effect_status: Mapped[str] = mapped_column(String(20), nullable=False, default=EFFECT_STATUS_UNKNOWN)
    effect_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    llm_summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    note: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    results_json: Mapped[list] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
