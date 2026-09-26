"""Schemas for the single bounded CropPilot assistant (§19-§22).

Phase 7: `conversation_id` is server-owned. Posting without one creates a
conversation; the response carries its id and subsequent turns append.
"""

from pydantic import BaseModel, Field


class AssistantChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = None
    state: str | None = None
    commodity: str | None = None
    h3_index: str | None = None
    language: str = "en"
    # Page-aware context (V1.3): safe, allow-listed fields only. The
    # frontend sends its current route + visible filter state so "what am
    # I looking at" works. Never secrets, tokens, or DOM dumps.
    route: str | None = Field(default=None, max_length=64)
    page: str | None = Field(default=None, max_length=32)
    page_filters: dict = Field(default_factory=dict)


class AssistantCitationOut(BaseModel):
    source: str
    title: str
    snippet: str = ""
    score: float | None = None


class AssistantUIActionOut(BaseModel):
    action: str
    payload: dict = Field(default_factory=dict)


class AssistantChatResponse(BaseModel):
    text: str
    conversation_id: str | None = None
    provider: str | None = None
    citations: list[AssistantCitationOut] = Field(default_factory=list)
    ui_actions: list[AssistantUIActionOut] = Field(default_factory=list)
    tool_events: list[dict] = Field(default_factory=list)


class AssistantCapabilitiesResponse(BaseModel):
    enabled: bool
    providers: list[dict] = Field(default_factory=list)
    tools: list[dict] = Field(default_factory=list)
    ui_actions: list[str] = Field(default_factory=list)
    # Safe OpenRouter tier state (no keys, no quotas from the provider):
    # [{tier, model, enabled, tool_calling}]. Budget counters live behind
    # the admin diagnostics endpoint, never farmer-facing.
    openrouter: dict = Field(default_factory=dict)
    # V1.3 language/voice matrix from the canonical registry. Capability
    # flags reflect the actual runtime (uninstalled engines read false).
    languages: list[dict] = Field(default_factory=list)
    voice: dict = Field(default_factory=dict)
    # Translation bridge readiness (honest: ready false until weights land).
    translation: dict = Field(default_factory=dict)


class AssistantHealthResponse(BaseModel):
    enabled: bool
    configured_providers: list[str] = Field(default_factory=list)
    # Readiness split (§3): service running != model ready. model_ready is
    # a cheap cached presence probe; model_probe_ms is the probe latency
    # (0.0 when served from cache).
    model_ready: bool = False
    model_probe_ms: float = 0.0
    model: str = ""


class AssistantConversationOut(BaseModel):
    id: str
    title: str = ""


class AssistantMessageOut(BaseModel):
    role: str
    content: str
    provider: str = ""


class AssistantFeedbackRequest(BaseModel):
    message_id: str | None = None
    rating: str = Field(pattern="^(up|down)$")
    comment: str = Field(default="", max_length=1000)
