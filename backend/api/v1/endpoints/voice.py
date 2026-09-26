"""WebSocket voice endpoint: /ws/voice?lang=te&token=..."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query, WebSocket

from core.config import settings
from core.dependencies import DEV_USER_ID
from core.security import decode_token

router = APIRouter()


async def _ws_user(token: str | None):
    if not token:
        if settings.dev_auth_bypass_active:
            return _DevUser()
        return None
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            return None
        from db.session import async_session_factory
        from repositories.user import user_repository

        async with async_session_factory() as db:
            user = await user_repository.get_by_id(db, UUID(user_id))
            return user if user is not None and user.is_active else None
    except Exception:
        return None


class _DevUser:
    id = DEV_USER_ID
    role = "farmer"


@router.websocket("/ws/voice")
async def voice_socket(
    websocket: WebSocket,
    lang: str = Query(default="te"),
    token: str | None = Query(default=None),
):
    from services.assistant.voice import run_session

    user = await _ws_user(token)
    if user is None:
        await websocket.close(code=4401)
        return
    await run_session(websocket, user, default_lang=lang)
