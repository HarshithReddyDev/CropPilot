"""Deterministic provider router with ordered fallback and cooldown.

Priority comes from ASSISTANT_PROVIDER_ORDER. No random switching: the
first capable, non-cooling provider wins. Failures cool the provider down
so a dead endpoint is not hammered every request.
"""

from __future__ import annotations

import time
from collections.abc import AsyncIterator
from typing import Any

import structlog
from opentelemetry import trace

from core.config import settings
from services.assistant.providers import (
    GeminiProvider,
    GroqProvider,
    LLMProvider,
    OllamaProvider,
    OpenRouterProvider,
    ProviderError,
)
from services.assistant.types import (
    ChatMessage,
    ProviderChatResult,
    ProviderHealth,
    ProviderStatus,
    RequestRequirements,
    UsageStats,
)

logger = structlog.get_logger(__name__)
tracer = trace.get_tracer(__name__)


def _parse_order(raw: str) -> list[str]:
    return [p.strip().lower() for p in (raw or "").split(",") if p.strip()]


#: How long a positive ollama readiness probe stays trusted. Ollama can
#: restart independently of the api process, so cached True must expire.
MODEL_READY_TTL_S = 60.0


def _shift_reason(status: ProviderStatus) -> str:
    """Map a provider failure status to a tier_shift reason label."""
    return {
        ProviderStatus.RATE_LIMITED: "rate_limit",
        ProviderStatus.QUOTA_EXHAUSTED: "quota_exhausted",
        ProviderStatus.TIMEOUT: "timeout",
    }.get(status, "unavailable")


