from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, Float, Index, Integer, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .user import Base


ID_TYPE = BigInteger().with_variant(Integer, "sqlite")


class PredictionRecord(Base):
    __tablename__ = "prediction_record"
    __table_args__ = (Index("idx_user_created", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ID_TYPE, nullable=False, index=True)
    image_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    top1_class: Mapped[str] = mapped_column(String(200), nullable=False)
    top1_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    top_k: Mapped[int] = mapped_column(SmallInteger, default=5)
    results_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
