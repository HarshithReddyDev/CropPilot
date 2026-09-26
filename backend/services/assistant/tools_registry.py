"""Typed tool registry. The model only ever sees registered tools.

Every tool declares: name, description, Pydantic input/output schemas,
timeout, capability, authorization scope, audit event. Executors are
deterministic Python functions; the model never runs SQL, shell, code,
arbitrary HTTP, or browser commands.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from pydantic import BaseModel

from services.assistant.types import ToolEvent

logger = structlog.get_logger(__name__)


class ToolDefinition(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    name: str
    description: str
    input_schema: type[BaseModel]
    output_schema: type[BaseModel] | None = None
    timeout: int = 30
    capability: str = "general"
    # Tool family for dynamic per-step filtering (Phase B latency work):
    # only families relevant to the user turn are offered to the model.
    # Families: market, weather, schemes, disease, planning.
    family: str = "general"
    auth_scope: str = "user"
    audit_event: str = ""

    def openai_spec(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.input_schema.model_json_schema(),
        }


Executor = Callable[[dict[str, Any], dict[str, Any]], Awaitable[dict[str, Any]]]


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}
        self._executors: dict[str, Executor] = {}

    def register(self, definition: ToolDefinition, executor: Executor) -> None:
        if definition.name in self._tools:
            raise ValueError(f"tool already registered: {definition.name}")
        self._tools[definition.name] = definition
        self._executors[definition.name] = executor

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def specs(self) -> list[dict[str, Any]]:
        return [t.openai_spec() for t in self._tools.values()]

    def specs_for(self, families: set[str] | None) -> list[dict[str, Any]]:
        """Specs filtered to the given tool families.

        None or empty means all families (existing behavior). Family
        names of offered tools are exposed to traces by the caller.
        """
        if not families:
            return self.specs()
        return [t.openai_spec() for t in self._tools.values() if t.family in families]

    def families(self) -> set[str]:
        return {t.family for t in self._tools.values()}

    def names(self) -> list[str]:
        return list(self._tools)

    async def execute(self, name: str, arguments: dict[str, Any], context: dict[str, Any]) -> tuple[dict[str, Any], ToolEvent]:
        import time

        from telemetry.assistant_metrics import TOOL_CALLS

        started = time.monotonic()
        definition = self._tools.get(name)
        if definition is None:
            event = ToolEvent(tool=name, status="failed", detail="unknown tool")
            logger.warning("assistant_tool_rejected", tool=name, reason="unregistered")
            TOOL_CALLS.labels(tool=name, status="rejected").inc()
            return {"error": f"Unknown tool: {name}"}, event
        try:
            validated = definition.input_schema(**(arguments or {}))
        except Exception as e:
            event = ToolEvent(tool=name, status="failed", detail=f"invalid arguments: {e}")
            logger.warning("assistant_tool_rejected", tool=name, reason="schema")
            TOOL_CALLS.labels(tool=name, status="rejected").inc()
            return {"error": f"Invalid arguments for {name}: {e}"}, event
        try:
            output = await self._executors[name](validated.model_dump(), context)
        except Exception as e:
            event = ToolEvent(
                tool=name, status="failed", detail=str(e),
                latency_ms=int((time.monotonic() - started) * 1000),
            )
            logger.warning("assistant_tool_failed", tool=name, error=str(e))
            TOOL_CALLS.labels(tool=name, status="failed").inc()
            return {"error": f"Tool {name} failed: {e}"}, event
        if definition.audit_event:
            logger.info(
                "assistant_tool_audit", audit_event=definition.audit_event, tool=name,
                user=context.get("user_id"), conversation=context.get("conversation_id"),
            )
        event = ToolEvent(
            tool=name, status="succeeded",
            latency_ms=int((time.monotonic() - started) * 1000),
        )
        TOOL_CALLS.labels(tool=name, status="succeeded").inc()
        return output, event


tool_registry = ToolRegistry()
