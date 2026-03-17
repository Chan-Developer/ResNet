import math

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.prediction import PredictionRecord
from ..schemas.common import PageData
from ..schemas.prediction import HistoryOut


async def create_record(
    db: AsyncSession,
    *,
    user_id: int,
    image_filename: str,
    image_url: str,
    top1_class: str,
    top1_confidence: float,
    top_k: int,
    results_json: dict,
) -> PredictionRecord:
    record = PredictionRecord(
        user_id=user_id,
        image_filename=image_filename,
        image_url=image_url,
        top1_class=top1_class,
        top1_confidence=top1_confidence,
        top_k=top_k,
        results_json=results_json,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def get_history(
    db: AsyncSession, user_id: int, page: int = 1, size: int = 20
) -> PageData[HistoryOut]:
    total_result = await db.execute(
        select(func.count()).select_from(PredictionRecord).where(PredictionRecord.user_id == user_id)
    )
    total = total_result.scalar() or 0
    pages = math.ceil(total / size) if total > 0 else 0

    result = await db.execute(
        select(PredictionRecord)
        .where(PredictionRecord.user_id == user_id)
        .order_by(PredictionRecord.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    records = result.scalars().all()
    items = [HistoryOut.model_validate(r) for r in records]

    return PageData(items=items, total=total, page=page, size=size, pages=pages)


async def delete_record(db: AsyncSession, record_id: int, user_id: int) -> bool:
    result = await db.execute(
        delete(PredictionRecord).where(
            PredictionRecord.id == record_id, PredictionRecord.user_id == user_id
        )
    )
    await db.commit()
    return result.rowcount > 0
