"""Assistant routes — single bounded agent (§19, §22).

POST /assistant/chat        non-streaming turn (auth required)
POST /assistant/chat/stream SSE turn: provider/tool/delta/final/error
GET  /assistant/capabilities provider status + tool specs + UI actions
GET  /assistant/health      configured/enabled, no secrets
GET  /assistant/conversations list own conversations (newest first)
GET  /assistant/conversations/{id} own transcript slice
POST /assistant/feedback    rating + optional comment (auth required)

Persistence is best-effort: a turn never fails because the transcript
store did. Legacy /intel routes stay untouched (§20 compatibility).
"""

import json
import uuid
from datetime import datetime, timedelta, timezone

import structlog
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.dependencies import get_current_active_admin, get_current_user, get_db
from models import User
from schemas.assistant import (
    AssistantCapabilitiesResponse,
    AssistantChatRequest,
    AssistantChatResponse,
    AssistantCitationOut,
    AssistantConversationOut,
    AssistantFeedbackRequest,
    AssistantHealthResponse,
    AssistantMessageOut,
    AssistantUIActionOut,
)
from services.assistant import memory as assistant_memory
from services.assistant.service import assistant_service
from services.assistant.tools_registry import tool_registry
from services.assistant.ui_actions import ACTION_SPECS
from telemetry.assistant_metrics import FEEDBACK

router = APIRouter(prefix="/assistant", tags=["assistant"])
logger = structlog.get_logger(__name__)


_ALLOWED_PAGES = frozenset({
    "dashboard", "markets", "weather", "disease-detection",
    "schemes", "analytics", "maps", "ai-assistant",
})


def _page_context(body: AssistantChatRequest) -> dict:
    """Allow-listed page context only. Drops unknown routes, over-long
    values, and non-scalar filter entries (never secrets or DOM dumps)."""
    out: dict = {}
    route = (body.route or "")[:64]
    if route.startswith("/") and all(c.isalnum() or c in "-_/" for c in route):
        out["route"] = route
    if body.page in _ALLOWED_PAGES:
        out["page"] = body.page
    if isinstance(body.page_filters, dict):
        clean = {
            str(k)[:32]: v for k, v in list(body.page_filters.items())[:16]
            if isinstance(v, (str, int, float, bool)) and len(str(v)) <= 128
        }
        if clean:
            out["page_filters"] = clean
    return out


def _context(body: AssistantChatRequest, user: User) -> dict:
    ctx = {
        "user_id": str(user.id),
        "state": body.state,
        "commodity": body.commodity,
        "h3_index": body.h3_index,
    }
    ctx.update(_page_context(body))
    return ctx


def _citations(result: dict) -> list[AssistantCitationOut]:
    out = []
    for c in result.get("citations", []):
        c = c.model_dump() if hasattr(c, "model_dump") else c
        out.append(
            AssistantCitationOut(
                source=str(c.get("source", "")),
                title=str(c.get("title", "")),
                snippet=str(c.get("snippet", "")),
                score=c.get("score"),
            )
        )
    return out


def _actions(result: dict) -> list[AssistantUIActionOut]:
    out = []
    for a in result.get("ui_actions", []):
        a = a.model_dump() if hasattr(a, "model_dump") else a
        out.append(
            AssistantUIActionOut(
                action=str(a.get("action", "")),
                payload=dict(a.get("payload", {})),
            )
        )
    return out


async def _load_turn(
    db: AsyncSession, user: User, conversation_id: str | None, message: str
) -> tuple[uuid.UUID | None, list[dict[str, str]]]:
    """Resolve/create conversation + recent history. Never raises: on any
    persistence failure the turn proceeds stateless."""
    if not conversation_id:
        try:
            conv = await assistant_memory.get_or_create_conversation(
                db, user.id, None, title=message[:80]
            )
            return conv.id, []
        except Exception as e:
            logger.warning("assistant_conversation_create_failed", error=str(e))
            await db.rollback()
            return None, []
    try:
        cid = uuid.UUID(conversation_id)
    except ValueError:
        return None, []
    try:
        conv = await assistant_memory.get_or_create_conversation(
            db, user.id, cid, title=message[:80]
        )
        history = await assistant_memory.recent_history(db, conv.id)
        return conv.id, history
    except Exception as e:
        logger.warning("assistant_history_load_failed", error=str(e))
        await db.rollback()
        return None, []


async def _store_turn(
    db: AsyncSession,
    conversation_id: uuid.UUID | None,
    user_message: str,
    assistant_text: str,
    provider: str,
) -> None:
    if conversation_id is None:
        return
    try:
        now = datetime.now(timezone.utc)
        await assistant_memory.append_message(
            db, conversation_id, "user", user_message, created_at=now
        )
        await assistant_memory.append_message(
            db,
            conversation_id,
            "assistant",
            assistant_text,
            provider=provider,
            created_at=now + timedelta(microseconds=1),
        )
    except Exception as e:
        logger.warning("assistant_turn_store_failed", error=str(e))
        await db.rollback()


async def _owned_conversation(db: AsyncSession, user: User, conversation_id: str):
    try:
        cid = uuid.UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Conversation not found")
    try:
        conv = await db.get(assistant_memory.AssistantConversation, cid)
    except Exception as e:
        logger.warning("assistant_conversation_lookup_failed", error=str(e))
        raise HTTPException(status_code=503, detail="Conversation store unavailable")
    if conv is None or conv.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.post("/chat", response_model=AssistantChatResponse)
