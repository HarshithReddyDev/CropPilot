"""OpenRouter free-model tier manager tests (§38-39).

Budget shifting, failure failover, reservation atomicity (incl concurrent),
usage accounting (chat + stream), persistence/daily reset, capability
matching, local-only mode. No live provider calls; Ollama fallback is
covered by the router's existing ordered-fallback tests.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any, cast

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import db.session as db_session_mod
from core.config import settings
from db.base import Base
from models.assistant import AssistantProviderUsage
from services.assistant.openrouter_tiers import TierManager, TierSpec, _reserve_tokens, build_tiers, tier_manager
from services.assistant.providers import LLMProvider, OpenAICompatibleProvider, ProviderError
from services.assistant.router import LLMProviderRouter
from services.assistant.types import (
    ChatMessage,
    ProviderChatResult,
    ProviderStatus,
    RequestRequirements,
    UsageStats,
)


# ---------------------------------------------------------------- fixtures


@pytest_asyncio.fixture
async def tdb(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/tiers.db")
    tables = [t for t in Base.metadata.tables.values() if t.name == "assistant_provider_usage"]
    assert len(tables) == 1
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=tables)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def tsession(tdb):
    factory = async_sessionmaker(tdb, expire_on_commit=False)
    async with factory() as session:
        yield session


def _tiers_on(
    monkeypatch,
    t1: str = "alpha/a:free",
    t2: str = "beta/b:free",
    t3: str = "",
    max_requests: int = 5,
    max_tokens: int = 10000,
    tool_calling_1: bool = True,
):
    monkeypatch.setattr(settings, "ASSISTANT_OPENROUTER_TIERING_ENABLED", True)
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(settings, "ASSISTANT_OPENROUTER_TIER_1_MODEL", t1)
    monkeypatch.setattr(settings, "ASSISTANT_OPENROUTER_TIER_1_MAX_REQUESTS", max_requests)
    monkeypatch.setattr(settings, "ASSISTANT_OPENROUTER_TIER_1_MAX_TOKENS", max_tokens)
    monkeypatch.setattr(settings, "ASSISTANT_OPENROUTER_TIER_1_TOOL_CALLING", tool_calling_1)
    monkeypatch.setattr(settings, "ASSISTANT_OPENROUTER_TIER_1_MAX_CONTEXT", 0)
    monkeypatch.setattr(settings, "ASSISTANT_OPENROUTER_TIER_2_MODEL", t2)
    monkeypatch.setattr(settings, "ASSISTANT_OPENROUTER_TIER_2_MAX_REQUESTS", max_requests)
    monkeypatch.setattr(settings, "ASSISTANT_OPENROUTER_TIER_2_MAX_TOKENS", max_tokens)
    monkeypatch.setattr(settings, "ASSISTANT_OPENROUTER_TIER_2_TOOL_CALLING", True)
    monkeypatch.setattr(settings, "ASSISTANT_OPENROUTER_TIER_2_MAX_CONTEXT", 0)
    monkeypatch.setattr(settings, "ASSISTANT_OPENROUTER_TIER_3_MODEL", t3)
    monkeypatch.setattr(settings, "ASSISTANT_OPENROUTER_TIER_3_MAX_REQUESTS", max_requests)
    monkeypatch.setattr(settings, "ASSISTANT_OPENROUTER_TIER_3_MAX_TOKENS", max_tokens)
    monkeypatch.setattr(settings, "ASSISTANT_OPENROUTER_TIER_3_TOOL_CALLING", True)
    monkeypatch.setattr(settings, "ASSISTANT_OPENROUTER_TIER_3_MAX_CONTEXT", 0)
    monkeypatch.setattr(settings, "ASSISTANT_OPENROUTER_TOKEN_RESERVE", 100)


async def _usage_row(session, mgr, tier):
    row = await mgr._row(session, tier)
    assert row is not None
    return row


def _tier(n: int = 1, model: str = "alpha/a:free", max_requests: int = 5, max_tokens: int = 10000) -> TierSpec:
    return TierSpec(tier=n, model=model, max_requests=max_requests, max_tokens=max_tokens,
                    tool_calling=True, max_context=0)


# ---------------------------------------------------------------- registry (§38)


def test_build_tiers_deterministic_order(monkeypatch):
    _tiers_on(monkeypatch, t3="gamma/g:free")
    tiers = build_tiers()
    assert [t.tier for t in tiers] == [1, 2, 3]
    assert tiers[0].model == "alpha/a:free"


def test_build_tiers_rejects_paid_model(monkeypatch):
    _tiers_on(monkeypatch, t1="alpha/a")  # no :free suffix
    tiers = build_tiers()
    assert [t.tier for t in tiers] == [2]
    assert all(t.model.endswith(":free") for t in tiers)


def test_build_tiers_empty_means_disabled(monkeypatch):
    _tiers_on(monkeypatch, t1="", t2="")
    assert build_tiers() == []


def test_eligible_skips_non_tool_tier_for_tool_request():
    mgr = TierManager()
    tier = TierSpec(tier=1, model="x:free", max_requests=5, max_tokens=100,
                    tool_calling=False, max_context=0)
    ok, reason = mgr.eligible(tier, RequestRequirements(function_calling=True))
    assert (ok, reason) == (False, "capability_mismatch")
    ok, _ = mgr.eligible(tier, RequestRequirements())
    assert ok is True


def test_eligible_skips_vision_and_structured():
    mgr = TierManager()
    tier = _tier()
    assert mgr.eligible(tier, RequestRequirements(vision=True))[0] is False
    assert mgr.eligible(tier, RequestRequirements(structured_output=True))[0] is False


# ---------------------------------------------------------------- budgets (§38)


async def test_reserve_then_reconcile_actual(tsession):
    mgr = TierManager()
    tier = _tier()
    reserve = _reserve_tokens()
    assert await mgr.reserve(tsession, tier) is True
    row = await _usage_row(tsession, mgr, tier)
    assert row.request_count == 1 and row.total_tokens == reserve  # reservation held
    await mgr.reconcile(tsession, tier, reserve, UsageStats(prompt_tokens=10, completion_tokens=5, total_tokens=15))
    row = await _usage_row(tsession, mgr, tier)
    assert (row.prompt_tokens, row.completion_tokens, row.total_tokens) == (10, 5, 15)
    assert row.request_count == 1


async def test_request_budget_exhaustion(tsession):
    mgr = TierManager()
    tier = _tier(max_requests=2)
    assert await mgr.reserve(tsession, tier) is True
    await mgr.reconcile(tsession, tier, 100, UsageStats(prompt_tokens=1, completion_tokens=1, total_tokens=2))
    assert await mgr.reserve(tsession, tier) is True
    await mgr.reconcile(tsession, tier, 100, UsageStats(prompt_tokens=1, completion_tokens=1, total_tokens=2))
    assert await mgr.reserve(tsession, tier) is False


async def test_token_budget_exhaustion(tsession):
    reserve = _reserve_tokens()
    mgr = TierManager()
    tier = _tier(max_tokens=reserve + 50)
    assert await mgr.reserve(tsession, tier) is True
    await mgr.reconcile(tsession, tier, reserve,
                        UsageStats(prompt_tokens=60, completion_tokens=0, total_tokens=60))
    # 60 used + reserve > max -> exhausted
    assert await mgr.reserve(tsession, tier) is False


async def test_failed_request_releases_reservation(tsession):
    mgr = TierManager()
    tier = _tier()
    reserve = _reserve_tokens()
    assert await mgr.reserve(tsession, tier) is True
    await mgr.reconcile(tsession, tier, reserve, None)
    row = await _usage_row(tsession, mgr, tier)
    assert row.total_tokens == 0
    assert row.request_count == 1  # request happened; tokens not counted


async def test_daily_bucket_resets(tsession):
    mgr = TierManager()
    tier = _tier(max_requests=1)
    yesterday = datetime.now(timezone.utc).date() - timedelta(days=1)
    tsession.add(AssistantProviderUsage(
        usage_date=yesterday, provider="openrouter", model=tier.model,
        tier=1, request_count=99, total_tokens=999999,
    ))
    await tsession.commit()
    assert await mgr.reserve(tsession, tier) is True  # fresh bucket today


async def test_concurrent_reserves_never_overbook(tdb):
    """8 racers, 3 request budget: accepted <= 3, counters consistent."""
    mgr = TierManager()
    tier = _tier(max_requests=3)
    factory = async_sessionmaker(tdb, expire_on_commit=False)

    async def one():
        async with factory() as s:
            return await mgr.reserve(s, tier)

    results = await asyncio.gather(*[one() for _ in range(8)])
    accepted = sum(1 for r in results if r)
    assert 1 <= accepted <= 3
    async with factory() as s:
        row = await _usage_row(s, mgr, tier)
        assert row.request_count == accepted
        assert row.total_tokens == accepted * _reserve_tokens()
        assert row.total_tokens >= 0


# ---------------------------------------------------------------- usage (§38)


def test_usage_from_openrouter_shapes():
    u = UsageStats.from_openrouter({"prompt_tokens": 10, "completion_tokens": 4, "total_tokens": 14})
    assert u is not None
    assert (u.prompt_tokens, u.completion_tokens, u.total_tokens) == (10, 4, 14)
    assert UsageStats.from_openrouter(None) is None
    assert UsageStats.from_openrouter({"prompt_tokens": -1}) is None
    assert UsageStats.from_openrouter("nope") is None
    # total derived when absent
    u2 = UsageStats.from_openrouter({"prompt_tokens": 5, "completion_tokens": 5})
    assert u2 is not None and u2.total_tokens == 10


async def test_chat_usage_parsed_and_error_mapping(monkeypatch):
    import services.assistant.providers as providers_mod

    providers_mod._SHARED_CLIENT = None

    class Resp:
        def __init__(self, status, payload=None):
            self.status_code = status
            self._payload = payload or {}

        def json(self):
            return self._payload

    class Client:
        def __init__(self, resp):
            self._resp = resp

        async def post(self, *a, **k):
            return self._resp

    p = OpenAICompatibleProvider("t", "http://x/v1", "m")
    monkeypatch.setattr(providers_mod, "_SHARED_CLIENT", Client(
        Resp(200, {"choices": [{"message": {"content": "hi"}}],
                     "usage": {"prompt_tokens": 7, "completion_tokens": 3, "total_tokens": 10}})))
    result = await p.chat([ChatMessage(role="user", content="yo")])
    assert result.usage is not None and result.usage.total_tokens == 10

    for status, expect in ((402, ProviderStatus.QUOTA_EXHAUSTED),
                           (404, ProviderStatus.MODEL_NOT_FOUND),
                           (400, ProviderStatus.INVALID_REQUEST),
                           (429, ProviderStatus.RATE_LIMITED)):
        monkeypatch.setattr(providers_mod, "_SHARED_CLIENT", Client(Resp(status)))
        try:
            await p.chat([ChatMessage(role="user", content="yo")])
            raise AssertionError(f"{status} should raise")
        except ProviderError as e:
            assert e.status == expect, (status, e.status)


async def test_stream_usage_chunk_captured(monkeypatch):
    import json as _json

    import services.assistant.providers as providers_mod

    providers_mod._SHARED_CLIENT = None
    lines = [
        'data: {"choices": [{"delta": {"content": "hel"}}]}',
        'data: {"choices": [{"delta": {}}], "usage": {"prompt_tokens": 20, "completion_tokens": 2, "total_tokens": 22}}',
        "data: [DONE]",
    ]

    class StreamResp:
        status_code = 200

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def aiter_lines(self):
            for line in lines:
                yield line

    class Client:
        def stream(self, *a, **k):
            return StreamResp()

    p = OpenAICompatibleProvider("t", "http://x/v1", "m")
    monkeypatch.setattr(providers_mod, "_SHARED_CLIENT", Client())
    seen: list[UsageStats] = []
    deltas = [d async for d in p.stream(
        [ChatMessage(role="user", content="yo")], on_usage=seen.append)]
    assert deltas == ["hel"]
    assert len(seen) == 1 and seen[0].total_tokens == 22


# ---------------------------------------------------------------- routing (§38)


class _TierFake:
    """Scripted per-tier provider. Each step is a dict:
    {"ok": True, "text": ..., "usage": ...} or {"ok": False, "status": ...}."""

    def __init__(self, steps: list[dict[str, Any]]):
        self._steps = list(steps)
        self.calls = 0

    async def chat(self, messages, tools=None, timeout=60, tool_choice=None):
        self.calls += 1
        step = self._steps.pop(0) if self._steps else {"ok": True, "text": "default", "usage": None}
        if not step.get("ok", True):
            status = step.get("status", ProviderStatus.UNAVAILABLE)
            raise ProviderError(f"fake {status}", status)
        return ProviderChatResult(
            message=ChatMessage(role="assistant", content=str(step.get("text", ""))),
            model="fake-model", provider="openrouter", usage=step.get("usage"),
        )

    async def stream(self, messages, tools=None, timeout=60, on_usage=None):
        self.calls += 1
        if on_usage is not None:
            on_usage(UsageStats(prompt_tokens=9, completion_tokens=1, total_tokens=10))
        yield "streamed"


def _router_with_tiers(monkeypatch, tdb, fakes: dict[str, _TierFake]):
    monkeypatch.setattr(db_session_mod, "async_session_factory",
                        async_sessionmaker(tdb, expire_on_commit=False))
    router = LLMProviderRouter.__new__(LLMProviderRouter)
    router._providers = cast("dict[str, LLMProvider]", {"openrouter": None, "ollama": None})
    router._cooldown_until = {}
    router._failures = {}
    router._ollama_ready = False
    router._ollama_ready_at = None
    monkeypatch.setattr(router, "_tier_provider", lambda tier: fakes[tier.model])
    return router


def _span():
    return SimpleNamespace(set_attribute=lambda *a: None)


async def test_tier1_selected_and_accounted(monkeypatch, tdb):
    _tiers_on(monkeypatch)
    fakes = {"alpha/a:free": _TierFake([{"ok": True, "text": "t1 answer",
                                           "usage": UsageStats(prompt_tokens=30, completion_tokens=10,
                                                               total_tokens=40)}]),
             "beta/b:free": _TierFake([])}
    router = _router_with_tiers(monkeypatch, tdb, fakes)
    result = await router._chat_openrouter_tiers(
        [ChatMessage(role="user", content="hi")], None, RequestRequirements(), None,
        _span(), [], [])
    assert result.message.content == "t1 answer"
    assert result.model == "fake-model"
    factory = async_sessionmaker(tdb, expire_on_commit=False)
    async with factory() as s:
        row = (await s.execute(select(AssistantProviderUsage))).scalars().all()
        assert len(row) == 1 and row[0].total_tokens == 40


async def test_budget_exhaustion_shifts_to_tier2(monkeypatch, tdb):
    _tiers_on(monkeypatch, max_requests=1)
    mgr = TierManager()
    factory = async_sessionmaker(tdb, expire_on_commit=False)
    async with factory() as s:
        assert await mgr.reserve(s, _tier()) is True  # consume tier 1 budget
    fakes = {"alpha/a:free": _TierFake([]),
             "beta/b:free": _TierFake([{"ok": True, "text": "t2 answer", "usage": None}])}
    router = _router_with_tiers(monkeypatch, tdb, fakes)
    result = await router._chat_openrouter_tiers(
        [ChatMessage(role="user", content="hi")], None, RequestRequirements(), None,
        _span(), [], [])
    assert result.message.content == "t2 answer"
    assert fakes["alpha/a:free"].calls == 0


async def test_429_shifts_to_next_tier(monkeypatch, tdb):
    _tiers_on(monkeypatch)
    fakes = {"alpha/a:free": _TierFake([{"ok": False, "status": ProviderStatus.RATE_LIMITED}]),
             "beta/b:free": _TierFake([{"ok": True, "text": "t2 after 429", "usage": None}])}
    router = _router_with_tiers(monkeypatch, tdb, fakes)
    result = await router._chat_openrouter_tiers(
        [ChatMessage(role="user", content="hi")], None, RequestRequirements(), None,
        _span(), [], [])
    assert result.message.content == "t2 after 429"


async def test_model_not_found_disables_tier(monkeypatch, tdb):
    _tiers_on(monkeypatch)
    tier_manager.reset_runtime_state()
    fakes = {"alpha/a:free": _TierFake([{"ok": False, "status": ProviderStatus.MODEL_NOT_FOUND}]),
             "beta/b:free": _TierFake([{"ok": True, "text": "t2", "usage": None}])}
    router = _router_with_tiers(monkeypatch, tdb, fakes)
    errors: list[str] = []
    await router._chat_openrouter_tiers(
        [ChatMessage(role="user", content="hi")], None, RequestRequirements(), None,
        _span(), [], errors)
    # second turn: tier 1 never attempted again
    await router._chat_openrouter_tiers(
        [ChatMessage(role="user", content="hi"), ChatMessage(role="assistant", content="t2")],
        None, RequestRequirements(), None, _span(), [], errors)
    assert fakes["alpha/a:free"].calls == 1
    assert fakes["beta/b:free"].calls == 2
    tier_manager.reset_runtime_state()


async def test_invalid_request_never_retried(monkeypatch, tdb):
    _tiers_on(monkeypatch)
    fakes = {"alpha/a:free": _TierFake([{"ok": False, "status": ProviderStatus.INVALID_REQUEST}]),
             "beta/b:free": _TierFake([])}
    router = _router_with_tiers(monkeypatch, tdb, fakes)
    try:
        await router._chat_openrouter_tiers(
            [ChatMessage(role="user", content="hi")], None, RequestRequirements(), None,
            _span(), [], [])
        raise AssertionError("must propagate")
    except ProviderError as e:
        assert e.status == ProviderStatus.INVALID_REQUEST
    assert fakes["beta/b:free"].calls == 0


async def test_auth_error_aborts_tier_loop(monkeypatch, tdb):
    _tiers_on(monkeypatch)
    fakes = {"alpha/a:free": _TierFake([{"ok": False, "status": ProviderStatus.MISCONFIGURED}]),
             "beta/b:free": _TierFake([])}
    router = _router_with_tiers(monkeypatch, tdb, fakes)
    errors: list[str] = []
    try:
        await router._chat_openrouter_tiers(
            [ChatMessage(role="user", content="hi")], None, RequestRequirements(), None,
            _span(), [], errors)
        raise AssertionError("must raise exhausted")
    except ProviderError as e:
        assert e.status == ProviderStatus.UNAVAILABLE
    assert fakes["beta/b:free"].calls == 0  # same broken key everywhere
    assert any("openrouter:t1" in x for x in errors)


async def test_capability_mismatch_skips_tier(monkeypatch, tdb):
    _tiers_on(monkeypatch, tool_calling_1=False)
    fakes = {"alpha/a:free": _TierFake([]),
             "beta/b:free": _TierFake([{"ok": True, "text": "t2 tools", "usage": None}])}
    router = _router_with_tiers(monkeypatch, tdb, fakes)
    result = await router._chat_openrouter_tiers(
        [ChatMessage(role="user", content="price?")],
        [{"type": "function", "function": {"name": "market_latest"}}],
        RequestRequirements(function_calling=True), "required",
        _span(), [], [])
    assert result.message.content == "t2 tools"
    assert fakes["alpha/a:free"].calls == 0


async def test_stream_tier_reconciles_usage(monkeypatch, tdb):
    _tiers_on(monkeypatch)
    fakes = {"alpha/a:free": _TierFake([]), "beta/b:free": _TierFake([])}
    router = _router_with_tiers(monkeypatch, tdb, fakes)
    errors: list[str] = []
    deltas = [d async for d in router._stream_openrouter_tiers(
        [ChatMessage(role="user", content="hi")], None, RequestRequirements(), errors)]
    assert deltas and deltas[0][0] == "openrouter" and deltas[0][1] == "alpha/a:free"
    factory = async_sessionmaker(tdb, expire_on_commit=False)
    async with factory() as s:
        rows = (await s.execute(select(AssistantProviderUsage))).scalars().all()
        assert len(rows) == 1 and rows[0].total_tokens == 10


async def test_local_only_mode_disables_tiering(monkeypatch):
    monkeypatch.setattr(settings, "ASSISTANT_OPENROUTER_TIERING_ENABLED", False)
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "")
    router = LLMProviderRouter.__new__(LLMProviderRouter)
    router._providers = cast("dict[str, LLMProvider]", {"ollama": None})
    router._cooldown_until = {}
    router._failures = {}
    router._ollama_ready = False
    router._ollama_ready_at = None
    assert router._tiering_active() is False


async def test_snapshot_shape_for_diagnostics(tsession):
    mgr = TierManager()
    tier = _tier()
    assert await mgr.reserve(tsession, tier) is True
    snap = await mgr.snapshot(tsession)
    assert len(snap) == 1
    assert snap[0]["model"] == tier.model and snap[0]["requests"] == 1
    assert "last_request_at" in snap[0]


def test_tiering_registers_leg_without_legacy_model(monkeypatch):
    """Tiering + key + tiers but no legacy OPENROUTER_MODEL still puts
    openrouter in the router order (live bug: tier path never ran)."""
    _tiers_on(monkeypatch)
    monkeypatch.setattr(settings, "OPENROUTER_MODEL", "")
    monkeypatch.setattr(settings, "ASSISTANT_PROVIDER_ORDER", "openrouter,ollama")
    router = LLMProviderRouter()
    assert "openrouter" in router.order
    leg = router._providers["openrouter"]
    assert leg.model_name() == "alpha/a:free"
    assert router._tiering_active() is True


def test_no_key_no_leg_even_with_tiers(monkeypatch):
    _tiers_on(monkeypatch)
    monkeypatch.setattr(settings, "OPENROUTER_MODEL", "")
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "")
    router = LLMProviderRouter()
    assert "openrouter" not in router.order
    assert router._tiering_active() is False
