from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.disease import DiseaseLog
from repositories.base import BaseRepository


class DiseaseRepository(BaseRepository):
    def __init__(self):
        super().__init__(DiseaseLog)

    async def get_with_detections(
        self, db: AsyncSession, disease_log_id: UUID
    ) -> DiseaseLog | None:
        stmt = (
            select(DiseaseLog)
            .where(DiseaseLog.id == disease_log_id)
            .options(selectinload(DiseaseLog.detections_rel))
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_plot(
        self, db: AsyncSession, plot_id: UUID, skip: int = 0, limit: int = 50
    ):
        stmt = (
            select(DiseaseLog)
            .where(DiseaseLog.plot_id == plot_id)
            .order_by(DiseaseLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_by_h3_index(
        self, db: AsyncSession, h3_index: str, days_back: int = 7
    ):
        from datetime import datetime, timedelta, timezone
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
        stmt = (
            select(DiseaseLog)
            .where(DiseaseLog.h3_spatial_index == h3_index)
            .where(DiseaseLog.created_at >= cutoff)
            .order_by(DiseaseLog.created_at.desc())
        )
        result = await db.execute(stmt)
        return result.scalars().all()


disease_repository = DiseaseRepository()
