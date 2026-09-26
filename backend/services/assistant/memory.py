"""Assistant memory: conversation transcript + generic key/value recall.

Transcript rows are append-only. Memory reads return the latest value per
key for a subject; writes upsert. Failures never break a chat turn: the
endpoint treats persistence as best-effort and logs.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.assistant import AssistantConversation, AssistantMemory, AssistantMessage

logger = structlog.get_logger(__name__)

HISTORY_TURNS = 6


async def get_or_create_conversation(
    db: AsyncSession,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID | None,
    title: str = "",
) -> AssistantConversation:
    if conversation_id is not None:
        try:
            row = await db.get(AssistantConversation, conversation_id)
        except Exception:
            row = None  # malformed id can never match; mint fresh below
        if row is not None and row.user_id == user_id:
            return row
    conv = AssistantConversation(user_id=user_id, title=title[:255])
    db.add(conv)
    await db.flush()
    return conv


async def append_message(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    role: str,
    content: str,
    provider: str = "",
    extra: dict[str, Any] | None = None,
    created_at: datetime | None = None,
) -> AssistantMessage:
    row = AssistantMessage(
        conversation_id=conversation_id,
        role=role,
        content=content,
        provider=provider,
        extra=extra or {},
    )
    if created_at is not None:
        # Explicit stamp beats server_default now(): same-transaction rows
        # would otherwise tie and lose their order.
        row.created_at = created_at
    db.add(row)
    conv = await db.get(AssistantConversation, conversation_id)
    if conv is not None:
        conv.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return row


async def recent_history(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    turns: int = HISTORY_TURNS,
) -> list[dict[str, str]]:
    """Last N user/assistant turns as {role, content}, oldest first."""
    stmt = (
        select(AssistantMessage)
        .where(AssistantMessage.conversation_id == conversation_id)
        .where(AssistantMessage.role.in_(("user", "assistant")))
        .order_by(desc(AssistantMessage.created_at))
        .limit(turns * 2)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [
        {"role": r.role, "content": r.content} for r in reversed(rows)
    ]


async def list_messages(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    limit: int = 100,
) -> list[AssistantMessage]:
    """Full transcript slice, oldest first."""
    stmt = (
        select(AssistantMessage)
        .where(AssistantMessage.conversation_id == conversation_id)
        .order_by(AssistantMessage.created_at)
        .limit(limit)
    )
    return list((await db.execute(stmt)).scalars().all())


async def list_conversations(
    db: AsyncSession, user_id: uuid.UUID, limit: int = 20
) -> list[AssistantConversation]:
    stmt = (
        select(AssistantConversation)
        .where(AssistantConversation.user_id == user_id)
        .order_by(desc(AssistantConversation.updated_at))
        .limit(limit)
    )
    return list((await db.execute(stmt)).scalars().all())


async def set_memory(
    db: AsyncSession,
    subject: str,
    key: str,
    value: dict[str, Any],
    effective_to: datetime | None = None,
) -> AssistantMemory:
    stmt = (
        select(AssistantMemory)
        .where(AssistantMemory.subject == subject)
        .where(AssistantMemory.key == key)
        .order_by(desc(AssistantMemory.created_at))
        .limit(1)
    )
    row = (await db.execute(stmt)).scalars().first()
    now = datetime.now(timezone.utc)
    if row is None:
        row = AssistantMemory(
            subject=subject, key=key, value=value,
            effective_from=now, effective_to=effective_to,
        )
        db.add(row)
    else:
        row.value = value
        row.effective_from = now
        row.effective_to = effective_to
    await db.flush()
    return row


async def get_memory(db: AsyncSession, subject: str, key: str) -> dict[str, Any] | None:
    stmt = (
        select(AssistantMemory)
        .where(AssistantMemory.subject == subject)
        .where(AssistantMemory.key == key)
        .order_by(desc(AssistantMemory.created_at))
        .limit(1)
    )
    row = (await db.execute(stmt)).scalars().first()
    return dict(row.value) if row is not None else None
