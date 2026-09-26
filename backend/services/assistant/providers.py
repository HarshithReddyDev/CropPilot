"""LLM provider abstraction. Direct HTTP, OpenAI-compatible chat shape.

All four providers speak the same wire shape so the agent stays
provider-independent. Selection/fallback lives in the router, never here.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

import httpx
import structlog

from services.assistant.types import (
    ChatMessage,
    ChatToolCall,
    ProviderCapabilities,
    ProviderChatResult,
    ProviderHealth,
    ProviderStatus,
    UsageStats,
)

logger = structlog.get_logger(__name__)

# Shared HTTP client: one connection pool per process instead of a fresh
# pool + TLS handshake per provider call. Per-request `timeout=` still
# applies at the call site. Lifespan-managed by the app; never closed here.
_SHARED_CLIENT: httpx.AsyncClient | None = None


def _client() -> httpx.AsyncClient:
    global _SHARED_CLIENT
    if _SHARED_CLIENT is None:
        _SHARED_CLIENT = httpx.AsyncClient(
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
    return _SHARED_CLIENT


class ProviderError(Exception):
    def __init__(self, message: str, status: ProviderStatus = ProviderStatus.UNAVAILABLE):
        super().__init__(message)
        self.status = status


def _openai_messages(messages: list[ChatMessage]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for m in messages:
        d: dict[str, Any] = {"role": m.role, "content": m.content}
        if m.tool_calls:
            d["tool_calls"] = [
                {
                    "id": t.id,
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "arguments": _json_dumps(t.arguments),
                    },
                }
                for t in m.tool_calls
            ]
        if m.tool_call_id:
            d["tool_call_id"] = m.tool_call_id
        if m.name:
            d["name"] = m.name
        out.append(d)
    return out


def _json_dumps(payload: dict[str, Any]) -> str:
    import json

    return json.dumps(payload)


def _parse_tool_calls(raw: list[dict[str, Any]]) -> list[ChatToolCall]:
    import json

    calls: list[ChatToolCall] = []
    for t in raw or []:
        fn = t.get("function", {})
        try:
            args = json.loads(fn.get("arguments") or "{}")
        except (ValueError, TypeError):
            args = {}
        if not isinstance(args, dict):
            args = {}
        calls.append(ChatToolCall(id=t.get("id", ""), name=fn.get("name", ""), arguments=args))
    return calls


class LLMProvider(ABC):
    """Provider-independent interface. Agent code never branches on provider."""

    @abstractmethod
    def name(self) -> str: ...

    def model_name(self) -> str:
        return getattr(self, "_model", "")

    @abstractmethod
    def capabilities(self) -> ProviderCapabilities: ...

    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        tools: list[dict[str, Any]] | None = None,
        timeout: int = 60,
        tool_choice: str | None = None,
    ) -> ProviderChatResult: ...

    @abstractmethod
    def stream(
        self,
        messages: list[ChatMessage],
        tools: list[dict[str, Any]] | None = None,
        timeout: int = 60,
        on_usage: Any = None,
    ) -> AsyncIterator[str]: ...

    @abstractmethod
    async def health(self) -> ProviderHealth: ...


class OpenAICompatibleProvider(LLMProvider):
    """Shared HTTP core: POST {base_url}/chat/completions, SSE stream."""

    def __init__(
        self,
        provider_name: str,
        base_url: str,
        model: str,
        api_key: str = "",
        capabilities: ProviderCapabilities | None = None,
        extra_headers: dict[str, str] | None = None,
    ):
        self._name = provider_name
        self._base = base_url.rstrip("/")
        self._model = model
        self._key = api_key
        self._caps = capabilities or ProviderCapabilities()
        self._headers = {"Content-Type": "application/json", **(extra_headers or {})}
        if api_key:
            self._headers["Authorization"] = f"Bearer {api_key}"

    def name(self) -> str:
        return self._name

    def capabilities(self) -> ProviderCapabilities:
        return self._caps

    def _extra_body(self) -> dict[str, Any]:
        """Provider-specific body fields. Base: none."""
        return {}

    def _payload(self, messages: list[ChatMessage], tools: list[dict[str, Any]] | None, stream: bool, tool_choice: str | None = None) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": self._model,
            "messages": _openai_messages(messages),
            "stream": stream,
            # temperature 0: tool-calling small models (llama3.1:8b) narrate
            # phantom API calls at default sampling instead of emitting
            # real tool calls. Deterministic output required.
            "temperature": 0,
            **self._extra_body(),
        }
        if tools and self._caps.function_calling:
            body["tools"] = [{"type": "function", "function": t} for t in tools]
            # "required" forces a real tool call. Used on step 0 for
            # factual questions: small local models otherwise answer
            # from weights and hallucinate prices/schemes.
            if tool_choice:
                body["tool_choice"] = tool_choice
        return body

    async def chat(
        self,
        messages: list[ChatMessage],
        tools: list[dict[str, Any]] | None = None,
        timeout: int = 60,
        tool_choice: str | None = None,
    ) -> ProviderChatResult:
        started = time.monotonic()
        try:
            resp = await _client().post(
                f"{self._base}/chat/completions",
                headers=self._headers,
                json=self._payload(messages, tools, stream=False, tool_choice=tool_choice),
                timeout=timeout,
            )
        except httpx.TimeoutException as e:
            raise ProviderError(f"{self._name} timed out", ProviderStatus.TIMEOUT) from e
        except httpx.ConnectError as e:
            raise ProviderError(f"{self._name} unreachable: {e}", ProviderStatus.UNAVAILABLE) from e
        if resp.status_code == 429:
            raise ProviderError(f"{self._name} rate limited", ProviderStatus.RATE_LIMITED)
        if resp.status_code in (401, 403):
            raise ProviderError(f"{self._name} rejected credentials", ProviderStatus.MISCONFIGURED)
        if resp.status_code == 402:
            raise ProviderError(f"{self._name} credits exhausted", ProviderStatus.QUOTA_EXHAUSTED)
        if resp.status_code == 404:
            raise ProviderError(f"{self._name} model not found: {self._model}", ProviderStatus.MODEL_NOT_FOUND)
        if resp.status_code in (400, 422):
            raise ProviderError(f"{self._name} rejected request ({resp.status_code})", ProviderStatus.INVALID_REQUEST)
        if resp.status_code >= 500:
            raise ProviderError(f"{self._name} server error {resp.status_code}", ProviderStatus.UNAVAILABLE)
        if resp.status_code != 200:
            raise ProviderError(f"{self._name} error {resp.status_code}", ProviderStatus.UNAVAILABLE)
        try:
            body = resp.json()
            choice = body["choices"][0]["message"]
        except (ValueError, KeyError, IndexError) as e:
            raise ProviderError(f"{self._name} bad response", ProviderStatus.UNAVAILABLE) from e
        logger.info("assistant_provider_chat", provider=self._name, latency_ms=int((time.monotonic() - started) * 1000))
        return ProviderChatResult(
            message=ChatMessage(
                role="assistant",
                content=choice.get("content") or "",
                tool_calls=_parse_tool_calls(choice.get("tool_calls") or []),
            ),
            model=self._model,
            provider=self._name,
            usage=UsageStats.from_openrouter(body.get("usage")),
        )

    async def stream(
        self,
        messages: list[ChatMessage],
        tools: list[dict[str, Any]] | None = None,
        timeout: int = 60,
        on_usage: Any = None,
    ) -> AsyncIterator[str]:
        """Yield content deltas. If on_usage is given it is called once with
        the UsageStats from OpenRouter's terminal accounting chunk (the
        final chunk before [DONE]; content-free delta + usage object).
        Missing usage -> on_usage never fires, never fabricated."""
        import json

        try:
            async with _client().stream(
                "POST",
                f"{self._base}/chat/completions",
                headers=self._headers,
                json=self._payload(messages, tools, stream=True),
                timeout=timeout,
            ) as resp:
                    if resp.status_code == 429:
                        raise ProviderError(f"{self._name} rate limited", ProviderStatus.RATE_LIMITED)
                    if resp.status_code in (401, 403):
                        raise ProviderError(f"{self._name} rejected credentials", ProviderStatus.MISCONFIGURED)
                    if resp.status_code == 402:
                        raise ProviderError(f"{self._name} credits exhausted", ProviderStatus.QUOTA_EXHAUSTED)
                    if resp.status_code == 404:
                        raise ProviderError(f"{self._name} model not found: {self._model}", ProviderStatus.MODEL_NOT_FOUND)
                    if resp.status_code in (400, 422):
                        raise ProviderError(f"{self._name} rejected request ({resp.status_code})", ProviderStatus.INVALID_REQUEST)
                    if resp.status_code != 200:
                        raise ProviderError(f"{self._name} error {resp.status_code}", ProviderStatus.UNAVAILABLE)
                    async for line in resp.aiter_lines():
                        if not line.startswith("data:"):
                            continue
                        data = line[5:].strip()
                        if data == "[DONE]":
                            return
                        try:
                            chunk = json.loads(data)
                            delta = chunk["choices"][0]["delta"]
                        except (ValueError, KeyError, IndexError):
                            continue
                        if on_usage is not None:
                            usage = UsageStats.from_openrouter(chunk.get("usage"))
                            if usage is not None:
                                try:
                                    on_usage(usage)
                                except Exception:
                                    logger.warning("assistant_usage_sink_failed", provider=self._name)
                                on_usage = None  # usage arrives exactly once
                        if delta.get("content"):
                            yield delta["content"]
        except httpx.TimeoutException as e:
            raise ProviderError(f"{self._name} timed out", ProviderStatus.TIMEOUT) from e
        except httpx.ConnectError as e:
            raise ProviderError(f"{self._name} unreachable: {e}", ProviderStatus.UNAVAILABLE) from e

    async def health(self) -> ProviderHealth:
        if not self._model:
            return ProviderHealth(
                name=self._name, model="", status=ProviderStatus.MISCONFIGURED,
                detail="model not configured", capabilities=self._caps,
            )
        try:
            result = await self.chat(
                [ChatMessage(role="user", content="ping")], tools=None, timeout=15,
            )
            ok = bool(result.message.content)
        except ProviderError as e:
            return ProviderHealth(
                name=self._name, model=self._model, status=e.status,
                detail=str(e), capabilities=self._caps,
            )
        return ProviderHealth(
            name=self._name, model=self._model,
            status=ProviderStatus.AVAILABLE if ok else ProviderStatus.UNAVAILABLE,
            capabilities=self._caps,
        )


class OllamaProvider(OpenAICompatibleProvider):
    def __init__(self, base_url: str, model: str, fallback_model: str = ""):
        super().__init__(
            "ollama", f"{base_url.rstrip('/')}/v1", model,
            capabilities=ProviderCapabilities(
                function_calling=True, structured_output=False, vision=False,
                max_context=32768, languages=["en", "hi", "te"],
            ),
        )
        self._fallback_model = fallback_model

    def _extra_body(self) -> dict[str, Any]:
        # keep_alive avoids a ~15-20s model reload on CPU boxes between
        # turns. Value comes from OLLAMA_KEEP_ALIVE ("30m" typical).
        from core.config import settings

        keep = (settings.OLLAMA_KEEP_ALIVE or "").strip()
        return {"keep_alive": keep} if keep else {}

    async def health(self) -> ProviderHealth:
        # No auto-download: report missing model as a diagnostics error.
        try:
            resp = await _client().get(f"{self._base}/models", timeout=10)
            if resp.status_code != 200:
                tags = await _client().get(self._base.replace("/v1", "/api/tags"), timeout=10)
                tags.raise_for_status()
                names = [m.get("name", "") for m in tags.json().get("models", [])]
            else:
                names = [m.get("id", "") for m in resp.json().get("data", [])]
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            return ProviderHealth(
                name="ollama", model=self._model, status=ProviderStatus.UNAVAILABLE,
                detail=f"Ollama not reachable at {self._base}: {e}. Start Ollama first.",
                capabilities=self._caps,
            )
        except httpx.HTTPError as e:
            return ProviderHealth(
                name="ollama", model=self._model, status=ProviderStatus.UNAVAILABLE,
                detail=str(e), capabilities=self._caps,
            )
        short = self._model.split(":")[0]
        if not any(short in (n or "") for n in names):
            hint = f"Model '{self._model}' not installed. Run: ollama pull {self._model}"
            if self._fallback_model:
                hint += f" (fallback configured: {self._fallback_model})"
            return ProviderHealth(
                name="ollama", model=self._model, status=ProviderStatus.MISCONFIGURED,
                detail=hint, capabilities=self._caps,
            )
        if self._fallback_model and not any(self._fallback_model.split(":")[0] in (n or "") for n in names):
            logger.warning("assistant_ollama_fallback_missing", model=self._fallback_model)
        return ProviderHealth(
            name="ollama", model=self._model, status=ProviderStatus.AVAILABLE,
            capabilities=self._caps,
        )


class OpenRouterProvider(OpenAICompatibleProvider):
    def __init__(
        self,
        api_key: str,
        model: str,
        free_router: bool = False,
        tool_calling: bool = True,
        max_context: int = 65536,
    ):
        super().__init__(
            "openrouter", "https://openrouter.ai/api/v1", model, api_key,
            capabilities=ProviderCapabilities(
                function_calling=tool_calling and not free_router,
                structured_output=False,
                max_context=max_context,
            ),
            extra_headers={"HTTP-Referer": "https://croppilot.local", "X-Title": "CropPilot"},
        )
        self._free_router = free_router


class GeminiProvider(OpenAICompatibleProvider):
    def __init__(self, api_key: str, model: str):
        super().__init__(
            "gemini", "https://generativelanguage.googleapis.com/v1beta/openai", model, api_key,
            capabilities=ProviderCapabilities(
                function_calling=True, structured_output=True,
                vision=True, long_context=True, max_context=1_000_000,
            ),
        )


class GroqProvider(OpenAICompatibleProvider):
    def __init__(self, api_key: str, model: str):
        super().__init__(
            "groq", "https://api.groq.com/openai/v1", model, api_key,
            capabilities=ProviderCapabilities(
                function_calling=True, structured_output=True, max_context=32768,
            ),
        )