async def assistant_chat(
    body: AssistantChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conv_id, history = await _load_turn(db, user, body.conversation_id, body.message)
    result = await assistant_service.chat(
        body.message, _context(body, user), language=body.language, history=history
    )
    provider = result.get("provider") or {}
    await _store_turn(db, conv_id, body.message, result.get("text", ""),
                      provider.get("name", ""))
    return AssistantChatResponse(
        text=result.get("text", ""),
        conversation_id=str(conv_id) if conv_id else body.conversation_id,
        provider=provider.get("name"),
        citations=_citations(result),
        ui_actions=_actions(result),
        tool_events=result.get("tool_events", []),
    )


@router.post("/chat/stream")
async def assistant_chat_stream(
    body: AssistantChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ctx = _context(body, user)
    message = body.message
    conv_id, history = await _load_turn(db, user, body.conversation_id, message)
    lang = body.language

    async def events():
        assistant_text = ""
        async for item in assistant_service.stream(message, ctx, language=lang, history=history):
            if item["event"] == "final":
                item["data"]["conversation_id"] = str(conv_id) if conv_id else body.conversation_id
                assistant_text = item["data"].get("text", "")
            yield f"event: {item['event']}\ndata: {json.dumps(item['data'], default=str)}\n\n"
        await _store_turn(db, conv_id, message, assistant_text, "")

    return StreamingResponse(events(), media_type="text/event-stream")


@router.get("/conversations", response_model=list[AssistantConversationOut])
async def assistant_conversations(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rows = await assistant_memory.list_conversations(db, user.id)
    return [AssistantConversationOut(id=str(r.id), title=r.title or "") for r in rows]


@router.get("/conversations/{conversation_id}", response_model=list[AssistantMessageOut])
async def assistant_conversation_detail(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conv = await _owned_conversation(db, user, conversation_id)
    rows = await assistant_memory.list_messages(db, conv.id)
    return [
        AssistantMessageOut(role=r.role, content=r.content, provider=r.provider or "")
        for r in rows
    ]


@router.post("/feedback", status_code=204)
async def assistant_feedback(
    body: AssistantFeedbackRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    FEEDBACK.labels(rating=body.rating).inc()
    try:
        await assistant_memory.set_memory(
            db,
            subject=f"user:{user.id}",
            key=f"feedback:{body.message_id or 'general'}",
            value={"rating": body.rating, "comment": body.comment},
        )
    except Exception as e:
        logger.warning("assistant_feedback_store_failed", error=str(e))


@router.get("/capabilities", response_model=AssistantCapabilitiesResponse)
async def assistant_capabilities(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    del user
    caps = await assistant_service.capabilities()
    try:
        from sqlalchemy import func, select

        from models.scheme import GovernmentScheme

        total = await db.execute(
            select(func.count()).select_from(GovernmentScheme).where(
                GovernmentScheme.is_active == True
            )
        )
        caps["rag"]["document_count"] = total.scalar() or 0
    except Exception:
        pass
    return AssistantCapabilitiesResponse(
        enabled=settings.ASSISTANT_ENABLED,
        providers=caps["llm"]["providers"],
        tools=tool_registry.specs(),
        ui_actions=sorted(ACTION_SPECS),
        openrouter=_openrouter_tier_info(),
        languages=caps.get("languages", []),
        voice=caps.get("voice", {}),
        translation=caps.get("translation", {}),
    )


def _openrouter_tier_info() -> dict:
    """Safe tier configuration for capabilities. No keys, no usage."""
    from core.config import settings as _settings
    from services.assistant.openrouter_tiers import build_tiers

    if not _settings.OPENROUTER_API_KEY:
        return {"enabled": False, "tiering": False, "tiers": []}
    tiers = build_tiers()
    return {
        "enabled": True,
        "tiering": bool(_settings.ASSISTANT_OPENROUTER_TIERING_ENABLED),
        "tiers": [
            {
                "tier": t.tier,
                "model": t.model,
                "enabled": True,
                "tool_calling": t.tool_calling,
            }
            for t in tiers
        ],
        "fallback": "ollama",
    }


@router.get("/providers/usage")
async def assistant_provider_usage(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_active_admin),
):
    """Admin diagnostics: today's per-tier counters vs configured budgets.
    Counters only — no prompts, no keys. Farmer UI must not call this."""
    del admin
    from core.config import settings as _settings
    from services.assistant.openrouter_tiers import build_tiers, tier_manager

    tiers = {t.model: t for t in build_tiers()}
    rows = await tier_manager.snapshot(db)
    out = []
    for r in rows:
        t = tiers.get(r["model"])
        out.append(
            {
                **r,
                "configured_max_requests": t.max_requests if t else None,
                "configured_max_tokens": t.max_tokens if t else None,
                "status": (
                    "active"
                    if t
                    and r["requests"] < t.max_requests
                    and r["total_tokens"] < t.max_tokens
                    else "standby" if t else "unconfigured"
                ),
            }
        )
    return {
        "enabled": bool(_settings.OPENROUTER_API_KEY),
        "tiering": bool(_settings.ASSISTANT_OPENROUTER_TIERING_ENABLED),
        "ollama": {"model": _settings.ASSISTANT_LOCAL_MODEL},
        "tiers": out,
    }


@router.get("/health", response_model=AssistantHealthResponse)
async def assistant_health():
    from services.assistant.router import router as llm_router

    caps = await assistant_service.capabilities()
    model_ready, probe_ms = await llm_router.ollama_model_ready()
    return AssistantHealthResponse(
        enabled=settings.ASSISTANT_ENABLED,
        configured_providers=[
            p["name"] for p in caps["llm"]["providers"] if p.get("status") == "available"
        ],
        model_ready=model_ready,
        model_probe_ms=round(probe_ms, 1),
        model=settings.ASSISTANT_LOCAL_MODEL,
    )
