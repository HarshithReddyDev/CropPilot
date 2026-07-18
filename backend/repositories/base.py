from uuid import UUID

from sqlalchemy import select, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    def __init__(self, model):
        self.model = model

    async def create(self, db: AsyncSession, **kwargs):
        instance = self.model(**kwargs)
        db.add(instance)
        await db.flush()
        return instance

    async def get_by_id(self, db: AsyncSession, id: UUID):
        stmt = select(self.model).where(self.model.id == id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self, db: AsyncSession, skip: int = 0, limit: int = 100, **filters
    ):
        stmt = select(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key) and value is not None:
                stmt = stmt.where(getattr(self.model, key) == value)
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def update(self, db: AsyncSession, id: UUID, **kwargs):
        instance = await self.get_by_id(db, id)
        if instance is None:
            return None
        for key, value in kwargs.items():
            if value is not None and hasattr(instance, key):
                setattr(instance, key, value)
        await db.flush()
        return instance

    async def delete(self, db: AsyncSession, id: UUID) -> bool:
        stmt = sa_delete(self.model).where(self.model.id == id)
        result = await db.execute(stmt)
        return result.rowcount > 0

    async def count(self, db: AsyncSession, **filters) -> int:
        from sqlalchemy.functions import func
        stmt = select(func.count()).select_from(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key) and value is not None:
                stmt = stmt.where(getattr(self.model, key) == value)
        result = await db.execute(stmt)
        return result.scalar()
