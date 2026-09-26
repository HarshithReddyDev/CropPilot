"""Shared assistant types. Provider-independent by design."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ProviderStatus(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    RATE_LIMITED = "rate_limited"
    QUOTA_EXHAUSTED = "quota_exhausted"
    TIMEOUT = "timeout"
    MISCONFIGURED = "misconfigured"
    MODEL_NOT_FOUND = "model_not_found"
    INVALID_REQUEST = "invalid_request"


class ProviderCapabilities(BaseModel):
    text_generation: bool = True
    streaming: bool = True
    function_calling: bool = True
    structured_output: bool = False
    vision: bool = False
    long_context: bool = False
    multilingual: bool = True
    languages: list[str] = Field(default_factory=list)
    max_context: int = 8192


class ChatToolCall(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ChatMessage(BaseModel):
    role: str  # system | user | assistant | tool
    content: str = ""
    tool_calls: list[ChatToolCall] = Field(default_factory=list)
    tool_call_id: str | None = None
    name: str | None = None


class UsageStats(BaseModel):
    """Normalized provider-reported token usage. Real numbers only —
    never estimated. Missing provider data stays None, never zero-filled."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    @classmethod
    def from_openrouter(cls, raw: Any) -> UsageStats | None:
        if not isinstance(raw, dict):
            return None
        try:
            prompt = int(raw.get("prompt_tokens") or 0)
            completion = int(raw.get("completion_tokens") or 0)
            total = int(raw.get("total_tokens") or (prompt + completion))
        except (TypeError, ValueError):
            return None
        if prompt < 0 or completion < 0 or total < 0:
            return None
        return cls(prompt_tokens=prompt, completion_tokens=completion, total_tokens=total)


class ProviderChatResult(BaseModel):
    message: ChatMessage
    model: str
    provider: str
    usage: UsageStats | None = None


class ProviderHealth(BaseModel):
    name: str
    model: str
    status: ProviderStatus
    detail: str = ""
    capabilities: ProviderCapabilities = Field(default_factory=ProviderCapabilities)


class RequestRequirements(BaseModel):
    """What a request needs; router matches against capabilities."""

    function_calling: bool = False
    structured_output: bool = False
    vision: bool = False
    min_context: int = 0
    language: str | None = None


class Citation(BaseModel):
    title: str
    snippet: str = ""
    publisher: str = ""
    source: str = ""
    source_url: str = ""
    document_id: str = ""
    date: str = ""


class ToolEvent(BaseModel):
    tool: str
    status: str  # started | succeeded | failed
    detail: str = ""
    latency_ms: int = 0


class UIAction(BaseModel):
    action: str
    payload: dict[str, Any] = Field(default_factory=dict)