class LLMProviderRouter:
    def __init__(self):
        self._providers: dict[str, LLMProvider] = {}
        self._cooldown_until: dict[str, float] = {}
        self._failures: dict[str, int] = {}
        # Readiness cache: positive ollama probe cached (model present stays
        # present); negative never cached so a pulled model is picked up.
        self._ollama_ready: bool = False
        self._ollama_ready_at: float | None = None
        self._register_configured()

    def _register_configured(self) -> None:
        if settings.GEMINI_API_KEY and settings.GEMINI_MODEL:
            self._providers["gemini"] = GeminiProvider(settings.GEMINI_API_KEY, settings.GEMINI_MODEL)
        if settings.OPENROUTER_API_KEY and settings.OPENROUTER_MODEL:
            self._providers["openrouter"] = OpenRouterProvider(
                settings.OPENROUTER_API_KEY, settings.OPENROUTER_MODEL, settings.OPENROUTER_FREE_ROUTER,
            )
        elif settings.OPENROUTER_API_KEY:
            # Tiering without the legacy single model: register the leg so
            # the router order includes it. Capabilities are the UNION
            # across tiers (a tool request must still reach a tool-capable
            # Tier 2 even when Tier 1 cannot serve it); per-tier gates
            # apply inside the tier loop. Model label is Tier 1.
            from services.assistant.openrouter_tiers import build_tiers

            tiers = build_tiers()
            if tiers:
                self._providers["openrouter"] = OpenRouterProvider(
                    settings.OPENROUTER_API_KEY,
                    tiers[0].model,
                    tool_calling=any(t.tool_calling for t in tiers),
                    max_context=max(t.effective_context() for t in tiers),
                )
        if settings.GROQ_API_KEY and settings.GROQ_MODEL:
            self._providers["groq"] = GroqProvider(settings.GROQ_API_KEY, settings.GROQ_MODEL)
        # Ollama always registered: local-only mode must work with no keys.
        self._providers["ollama"] = OllamaProvider(
            settings.OLLAMA_BASE_URL, settings.ASSISTANT_LOCAL_MODEL, settings.ASSISTANT_LOCAL_FALLBACK_MODEL,
        )

    @property
    def order(self) -> list[str]:
        ordered = [p for p in _parse_order(settings.ASSISTANT_PROVIDER_ORDER) if p in self._providers]
        for name in self._providers:
            if name not in ordered:
                ordered.append(name)
        return ordered

    def _cooling(self, name: str) -> bool:
        return time.monotonic() < self._cooldown_until.get(name, 0.0)

    def _meets(self, provider: LLMProvider, req: RequestRequirements) -> bool:
        caps = provider.capabilities()
        if req.function_calling and not caps.function_calling:
            return False
        if req.structured_output and not caps.structured_output:
            return False
        if req.vision and not caps.vision:
            return False
        if req.min_context and caps.max_context < req.min_context:
            return False
        if req.language and caps.languages and req.language not in caps.languages:
            return False
        return True

    def _note_failure(self, name: str, status: ProviderStatus) -> None:
        from telemetry.assistant_metrics import PROVIDER_COOLDOWN

        self._failures[name] = self._failures.get(name, 0) + 1
        if status in (ProviderStatus.RATE_LIMITED, ProviderStatus.QUOTA_EXHAUSTED, ProviderStatus.TIMEOUT):
            self._cooldown_until[name] = time.monotonic() + settings.ASSISTANT_PROVIDER_COOLDOWN_SECONDS
            PROVIDER_COOLDOWN.labels(provider=name).inc()
        elif self._failures[name] >= 3:
            self._cooldown_until[name] = time.monotonic() + settings.ASSISTANT_PROVIDER_COOLDOWN_SECONDS
            PROVIDER_COOLDOWN.labels(provider=name).inc()

    def _note_success(self, name: str) -> None:
        self._failures.pop(name, None)
        self._cooldown_until.pop(name, None)

    def _tiering_active(self) -> bool:
        if not settings.ASSISTANT_OPENROUTER_TIERING_ENABLED:
            return False
        if not settings.OPENROUTER_API_KEY:
            return False
        from services.assistant.openrouter_tiers import build_tiers

        return bool(build_tiers())

    def _tier_provider(self, tier: Any) -> OpenRouterProvider:
        return OpenRouterProvider(
            settings.OPENROUTER_API_KEY,
            tier.model,
            tool_calling=tier.tool_calling,
            max_context=tier.effective_context(),
        )

    async def _chat_openrouter_tiers(
        self,
        messages: list[ChatMessage],
        tools: list[dict[str, Any]] | None,
        req: RequestRequirements,
        tool_choice: str | None,
        span: Any,
        attempted: list[str],
        errors: list[str],
    ) -> ProviderChatResult:
        """Tier 1 -> Tier 2 -> Tier 3 with budget reservation + failover.
        Raises ProviderError: outer loop then continues to Ollama, except
        INVALID_REQUEST which propagates (no blind retry elsewhere)."""
        import time as _time

        from db.session import async_session_factory
        from services.assistant.openrouter_tiers import _reserve_tokens, build_tiers, tier_manager
        from telemetry.assistant_metrics import PROVIDER_REQUESTS, PROVIDER_TOKENS, REQUEST_LATENCY

        tiers = build_tiers()
        prev: str = "none"
        async with async_session_factory() as db:
            for tier in tiers:
                ok, reason = tier_manager.eligible(tier, req)
                if not ok:
                    if reason not in ("cooling",):
                        tier_manager.shift(prev, tier.tier, reason)
                    prev = str(tier.tier)
                    continue
                reserve = _reserve_tokens()
                if not await tier_manager.reserve(db, tier):
                    tier_manager.shift(prev, tier.tier, "budget_exhausted")
                    prev = str(tier.tier)
                    continue
                provider = self._tier_provider(tier)
                attempted.append(f"openrouter:t{tier.tier}")
                started = _time.monotonic()
                try:
                    result = await provider.chat(
                        messages, tools,
                        timeout=settings.ASSISTANT_REQUEST_TIMEOUT,
                        tool_choice=tool_choice,
                    )
                except ProviderError as e:
                    await tier_manager.reconcile(db, tier, reserve, None)
                    latency = _time.monotonic() - started
                    REQUEST_LATENCY.labels(provider="openrouter", tier=str(tier.tier)).observe(latency)
                    if e.status == ProviderStatus.INVALID_REQUEST:
                        raise
                    if e.status == ProviderStatus.MISCONFIGURED:
                        errors.append(f"openrouter:t{tier.tier}: {e}")
                        break  # auth broken for all tiers; fall through to Ollama
                    if e.status == ProviderStatus.MODEL_NOT_FOUND:
                        tier_manager.disable_model(tier.model)
                        tier_manager.shift(prev, tier.tier, "unavailable")
                    else:
                        tier_manager.cool_tier(tier.model)
                        tier_manager.shift(prev, tier.tier, _shift_reason(e.status))
                    errors.append(f"openrouter:t{tier.tier}: {e}")
                    logger.warning(
                        "assistant_tier_failed", tier=tier.tier, model=tier.model,
                        status=e.status.value, error=str(e),
                    )
                    prev = str(tier.tier)
                    continue
                latency = _time.monotonic() - started
                REQUEST_LATENCY.labels(provider="openrouter", tier=str(tier.tier)).observe(latency)
                PROVIDER_REQUESTS.labels(provider="openrouter", tier=str(tier.tier), status="succeeded").inc()
                if result.usage is not None:
                    PROVIDER_TOKENS.labels(provider="openrouter", tier=str(tier.tier), kind="prompt").inc(result.usage.prompt_tokens)
                    PROVIDER_TOKENS.labels(provider="openrouter", tier=str(tier.tier), kind="completion").inc(result.usage.completion_tokens)
                    PROVIDER_TOKENS.labels(provider="openrouter", tier=str(tier.tier), kind="total").inc(result.usage.total_tokens)
                await tier_manager.reconcile(db, tier, reserve, result.usage)
                self._note_success("openrouter")
                if prev != "none":
                    logger.info("assistant_provider_fallback", provider=f"openrouter:t{tier.tier}", attempted=attempted)
                span.set_attribute("assistant.provider", "openrouter")
                span.set_attribute("assistant.model", result.model)
                span.set_attribute("assistant.tier", tier.tier)
                return result
        raise ProviderError(
            "OpenRouter tiers exhausted"
            + (f" ({'; '.join(errors)})" if errors else "")
            + "; falling back.",
            ProviderStatus.UNAVAILABLE,
        )

    async def chat(
        self,
        messages: list[ChatMessage],
        tools: list[dict[str, Any]] | None = None,
        requirements: RequestRequirements | None = None,
        tool_choice: str | None = None,
    ) -> ProviderChatResult:
        req = requirements or RequestRequirements(function_calling=bool(tools))
        errors: list[str] = []
        attempted: list[str] = []
        with tracer.start_as_current_span("assistant.provider.route") as span:
            for name in self.order:
                provider = self._providers[name]
                if not self._meets(provider, req):
                    continue
                if self._cooling(name):
                    errors.append(f"{name}: cooling down")
                    continue
                if name == "openrouter" and self._tiering_active():
                    try:
                        return await self._chat_openrouter_tiers(
                            messages, tools, req, tool_choice, span, attempted, errors,
                        )
                    except ProviderError as e:
                        if e.status == ProviderStatus.INVALID_REQUEST:
                            raise
                        self._note_failure(name, e.status)
                        errors.append(f"{name}: {e}")
                        continue
                attempted.append(name)
                try:
                    result = await provider.chat(messages, tools, timeout=settings.ASSISTANT_REQUEST_TIMEOUT, tool_choice=tool_choice)
                except ProviderError as e:
                    if e.status == ProviderStatus.INVALID_REQUEST:
                        raise
                    self._note_failure(name, e.status)
                    errors.append(f"{name}: {e}")
                    logger.warning("assistant_provider_failed", provider=name, status=e.status.value, error=str(e))
                    continue
                self._note_success(name)
                if len(attempted) > 1:
                    logger.info("assistant_provider_fallback", provider=name, attempted=attempted)
                    span.set_attribute("assistant.fallback_to", name)
                span.set_attribute("assistant.provider", name)
                span.set_attribute("assistant.model", result.model)
                return result
        raise ProviderError(
            "I can't reach the AI model right now. Please try again later."
            + (f" ({'; '.join(errors)})" if errors else ""),
            ProviderStatus.UNAVAILABLE,
        )

    def stream(
        self,
        messages: list[ChatMessage],
        tools: list[dict[str, Any]] | None = None,
        requirements: RequestRequirements | None = None,
    ) -> AsyncIterator[tuple[str, str, str]]:
        return self._stream_inner(messages, tools, requirements)

    async def _stream_inner(
        self,
        messages: list[ChatMessage],
        tools: list[dict[str, Any]] | None,
        requirements: RequestRequirements | None,
    ) -> AsyncIterator[tuple[str, str, str]]:
        """Yields (provider, model, delta). Falls forward on provider errors."""
        req = requirements or RequestRequirements(function_calling=bool(tools))
        errors: list[str] = []
        for name in self.order:
            provider = self._providers[name]
            if not self._meets(provider, req) or self._cooling(name):
                continue
            if name == "openrouter" and self._tiering_active():
                try:
                    async for item in self._stream_openrouter_tiers(messages, tools, req, errors):
                        yield item
                    return
                except ProviderError as e:
                    if e.status == ProviderStatus.INVALID_REQUEST:
                        raise
                    self._note_failure(name, e.status)
                    errors.append(f"{name}: {e}")
                    continue
            try:
                async for delta in provider.stream(messages, tools, timeout=settings.ASSISTANT_REQUEST_TIMEOUT):
                    yield name, provider.model_name(), delta
                self._note_success(name)
                return
            except ProviderError as e:
                if e.status == ProviderStatus.INVALID_REQUEST:
                    raise
                self._note_failure(name, e.status)
                errors.append(f"{name}: {e}")
                logger.warning("assistant_provider_failed", provider=name, status=e.status.value, error=str(e))
                continue
        raise ProviderError(
            "I can't reach the AI model right now. Please try again later."
            + (f" ({'; '.join(errors)})" if errors else ""),
            ProviderStatus.UNAVAILABLE,
        )

    async def _stream_openrouter_tiers(
        self,
        messages: list[ChatMessage],
        tools: list[dict[str, Any]] | None,
        req: RequestRequirements,
        errors: list[str],
    ) -> AsyncIterator[tuple[str, str, str]]:
        """Tiered streaming with usage reconciliation. Yields
        ("openrouter", tier_model, delta)."""
        import time as _time

        from db.session import async_session_factory
        from services.assistant.openrouter_tiers import _reserve_tokens, build_tiers, tier_manager
        from telemetry.assistant_metrics import PROVIDER_REQUESTS, PROVIDER_TOKENS, REQUEST_LATENCY

        tiers = build_tiers()
        prev = "none"
        async with async_session_factory() as db:
            for tier in tiers:
                ok, reason = tier_manager.eligible(tier, req)
                if not ok:
                    if reason not in ("cooling",):
                        tier_manager.shift(prev, tier.tier, reason)
                    prev = str(tier.tier)
                    continue
                reserve = _reserve_tokens()
                if not await tier_manager.reserve(db, tier):
                    tier_manager.shift(prev, tier.tier, "budget_exhausted")
                    prev = str(tier.tier)
                    continue
                provider = self._tier_provider(tier)
                seen: list[UsageStats] = []
                started = _time.monotonic()
                try:
                    async for delta in provider.stream(
                        messages, tools,
                        timeout=settings.ASSISTANT_REQUEST_TIMEOUT,
                        on_usage=seen.append,
                    ):
                        yield "openrouter", tier.model, delta
                except ProviderError as e:
                    await tier_manager.reconcile(db, tier, reserve, None)
                    REQUEST_LATENCY.labels(provider="openrouter", tier=str(tier.tier)).observe(_time.monotonic() - started)
                    if e.status == ProviderStatus.INVALID_REQUEST:
                        raise
                    if e.status == ProviderStatus.MISCONFIGURED:
                        errors.append(f"openrouter:t{tier.tier}: {e}")
                        break
                    if e.status == ProviderStatus.MODEL_NOT_FOUND:
                        tier_manager.disable_model(tier.model)
                        tier_manager.shift(prev, tier.tier, "unavailable")
                    else:
                        tier_manager.cool_tier(tier.model)
                        tier_manager.shift(prev, tier.tier, _shift_reason(e.status))
                    errors.append(f"openrouter:t{tier.tier}: {e}")
                    prev = str(tier.tier)
                    continue
                usage = seen[0] if seen else None
                REQUEST_LATENCY.labels(provider="openrouter", tier=str(tier.tier)).observe(_time.monotonic() - started)
                PROVIDER_REQUESTS.labels(provider="openrouter", tier=str(tier.tier), status="succeeded").inc()
                if usage is not None:
                    PROVIDER_TOKENS.labels(provider="openrouter", tier=str(tier.tier), kind="prompt").inc(usage.prompt_tokens)
                    PROVIDER_TOKENS.labels(provider="openrouter", tier=str(tier.tier), kind="completion").inc(usage.completion_tokens)
                    PROVIDER_TOKENS.labels(provider="openrouter", tier=str(tier.tier), kind="total").inc(usage.total_tokens)
                await tier_manager.reconcile(db, tier, reserve, usage)
                self._note_success("openrouter")
                return
        raise ProviderError(
            "OpenRouter tiers exhausted"
            + (f" ({'; '.join(errors)})" if errors else "")
            + "; falling back.",
            ProviderStatus.UNAVAILABLE,
        )

    async def ollama_model_ready(self) -> tuple[bool, float]:
        """Lightweight model-presence probe. Returns (ready, probe_ms).

        Positive result cached for MODEL_READY_TTL_S: an installed model
        does not uninstall itself, but Ollama itself can restart, so a
        stale True must expire (else /assistant/health reports ready
        while Ollama is down). Negative never cached so a fresh
        `ollama pull` is picked up on the next health check.
        Never raises; offline returns False.
        """
        import httpx

        if self._ollama_ready and self._ollama_ready_at is not None:
            if time.monotonic() - self._ollama_ready_at < MODEL_READY_TTL_S:
                return True, 0.0
            self._ollama_ready = False  # TTL expired: re-probe below
        started = time.monotonic()
        provider = self._providers.get("ollama")
        base = getattr(provider, "_base", settings.OLLAMA_BASE_URL)
        model = settings.ASSISTANT_LOCAL_MODEL.split(":")[0]
        try:
            resp = await httpx.AsyncClient().get(
                base.replace("/v1", "/api/tags"), timeout=2.0,
            )
            names = [m.get("name", "") for m in resp.json().get("models", [])]
            ready = any(model in (n or "") for n in names)
        except Exception:
            ready = False
        probe_ms = (time.monotonic() - started) * 1000.0
        if ready:
            self._ollama_ready = True
            self._ollama_ready_at = time.monotonic()
        return ready, probe_ms

    async def provider_status(self) -> list[ProviderHealth]:
        states: list[ProviderHealth] = []
        for name in self.order:
            provider = self._providers[name]
            try:
                health = await provider.health()
            except ProviderError as e:
                health = ProviderHealth(
                    name=name, model="", status=e.status, detail=str(e),
                    capabilities=provider.capabilities(),
                )
            if self._cooling(name):
                health.detail = (health.detail + " [cooling down]").strip()
            states.append(health)
        return states


router = LLMProviderRouter()
