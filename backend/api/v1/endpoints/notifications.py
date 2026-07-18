from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_user, get_db
from models.notification import Notification
from models.user import User
from services.notification import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("")
async def list_notifications(
    unread_only: bool = Query(False),
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await notification_service.get_notifications(db, current_user.id, unread_only)


@router.post("/{notification_id}/read")
async def mark_as_read(
    notification_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await notification_service.mark_as_read(db, notification_id, current_user.id)


@router.post("/read-all")
async def mark_all_as_read(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await notification_service.mark_all_as_read(db, current_user.id)
    return {"message": "All notifications marked as read"}
