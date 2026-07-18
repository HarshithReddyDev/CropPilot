from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.notification import Notification
from repositories.base import BaseRepository


class NotificationRepository(BaseRepository):
    def __init__(self):
        super().__init__(Notification)

    async def get_unread_by_user(
        self, db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 50
    ):
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)
            .order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def mark_as_read(
        self, db: AsyncSession, notification_id: UUID
    ) -> Notification | None:
        from datetime import datetime, timezone
        stmt = (
            update(Notification)
            .where(Notification.id == notification_id)
            .values(is_read=True, read_at=datetime.now(timezone.utc))
        )
        await db.execute(stmt)
        return await self.get_by_id(db, notification_id)

    async def mark_all_as_read(self, db: AsyncSession, user_id: UUID):
        from datetime import datetime, timezone
        stmt = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read == False,
            )
            .values(is_read=True, read_at=datetime.now(timezone.utc))
        )
        await db.execute(stmt)


notification_repository = NotificationRepository()
