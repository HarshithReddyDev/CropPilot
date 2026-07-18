from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.farm import Farm
from repositories.base import BaseRepository


class FarmRepository(BaseRepository):
    def __init__(self):
        super().__init__(Farm)

    async def get_farms_by_farmer(
        self, db: AsyncSession, farmer_id: UUID, skip: int = 0, limit: int = 100
    ):
        stmt = (
            select(Farm)
            .where(Farm.farmer_id == farmer_id)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()


farm_repository = FarmRepository()
