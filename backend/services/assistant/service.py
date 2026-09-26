"""Assistant service: endpoint -> service -> agent/tools boundary.

No business logic in route handlers. Persistence hooks (conversations,
messages, tool/UI events) attach in Phase 7; until then turns run
stateless with the caller-supplied context.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any
from uuid import uuid4

import structlog
from opentelemetry import trace

from core.config import settings
from services.assistant.agent import run_agent
from services.assistant.providers import ProviderError
from services.assistant.router import router
from services.assistant.tools_definitions import assistant_tools  # noqa: F401 - registration side effect
from services.assistant.types import ProviderHealth
from services.assistant.ui_actions import validate_ui_actions

logger = structlog.get_logger(__name__)
tracer = trace.get_tracer(__name__)


class AssistantService:
    async def chat(
        self,
        message: str,
        context: dict[str, Any],
        language: str = "en",
        history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        from telemetry.assistant_metrics import CHAT_TOTAL

        if not settings.ASSISTANT_ENABLED:
            CHAT_TOTAL.labels(provider="none", status="disabled").inc()
            return self._unavailable("The assistant is disabled by configuration.")
        # Deterministic commands never need the LLM: compute first so they
        # fire even when every provider is down (e.g. language switch).
        from services.assistant.commands import command_actions

        commanded = [
            a.model_dump() for a in validate_ui_actions(command_actions(message))
        ]
        with tracer.start_as_current_span("assistant.request"):
            try:
                result = await run_agent(message, context, language=language, history=history)
            except ProviderError as e:
                logger.warning("assistant_request_failed", error=str(e))
                CHAT_TOTAL.labels(provider="none", status="failed").inc()
                fallback = self._unavailable(str(e))
                fallback["ui_actions"] = commanded
                return fallback
            CHAT_TOTAL.labels(
                provider=(result.get("provider") or {}).get("name", "unknown"),
                status="succeeded",
            ).inc()
            actions = [a.model_dump() for a in validate_ui_actions(
                [x.model_dump() if hasattr(x, "model_dump") else x for x in result["ui_actions"]]
            )]
            # Deterministic commands (language switch, open page) ride
            # alongside the LLM answer; validation keeps them allow-listed.
            actions.extend(commanded)
            return {
                "message_id": str(uuid4()),
                "text": result["text"],
                "language": language,
                "citations": [c.model_dump() if hasattr(c, "model_dump") else c for c in result["citations"]],
                "tool_events": [e.model_dump() for e in result["tool_events"]],
                "ui_actions": actions,
                "provider": result["provider"],
                "voice": {"available": False, "language": language},
            }

    async def stream(
        self,
        message: str,
        context: dict[str, Any],
        language: str = "en",
        history: list[dict[str, str]] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Agentic turn with streamed final text. Tool steps run first,
        then the final answer streams token-by-token."""
        if not settings.ASSISTANT_ENABLED:
            yield {"event": "error", "data": "The assistant is disabled by configuration."}
            return
        # Phase 1: run the bounded turn, then stream its text as deltas.
        # True token streaming through the tool loop lands with Phase 5.
        try:
            result = await run_agent(message, context, language=language, history=history)
        except ProviderError as e:
            yield {"event": "error", "data": str(e)}
            return
        yield {"event": "provider", "data": result["provider"]}
        for event in result["tool_events"]:
            yield {"event": "tool", "data": event.model_dump()}
        text = result["text"] or ""
        for i in range(0, len(text), 120):
            yield {"event": "delta", "data": text[i : i + 120]}
        yield {
            "event": "final",
            "data": {
                "message_id": str(uuid4()),
                "text": text,
                "language": language,
                "citations": result["citations"],
                "ui_actions": [a.model_dump() for a in validate_ui_actions(
                    [x.model_dump() if hasattr(x, "model_dump") else x for x in result["ui_actions"]]
                )],
                "provider": result["provider"],
            },
        }

    async def capabilities(self) -> dict[str, Any]:
        providers: list[ProviderHealth] = await router.provider_status()
        from services.assistant.languages import language_matrix
        from services.assistant.voice import load_asr, load_tts

        asr, tts = load_asr(), load_tts()
        from services.assistant.translation import translation_manager

        asr_state, tts_state = asr.readiness(), tts.readiness()
        mt_state = translation_manager.readiness()
        return {
            "llm": {
                "order": router.order,
                "providers": [p.model_dump() for p in providers],
            },
            "languages": language_matrix(),
            "voice": {
                "enabled": settings.ASSISTANT_VOICE_ENABLED,
                "asr_engine": asr.name,
                "asr_available": asr_state["available"],
                "asr_ready": asr_state["ready"],
                "asr_languages": asr_state["languages"],
                "asr_model": asr_state.get("model", ""),
                "tts_engine": tts.name,
                "tts_available": tts_state["available"],
                "tts_ready": tts_state["ready"],
                "tts_languages": tts_state["languages"],
                "tts_model": tts_state.get("model", ""),
                "auto_speak": settings.ASSISTANT_AUTO_SPEAK,
                "persist_audio": settings.ASSISTANT_PERSIST_AUDIO,
            },
            "translation": {
                "engine": "indictrans2",
                "ready": mt_state["ready"],
                "directions": mt_state["directions"],
            },
            "rag": {
                "enabled": settings.ASSISTANT_RAG_ENABLED,
                "embedding_model": settings.ASSISTANT_EMBEDDING_MODEL,
                "dimensions": 1024,
                "vector_store": "postgresql+pgvector",
                "document_count": 0,
            },
            "ui": {"actions": [], "action_count": 0},
            "limits": {"max_tool_steps": min(settings.ASSISTANT_MAX_TOOL_STEPS, 10)},
        }

    @staticmethod
    def _unavailable(detail: str) -> dict[str, Any]:
        return {
            "message_id": str(uuid4()),
            "text": detail,
            "language": "en",
            "citations": [],
            "tool_events": [],
            "ui_actions": [],
            "provider": {"name": "none", "model": ""},
            "voice": {"available": False, "language": "en"},
        }


assistant_service = AssistantService()
