"""OpenRouter free-model tier manager: deterministic ordered fallback.

Tier 1 (strongest configured FREE model) -> Tier 2 -> Tier 3 -> Ollama.
Two distinct mechanisms:

1. BUDGET SHIFTING: a tier whose configured request/token budget is
   exhausted is skipped *before* any request is sent (reservation).
2. FAILURE FAILOVER: 429 / timeout / 5xx / 404-model moves to the next
   tier immediately; auth errors abort the OpenRouter leg; invalid
   requests are never blindly retried.

Budgets are LOCAL application caps, not provider quotas. Provider
429/402 moves tiers regardless of local budget state.

Persistence: one row per (UTC date, provider, model) in
`assistant_provider_usage`. Reservations use a single atomic
UPDATE ... WHERE (no read-then-write), so concurrent requests cannot
double-spend; contention fails closed to the next tier.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import structlog
from sqlalchemy import case, func, select, update
from sqlalchemy.exc import OperationalError

from core.config import settings
from db.session import async_session_factory
from models.assistant import AssistantProviderUsage
from services.assistant.types import (
    ChatMessage,
    ProviderChatResult,
    ProviderStatus,
    RequestRequirements,
    UsageStats,
)

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class TierSpec:
    """One configured tier. Single source of truth is Settings
    (ASSISTANT_OPENROUTER_TIER_{1,2,3}_*); nothing else hard-codes models."""

    tier: int
    model: str
    max_requests: int
    max_tokens: int
    tool_calling: bool
    max_context: int  # 0 = provider default

    def effective_context(self, default: int = 65536) -> int:
        return self.max_context or default


def build_tiers() -> list[TierSpec]:
    """Deterministic tier order 1->2->3. Tiers with an empty model are
    disabled; models not ending in ':free' are rejected (never silently
    route paid traffic)."""
    out: list[TierSpec] = []
    for n in (1, 2, 3):
        model = getattr(settings, f"ASSISTANT_OPENROUTER_TIER_{n}_MODEL", "").strip()
        if not model:
            continue
        if not model.endswith(":free"):
            logger.warning("assistant_tier_rejected_not_free", tier=n, model=model)
            continue
        out.append(
            TierSpec(
                tier=n,
                model=model,
                max_requests=max(1, getattr(settings, f"ASSISTANT_OPENROUTER_TIER_{n}_MAX_REQUESTS", 20)),
                max_tokens=max(1, getattr(settings, f"ASSISTANT_OPENROUTER_TIER_{n}_MAX_TOKENS", 100000)),
                tool_calling=bool(getattr(settings, f"ASSISTANT_OPENROUTER_TIER_{n}_TOOL_CALLING", True)),
                max_context=int(getattr(settings, f"ASSISTANT_OPENROUTER_TIER_{n}_MAX_CONTEXT", 0) or 0),
            )
        )
    return out


def _today() -> Any:
    # UTC aligns with OpenRouter's own free-quota reset (UTC midnight).
    # Non-UTC configuration falls back to server-local date.
    tz = (getattr(settings, "ASSISTANT_USAGE_TIMEZONE", "UTC") or "UTC").upper()
    if tz == "UTC":
        return datetime.now(timezone.utc).date()
    return datetime.now().date()


def _reserve_tokens() -> int:
    return max(0, int(getattr(settings, "ASSISTANT_OPENROUTER_TOKEN_RESERVE", 2000) or 0))


class TierManager:
    """Budget + cooldown state for OpenRouter tiers. Sessions are opened
    per call via the app session factory (same pattern as assistant
    tools); tests may inject their own factory."""

    def __init__(self, session_factory: Any = None):
        self._factory = session_factory
        self._disabled: set[str] = set()  # runtime-disabled models (404)
        self._cooldown_until: dict[str, float] = {}

    def _session(self) -> Any:
        return (self._factory or async_session_factory)()

    def reset_runtime_state(self) -> None:
        self._disabled.clear()
        self._cooldown_until.clear()

    # -- eligibility ----------------------------------------------------

    def tier_cooling(self, model: str) -> bool:
        return time.monotonic() < self._cooldown_until.get(model, 0.0)

    def cool_tier(self, model: str) -> None:
        from telemetry.assistant_metrics import PROVIDER_COOLDOWN

        self._cooldown_until[model] = time.monotonic() + settings.ASSISTANT_PROVIDER_COOLDOWN_SECONDS
        PROVIDER_COOLDOWN.labels(provider=f"openrouter:t{self._tier_of(model)}").inc()

    def _tier_of(self, model: str) -> str:
        for t in build_tiers():
            if t.model == model:
                return str(t.tier)
        return "?"

    def disable_model(self, model: str) -> None:
        self._disabled.add(model)

    def eligible(self, tier: TierSpec, req: RequestRequirements) -> tuple[bool, str]:
        """Capability gate. Returns (ok, reason)."""
        if tier.model in self._disabled:
            return False, "disabled"
        if self.tier_cooling(tier.model):
            return False, "cooling"
        if req.function_calling and not tier.tool_calling:
            return False, "capability_mismatch"
        if req.vision:
            return False, "capability_mismatch"
        if req.structured_output:
            return False, "capability_mismatch"
        if req.min_context and tier.effective_context() < req.min_context:
            return False, "capability_mismatch"
        return True, ""

    # -- budget ----------------------------------------------------------

    async def _row(self, db: Any, tier: TierSpec) -> AssistantProviderUsage | None:
        result = await db.execute(
            select(AssistantProviderUsage).where(
                AssistantProviderUsage.usage_date == _today(),
                AssistantProviderUsage.provider == "openrouter",
                AssistantProviderUsage.model == tier.model,
            )
        )
        return result.scalar_one_or_none()

    async def reserve(self, db: Any, tier: TierSpec) -> bool:
        """Atomically consume one request + token reservation. Single
        UPDATE ... WHERE: concurrent requests cannot overbook. Returns
        False (fail closed to next tier) on contention or DB errors."""
        reserve = _reserve_tokens()
        try:
            stmt = (
                update(AssistantProviderUsage)
                .where(
                    AssistantProviderUsage.usage_date == _today(),
                    AssistantProviderUsage.provider == "openrouter",
                    AssistantProviderUsage.model == tier.model,
                    AssistantProviderUsage.request_count + 1 <= tier.max_requests,
                    AssistantProviderUsage.total_tokens + reserve <= tier.max_tokens,
                )
                .values(
                    request_count=AssistantProviderUsage.request_count + 1,
                    total_tokens=AssistantProviderUsage.total_tokens + reserve,
                    last_request_at=func.now(),
                    updated_at=func.now(),
                )
            )
            result = await db.execute(stmt)
            if result.rowcount:
                await db.commit()
                return True
            # No row yet today (or budget spent): ensure the row exists,
            # then try the guarded UPDATE exactly once.
            if await self._row(db, tier) is None:
                db.add(
                    AssistantProviderUsage(
                        usage_date=_today(),
                        provider="openrouter",
                        model=tier.model,
                        tier=tier.tier,
                    )
                )
                await db.commit()
                result = await db.execute(stmt)
                await db.commit()
                return bool(result.rowcount)
            await db.rollback()
            return False
        except OperationalError:
            await db.rollback()
            return False

    async def reconcile(
        self, db: Any, tier: TierSpec, reserve: int, usage: UsageStats | None
    ) -> None:
        """Replace the conservative reservation with actual provider usage.
        Failures (usage None) release the reservation without counting
        tokens the provider never reported. Single atomic UPDATE with a
        portable CASE clamp (func.greatest is not SQLite-compatible)."""
        actual = usage.total_tokens if usage is not None else 0
        new_total = AssistantProviderUsage.total_tokens - reserve + actual
        values: dict[str, Any] = {
            "total_tokens": case((new_total < 0, 0), else_=new_total),
            "last_request_at": func.now(),
            "updated_at": func.now(),
        }
        if usage is not None:
            values["prompt_tokens"] = AssistantProviderUsage.prompt_tokens + usage.prompt_tokens
            values["completion_tokens"] = (
                AssistantProviderUsage.completion_tokens + usage.completion_tokens
            )
        try:
            stmt = (
                update(AssistantProviderUsage)
                .where(
                    AssistantProviderUsage.usage_date == _today(),
                    AssistantProviderUsage.provider == "openrouter",
                    AssistantProviderUsage.model == tier.model,
                )
                .values(**values)
            )
            await db.execute(stmt)
            await db.commit()
        except OperationalError:
            await db.rollback()

    async def snapshot(self, db: Any) -> list[dict[str, Any]]:
        """Today's counters per tier, for diagnostics. No secrets."""
        result = await db.execute(
            select(AssistantProviderUsage).where(
                AssistantProviderUsage.usage_date == _today(),
                AssistantProviderUsage.provider == "openrouter",
            )
        )
        return [
            {
                "tier": r.tier,
                "model": r.model,
                "requests": r.request_count,
                "prompt_tokens": r.prompt_tokens,
                "completion_tokens": r.completion_tokens,
                "total_tokens": r.total_tokens,
                "last_request_at": r.last_request_at.isoformat() if r.last_request_at else None,
            }
            for r in result.scalars().all()
        ]

    # -- events -----------------------------------------------------------

    def shift(self, from_tier: int | str, to_tier: int | str, reason: str) -> None:
        from telemetry.assistant_metrics import TIER_SHIFTS

        TIER_SHIFTS.labels(from_tier=str(from_tier), to_tier=str(to_tier), reason=reason).inc()
        logger.info(
            "provider.tier_shift", from_tier=str(from_tier), to_tier=str(to_tier), reason=reason
        )


tier_manager = TierManager()
