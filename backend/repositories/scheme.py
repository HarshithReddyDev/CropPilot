from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.scheme import GovernmentScheme
from repositories.base import BaseRepository


class SchemeRepository(BaseRepository):
    def __init__(self):
        super().__init__(GovernmentScheme)

    async def get_by_state(
        self, db: AsyncSession, state: str, skip: int = 0, limit: int = 50
    ):
        stmt = (
            select(GovernmentScheme)
            .where(
                GovernmentScheme.state_jurisdiction.ilike(f"%{state}%")
                | GovernmentScheme.state_jurisdiction.is_(None)
            )
            .where(GovernmentScheme.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_by_category(
        self, db: AsyncSession, category: str
    ):
        stmt = (
            select(GovernmentScheme)
            .where(GovernmentScheme.category == category)
            .where(GovernmentScheme.is_active == True)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def list_active(self, db: AsyncSession, limit: int = 50):
        """All active schemes regardless of jurisdiction. National
        fallback only: callers must mark the widened scope."""
        stmt = (
            select(GovernmentScheme)
            .where(GovernmentScheme.is_active == True)
            .order_by(GovernmentScheme.scheme_name.asc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()


scheme_repository = SchemeRepository()
