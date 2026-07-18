from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.notification import notification_repository


class NotificationService:
    async def create_notification(
        self,
        db: AsyncSession,
        user_id: UUID,
        title: str,
        body: str,
        notification_type: str = "info",
        channel: str = "in_app",
        reference_type: str | None = None,
        reference_id: UUID | None = None,
    ):
        return await notification_repository.create(
            db,
            user_id=user_id,
            title=title,
            body=body,
            notification_type=notification_type,
            channel=channel,
            reference_type=reference_type,
            reference_id=reference_id,
        )

    async def get_notifications(
        self, db: AsyncSession, user_id: UUID, unread_only: bool = False
    ):
        if unread_only:
            return await notification_repository.get_unread_by_user(db, user_id)
        return await notification_repository.get_all(db, user_id=user_id)

    async def mark_as_read(
        self, db: AsyncSession, notification_id: UUID, user_id: UUID
    ):
        notification = await notification_repository.mark_as_read(db, notification_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
            )
        return notification

    async def mark_all_as_read(self, db: AsyncSession, user_id: UUID):
        await notification_repository.mark_all_as_read(db, user_id)
