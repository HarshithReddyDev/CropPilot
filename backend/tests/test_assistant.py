"""Phase 8: assistant unit + integration tests.

Runs on sqlite with assistant tables only (full-metadata create_all is
broken on sqlite pre-existing: weather_forecasts.forecast_data raw JSONB).
"""

from __future__ import annotations

import base64
from collections.abc import AsyncIterator
from typing import Any
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from core.config import settings
from db.base import Base
from models.assistant import (
    AssistantConversation,
    AssistantMemory,
    AssistantMessage,
)
from services.assistant.providers import LLMProvider, ProviderError
from services.assistant.router import LLMProviderRouter
from services.assistant.types import (
    ChatMessage,
    ProviderCapabilities,
    ProviderChatResult,
    ProviderHealth,
    ProviderStatus,
)


# ---------------------------------------------------------------- fixtures


@pytest_asyncio.fixture
async def adb(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/a.db")
    tables = [t for t in Base.metadata.tables.values() if t.name.startswith("assistant_")]
    assert len(tables) == 4
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=tables)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def asession(adb):
    factory = async_sessionmaker(adb, expire_on_commit=False)
    async with factory() as session:
        yield session


class _Stub(LLMProvider):
    def __init__(self, pname: str, fail: ProviderStatus | None = None, text: str = "stub answer"):
        self._pname = pname
        self._fail = fail
        self._text = text
        self.calls = 0

    def name(self) -> str:
        return self._pname

    def model_name(self) -> str:
        return "stub-model"

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities()

    async def chat(
        self,
        messages: list[ChatMessage],
        tools: list[dict[str, Any]] | None = None,
        timeout: int = 60,
        tool_choice: str | None = None,
    ) -> ProviderChatResult:
        self.calls += 1
        if self._fail is not None:
            raise ProviderError("stub down", self._fail)
        return ProviderChatResult(
            message=ChatMessage(role="assistant", content=self._text),
            model="stub-model",
            provider=self._pname,
        )

    def stream(
        self,
        messages: list[ChatMessage],
        tools: list[dict[str, Any]] | None = None,
        timeout: int = 60,
        on_usage: Any = None,
    ) -> AsyncIterator[str]:
        return self._gen()

    async def _gen(self) -> AsyncIterator[str]:
        yield self._text

    async def health(self) -> ProviderHealth:
        return ProviderHealth(name=self._pname, model="stub-model", status=ProviderStatus.UNAVAILABLE)


def _router_with(stubs: dict[str, _Stub]) -> LLMProviderRouter:
    router = LLMProviderRouter()
    router._providers = dict(stubs)
    router._cooldown_until = {}
    router._failures = {}
    return router


# ---------------------------------------------------------------- router


async def test_router_order_honors_settings(monkeypatch):
    monkeypatch.setattr(settings, "ASSISTANT_PROVIDER_ORDER", "b,a")
    router = _router_with({"a": _Stub("a"), "b": _Stub("b")})
    assert router.order == ["b", "a"]


async def test_router_falls_forward_on_failure(monkeypatch):
    monkeypatch.setattr(settings, "ASSISTANT_PROVIDER_ORDER", "bad,good")
    router = _router_with(
        {"bad": _Stub("bad", fail=ProviderStatus.UNAVAILABLE), "good": _Stub("good")}
    )
    result = await router.chat([ChatMessage(role="user", content="hi")])
    assert result.provider == "good"
    assert result.message.content == "stub answer"


async def test_router_cools_down_rate_limited(monkeypatch):
    monkeypatch.setattr(settings, "ASSISTANT_PROVIDER_ORDER", "flaky,good")
    monkeypatch.setattr(settings, "ASSISTANT_PROVIDER_COOLDOWN_SECONDS", 300)
    flaky, good = _Stub("flaky", fail=ProviderStatus.RATE_LIMITED), _Stub("good")
    router = _router_with({"flaky": flaky, "good": good})
    first = await router.chat([ChatMessage(role="user", content="hi")])
    assert first.provider == "good"
    second = await router.chat([ChatMessage(role="user", content="hi")])
    assert second.provider == "good"
    # flaky hit once then cooled: good served both turns.
    assert flaky.calls == 1
    assert good.calls == 2


# ---------------------------------------------------------------- tools registry


async def test_unknown_tool_rejected():
    from services.assistant.tools_definitions import assistant_tools  # noqa: F401

    from services.assistant.tools_registry import tool_registry

    result, event = await tool_registry.execute("no_such_tool", {}, {})
    assert "error" in result
    assert event.status == "failed"


async def test_crop_profit_math():
    from services.assistant.tools_definitions import assistant_tools  # noqa: F401

    from services.assistant.tools_registry import tool_registry

    result, event = await tool_registry.execute(
        "crop_profit",
        {
            "crop": "wheat",
            "area_hectares": 2.0,
            "expected_yield_per_hectare": 40.0,
            "market_price_per_quintal": 2400.0,
            "cost_per_hectare": 30000.0,
        },
        {},
    )
    assert event.status == "succeeded"
    # revenue 2*40*2400=192000, cost 60000, profit 132000.
    assert result["profit_rs"] == 132000.0


async def test_tool_schema_rejects_missing_args():
    from services.assistant.tools_definitions import assistant_tools  # noqa: F401

    from services.assistant.tools_registry import tool_registry

    result, event = await tool_registry.execute("crop_profit", {"crop": "wheat"}, {})
    assert "error" in result
    assert event.status == "failed"


async def test_disease_log_requires_user():
    from services.assistant.tools_definitions import assistant_tools  # noqa: F401

    from services.assistant.tools_registry import tool_registry

    result, event = await tool_registry.execute(
        "disease_log_summary", {"log_id": str(uuid4())}, {}
    )
    # Graceful denial (not a tool failure): anonymous callers get ok=False.
    assert result["ok"] is False
    assert "sign in" in result["error"]


# ---------------------------------------------------------------- UI actions


def test_ui_actions_allow_list_and_scrub():
    from typing import Any, cast

    from services.assistant.ui_actions import allowed_actions, validate_ui_actions

    assert "apply-market-filters" in allowed_actions()
    raw = cast(
        Any,
        [
            {"action": "apply-market-filters", "payload": {"state": "Telangana", "bogus": 1}},
            {"action": "evil-action", "payload": {}},
            {"action": "open-market", "payload": {}},
            "not-a-dict",
            {"action": "follow-market", "payload": {"deep": {"nested": True}}},
        ],
    )
    out = validate_ui_actions(raw)
    assert len(out) == 1
    assert out[0].action == "apply-market-filters"
    assert out[0].payload == {"state": "Telangana"}


# ---------------------------------------------------------------- retrieval


async def test_retrieval_reranks_exact_name_top(monkeypatch):
    from rag.pipeline import rag_pipeline

    import services.assistant.retrieval as retrieval

    async def fake_search(query: str, state_jurisdiction: str | None = None, top_k: int = 5):
        return [
            {"content": "Crop Insurance Scheme unrelated text", "metadata": {"scheme_name": "Other"}, "score": 0.99},
            {"content": "PM-KISAN income support farmer benefit", "metadata": {"scheme_name": "PM-KISAN"}, "score": 0.5},
        ]

    monkeypatch.setattr(rag_pipeline, "hybrid_search_schemes", fake_search)
    text, citations = await retrieval.retrieve_schemes("PM-KISAN benefits", state="Telangana")
    assert "PM-KISAN" in text
    assert citations and citations[0].title == "PM-KISAN"


# ---------------------------------------------------------------- voice frames


def test_decode_audio_chunk_roundtrip():
    from services.assistant.voice import SAMPLE_RATE, decode_audio_chunk

    raw = b"\x01\x02" * 800  # 1600 bytes PCM16
    encoded = base64.b64encode(raw).decode("ascii")
    assert decode_audio_chunk(encoded, SAMPLE_RATE) == raw


def test_decode_audio_chunk_rejects():
    import pytest as _pytest

    from services.assistant.voice import decode_audio_chunk

    with _pytest.raises(ValueError):
        decode_audio_chunk("!!!not-base64!!!", 16000)
    with _pytest.raises(ValueError):
        decode_audio_chunk(base64.b64encode(b"\x00\x01").decode(), 8000)
    with _pytest.raises(ValueError):
        decode_audio_chunk("x" * 6000, 16000)


# ---------------------------------------------------------------- metrics


def test_metrics_counters_exist():
    from telemetry.assistant_metrics import (
        CHAT_TOTAL,
        FEEDBACK,
        PROVIDER_COOLDOWN,
        RAG_FALLBACK,
        STT_ERRORS,
        TOOL_CALLS,
        TTS_ERRORS,
    )

    CHAT_TOTAL.labels(provider="test", status="ok").inc()
    TOOL_CALLS.labels(tool="crop_profit", status="succeeded").inc()
    RAG_FALLBACK.labels(reason="vector_error").inc()
    PROVIDER_COOLDOWN.labels(provider="test").inc()
    STT_ERRORS.labels(engine="disabled").inc()
    TTS_ERRORS.labels(engine="disabled").inc()
    FEEDBACK.labels(rating="up").inc()
    assert CHAT_TOTAL.labels(provider="test", status="ok")._value.get() == 1


# ---------------------------------------------------------------- memory


async def test_memory_conversation_roundtrip(asession):
    from services.assistant.memory import (
        append_message,
        get_memory,
        get_or_create_conversation,
        list_conversations,
        recent_history,
        set_memory,
    )

    user_id = uuid4()
    conv = await get_or_create_conversation(asession, user_id, None)
    await asession.commit()
    # Explicit stamps: same-transaction DB now() ties have no defined order.
    from datetime import datetime, timedelta

    base = datetime(2026, 1, 1, 12, 0, 0)
    await append_message(asession, conv.id, "user", "hello", created_at=base)
    await append_message(
        asession, conv.id, "assistant", "hi there", created_at=base + timedelta(seconds=1)
    )
    await asession.commit()

    history = await recent_history(asession, conv.id)
    assert [h["role"] for h in history] == ["user", "assistant"]
    assert history[0]["content"] == "hello"

    # Ownership mismatch yields a fresh conversation, never someone else's.
    other = await get_or_create_conversation(asession, uuid4(), uuid4())
    assert other.id != conv.id

    await set_memory(asession, f"user:{user_id}", "state", {"value": "Telangana"})
    await asession.commit()
    row = await get_memory(asession, f"user:{user_id}", "state")
    assert row == {"value": "Telangana"}

    convs = await list_conversations(asession, user_id)
    assert len(convs) == 1


# ---------------------------------------------------------------- endpoints


@pytest_asyncio.fixture
async def api_client(adb, monkeypatch):
    from core.dependencies import get_db
    from main import app

    async def fake_run_agent(message, context, language="en", history=None):
        return {
            "text": "canned answer",
            "provider": {"name": "test", "model": "stub"},
            "citations": [],
            "ui_actions": [],
            "tool_events": [],
        }

    monkeypatch.setattr("services.assistant.service.run_agent", fake_run_agent)

    factory = async_sessionmaker(adb, expire_on_commit=False)

    async def override_get_db():
        async with factory() as session:
            yield session
            await session.commit()

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


async def test_chat_persists_conversation(api_client):
    body = {"message": "hello", "language": "en"}
    first = await api_client.post("/api/v1/assistant/chat", json=body)
    assert first.status_code == 200, first.text
    data = first.json()
    assert data["text"] == "canned answer"
    cid = data["conversation_id"]
    assert cid

    second = await api_client.post(
        "/api/v1/assistant/chat", json={**body, "conversation_id": cid}
    )
    assert second.status_code == 200
    assert second.json()["conversation_id"] == cid

    listing = await api_client.get("/api/v1/assistant/conversations")
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    detail = await api_client.get(f"/api/v1/assistant/conversations/{cid}")
    assert detail.status_code == 200
    roles = [m["role"] for m in detail.json()]
    assert roles == ["user", "assistant", "user", "assistant"]

    feedback = await api_client.post(
        "/api/v1/assistant/feedback",
        json={"conversation_id": cid, "rating": "up"},
    )
    assert feedback.status_code == 204


async def test_chat_stream_sse_final_has_conversation(api_client):
    import json

    event_names: list[str] = []
    finals: list[dict] = []
    async with api_client.stream(
        "POST", "/api/v1/assistant/chat/stream", json={"message": "hi"}
    ) as response:
        assert response.status_code == 200
        async for line in response.aiter_lines():
            if line.startswith("event:"):
                event_names.append(line[6:].strip())
            elif line.startswith("data:") and event_names and event_names[-1] == "final":
                finals.append(json.loads(line[5:].strip()))
    assert "final" in event_names
    assert finals and finals[0]["conversation_id"]


async def test_capabilities_lists_tools_and_actions(api_client):
    response = await api_client.get("/api/v1/assistant/capabilities")
    assert response.status_code == 200
    data = response.json()
    assert "crop_profit" in [t["name"] for t in data["tools"]]
    assert "apply-market-filters" in data["ui_actions"]


async def test_chat_survives_store_failure(api_client, monkeypatch):
    """Persistence is best-effort: a broken transcript store (e.g. typed-UUID
    DataError on postgres) must not 500 the turn — session rolled back,
    turn proceeds stateless."""

    async def boom(*args, **kwargs):
        raise RuntimeError("store down")

    monkeypatch.setattr(
        "api.v1.endpoints.assistant.assistant_memory.get_or_create_conversation",
        boom,
    )
    response = await api_client.post(
        "/api/v1/assistant/chat", json={"message": "hi", "language": "en"}
    )
    assert response.status_code == 200, response.text
    assert response.json()["text"] == "canned answer"


# ---------------------------------------------------------------- agent


class _ScriptRouter:
    """Router stub replaying canned ProviderChatResults in order."""

    def __init__(self, script: list):
        self._script = script
        self.calls = 0

    async def chat(self, messages, tools=None, requirements=None, tool_choice=None):
        result = self._script[min(self.calls, len(self._script) - 1)]
        self.calls += 1
        return result


def _assistant_text_result(text: str):
    return ProviderChatResult(
        message=ChatMessage(role="assistant", content=text),
        model="stub-model",
        provider="stub",
    )


def _tool_call_result(name: str, arguments: dict):
    from services.assistant.types import ChatToolCall

    return ProviderChatResult(
        message=ChatMessage(
            role="assistant",
            content="",
            tool_calls=[ChatToolCall(id="c1", name=name, arguments=arguments)],
        ),
        model="stub-model",
        provider="stub",
    )


async def test_run_agent_tool_then_answer(monkeypatch):
    from services.assistant.tools_definitions import assistant_tools  # noqa: F401

    import services.assistant.agent as agent_mod

    profit_args = {
        "crop": "wheat",
        "area_hectares": 1.0,
        "expected_yield_per_hectare": 40.0,
        "market_price_per_quintal": 2400.0,
        "cost_per_hectare": 30000.0,
    }
    script_router = _ScriptRouter(
        [_tool_call_result("crop_profit", profit_args), _assistant_text_result("done")]
    )
    monkeypatch.setattr(agent_mod, "router", script_router)
    result = await agent_mod.run_agent("profit?", context={})
    assert result["text"] == "done"
    assert result["provider"] == {"name": "stub", "model": "stub-model"}
    assert len(result["tool_events"]) == 1


async def test_run_agent_bounded_steps(monkeypatch):
    from services.assistant.tools_definitions import assistant_tools  # noqa: F401

    import services.assistant.agent as agent_mod

    script_router = _ScriptRouter(
        [_tool_call_result("crop_profit", {"crop": "w", "area_hectares": 0,
                                           "expected_yield_per_hectare": 0,
                                           "market_price_per_quintal": 0,
                                           "cost_per_hectare": 0})]
    )
    monkeypatch.setattr(agent_mod, "router", script_router)
    monkeypatch.setattr(settings, "ASSISTANT_MAX_TOOL_STEPS", 2)
    result = await agent_mod.run_agent("loop?", context={})
    assert len(result["tool_events"]) == 2
    assert result["text"] == ""


def test_looks_factual_covers_golden_queries():
    """Step-0 force heuristic must fire for every factual golden query."""
    import services.assistant.agent as agent_mod

    factual = [
        "Paddy price in Nalgonda today?",
        "Cotton modal price trend last 30 days in Telangana?",
        "Compare wheat prices across mandis",
        "Market overview for Telangana",
        "వరంగల్‌లో మొక్కజొన్న ధర?",
        "Current weather for my plot?",
        "5-day forecast, should I spray?",
        "Which schemes am I eligible for?",
        "PM-KISAN benefits?",
        "List Telangana state schemes",
        "रायथु बंधु योजना क्या है?",
        "Summarize my latest disease report",
        "Profit for 2ha paddy at current prices?",
        "నా పంటకు లాభం ఎంత?",
        "Chilli prices Adilabad vs Khammam?",
        "Maize arrivals this week?",
        "Is it going to rain tomorrow?",
        "Crop insurance schemes?",
    ]
    for q in factual:
        assert agent_mod._looks_factual(q), q
    for q in ["Hello, what can you do?", "నమస్తే, సహాయం కావాలి", "hello"]:
        assert not agent_mod._looks_factual(q), q


def test_agent_truncate_and_prepare():
    import services.assistant.agent as agent_mod

    assert agent_mod._truncate("abc") == "abc"
    assert agent_mod._truncate("x" * 5000).endswith("...[truncated]")
    state = agent_mod.prepare_input(
        {"messages": [{"role": "user", "content": "hi"}],
         "steps": 0, "tool_events": [], "citations": [],
         "ui_actions": [], "language": "en", "route": "",
         "provider_name": "", "provider_model": "", "overlap_retried": False}
    )
    # prepare emits counters only; run_agent prepends the system prompt so
    # add_messages never reorders to [user, system].
    assert "messages" not in state
    assert state["steps"] == 0
    # human/ai role aliases map to user/assistant.
    mapped = agent_mod._to_provider_messages(
        [{"role": "human", "content": "a"}, {"role": "ai", "content": "b"}]
    )
    assert [m.role for m in mapped] == ["user", "assistant"]


# ---------------------------------------------------------------- providers


class _FakeHTTPResp:
    def __init__(self, status_code: int = 200, payload: dict | None = None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise ValueError(f"http {self.status_code}")


class _FakeHTTPClient:
    def __init__(self, resp: _FakeHTTPResp | None = None, exc: Exception | None = None):
        self._resp = resp or _FakeHTTPResp()
        self._exc = exc

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, *args, **kwargs):
        if self._exc is not None:
            raise self._exc
        return self._resp

    async def get(self, *args, **kwargs):
        if self._exc is not None:
            raise self._exc
        return self._resp


def _patch_http(monkeypatch, resp=None, exc=None):
    import httpx

    import services.assistant.providers as providers_mod

    providers_mod._SHARED_CLIENT = None  # singleton must honor this test's patch
    monkeypatch.setattr(
        httpx, "AsyncClient", lambda *args, **kwargs: _FakeHTTPClient(resp, exc)
    )


def _ok_chat_payload(text="hello"):
    return {"choices": [{"message": {"content": text}}]}


async def test_provider_chat_text_and_tool_calls(monkeypatch):
    import services.assistant.providers as providers_mod
    from services.assistant.providers import OpenAICompatibleProvider

    provider = OpenAICompatibleProvider("test", "http://x/v1", "m")
    _patch_http(monkeypatch, _FakeHTTPResp(200, _ok_chat_payload("hi")))
    result = await provider.chat([ChatMessage(role="user", content="yo")])
    assert result.message.content == "hi"

    tool_payload = {
        "choices": [{
            "message": {
                "content": "",
                "tool_calls": [{
                    "id": "c1",
                    "function": {
                        "name": "crop_profit",
                        "arguments": '{"crop": "wheat"}',
                    },
                }],
            }
        }]
    }
    _patch_http(monkeypatch, _FakeHTTPResp(200, tool_payload))
    result = await provider.chat([ChatMessage(role="user", content="yo")])
    assert result.message.tool_calls[0].name == "crop_profit"
    assert result.message.tool_calls[0].arguments == {"crop": "wheat"}


async def test_provider_chat_error_mapping(monkeypatch):
    import httpx

    from services.assistant.providers import OpenAICompatibleProvider

    provider = OpenAICompatibleProvider("test", "http://x/v1", "m")
    cases = [
        (_FakeHTTPResp(429), ProviderStatus.RATE_LIMITED),
        (_FakeHTTPResp(401), ProviderStatus.MISCONFIGURED),
        (_FakeHTTPResp(500), ProviderStatus.UNAVAILABLE),
        (_FakeHTTPResp(200, {"nope": True}), ProviderStatus.UNAVAILABLE),
    ]
    for resp, status in cases:
        _patch_http(monkeypatch, resp)
        with pytest.raises(ProviderError) as exc_info:
            await provider.chat([ChatMessage(role="user", content="yo")])
        assert exc_info.value.status == status
    _patch_http(monkeypatch, exc=httpx.TimeoutException("slow"))
    with pytest.raises(ProviderError) as exc_info:
        await provider.chat([ChatMessage(role="user", content="yo")])
    assert exc_info.value.status == ProviderStatus.TIMEOUT
    _patch_http(monkeypatch, exc=httpx.ConnectError("refused"))
    with pytest.raises(ProviderError) as exc_info:
        await provider.chat([ChatMessage(role="user", content="yo")])
    assert exc_info.value.status == ProviderStatus.UNAVAILABLE


async def test_provider_payload_tools_gating():
    from services.assistant.types import ProviderCapabilities
    from services.assistant.providers import OpenAICompatibleProvider

    no_tools = OpenAICompatibleProvider("t", "http://x/v1", "m")
    body = no_tools._payload(
        [ChatMessage(role="user", content="hi")], [{"name": "crop_profit"}], stream=False
    )
    assert "tools" in body  # default capabilities allow function calling

    plain = OpenAICompatibleProvider(
        "t", "http://x/v1", "m",
        capabilities=ProviderCapabilities(function_calling=False),
    )
    body = plain._payload(
        [ChatMessage(role="user", content="hi")], [{"name": "crop_profit"}], stream=False
    )
    assert "tools" not in body


async def test_provider_stream_deltas(monkeypatch):
    import json as _json

    from services.assistant.providers import OpenAICompatibleProvider

    line = "data: " + _json.dumps({"choices": [{"delta": {"content": "hel"}}]})
    line2 = "data: " + _json.dumps({"choices": [{"delta": {"content": "lo"}}]})

    class _StreamResp(_FakeHTTPResp):
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def aiter_lines(self):
            for text in (line, "event: ping", line2, "data: [DONE]"):
                yield text

    class _StreamClient(_FakeHTTPClient):
        def stream(self, *args, **kwargs):
            return _StreamResp(200)

    import httpx

    import services.assistant.providers as providers_mod

    providers_mod._SHARED_CLIENT = None
    monkeypatch.setattr(httpx, "AsyncClient", lambda *args, **kwargs: _StreamClient())
    provider = OpenAICompatibleProvider("test", "http://x/v1", "m")
    out = [d async for d in provider.stream([ChatMessage(role="user", content="hi")])]
    assert out == ["hel", "lo"]


async def test_base_health_ok_and_unreachable(monkeypatch):
    import httpx

    from services.assistant.providers import OpenAICompatibleProvider

    provider = OpenAICompatibleProvider("test", "http://x/v1", "m")
    _patch_http(monkeypatch, _FakeHTTPResp(200, _ok_chat_payload("pong")))
    health = await provider.health()
    assert health.status == ProviderStatus.AVAILABLE

    _patch_http(monkeypatch, exc=httpx.ConnectError("refused"))
    health = await provider.health()
    assert health.status == ProviderStatus.UNAVAILABLE


async def test_ollama_health_reports(monkeypatch):
    import httpx

    from services.assistant.providers import OllamaProvider

    provider = OllamaProvider("http://ollama:11434", "qwen3:8b", "qwen3:4b")
    _patch_http(monkeypatch, exc=httpx.ConnectError("refused"))
    health = await provider.health()
    assert health.status == ProviderStatus.UNAVAILABLE
    assert "Ollama" in health.detail

    _patch_http(monkeypatch, _FakeHTTPResp(200, {"data": [{"id": "other:7b"}]}))
    health = await provider.health()
    assert health.status == ProviderStatus.MISCONFIGURED
    assert "ollama pull qwen3:8b" in health.detail

    _patch_http(monkeypatch, _FakeHTTPResp(200, {"data": [{"id": "qwen3:8b"}]}))
    health = await provider.health()
    assert health.status == ProviderStatus.AVAILABLE


# ---------------------------------------------------------------- voice session


class _FakeWS:
    def __init__(self, inbound: list):
        self._inbound = list(inbound)
        self.sent: list = []
        self.accepted = False
        self.close_code: int | None = None

    async def accept(self):
        self.accepted = True

    async def receive_json(self):
        if not self._inbound:
            raise RuntimeError("client disconnected")
        return self._inbound.pop(0)

    async def send_json(self, payload):
        self.sent.append(payload)

    async def close(self, code: int = 1000):
        self.close_code = code


def _audio_frame() -> dict:
    import base64 as _b64

    return {
        "type": "audio",
        "data": _b64.b64encode(b"\x01\x02" * 800).decode("ascii"),
        "sample_rate": 16000,
    }


async def test_voice_rejects_bad_config():
    from services.assistant.voice import run_session

    ws = _FakeWS([{"type": "hello"}])
    await run_session(ws, user=None)
    assert ws.close_code == 4400


async def test_voice_disabled_path(monkeypatch):
    from services.assistant.voice import run_session

    monkeypatch.setattr(settings, "ASSISTANT_ENABLE_VOICE", False)
    ws = _FakeWS([{"type": "config", "lang": "en"}])
    await run_session(ws, user=None)
    codes = [m.get("code") for m in ws.sent if m.get("type") == "error"]
    assert "voice_disabled" in codes


async def test_voice_commit_asr_unavailable(monkeypatch):
    import services.assistant.voice as voice_mod

    run_session = voice_mod.run_session
    # Force the fail-closed path regardless of host/container engines.
    monkeypatch.setattr(voice_mod, "load_asr", lambda: voice_mod.DisabledASR())
    monkeypatch.setattr(voice_mod, "load_tts", lambda: voice_mod.DisabledTTS())
    assert voice_mod.load_asr().name == "disabled"
    assert voice_mod.load_tts().name == "disabled"
    ws = _FakeWS([{"type": "config", "lang": "en"}, _audio_frame(), {"type": "commit"}])
    await run_session(ws, user=None, default_lang="en")
    kinds = [m.get("type") for m in ws.sent]
    assert "ready" in kinds
    codes = [m.get("code") for m in ws.sent if m.get("type") == "error"]
    assert "asr_unavailable" in codes


async def test_voice_persist_flag_warns_but_continues():
    from services.assistant.voice import run_session

    ws = _FakeWS([{"type": "config", "lang": "en", "persist_audio": True}])
    await run_session(ws, user=None, default_lang="en")
    codes = [m.get("code") for m in ws.sent if m.get("type") == "error"]
    assert "persistence_disabled" in codes
    assert "ready" in [m.get("type") for m in ws.sent]


def test_split_audio_chunks():
    from services.assistant.voice import AUDIO_CHUNK_BYTES, split_audio

    frames = split_audio(b"a" * (AUDIO_CHUNK_BYTES + 10))
    assert len(frames) == 2


async def test_router_stream_falls_forward(monkeypatch):
    from services.assistant.types import ProviderCapabilities

    class _BadStream(_Stub):
        def stream(self, messages, tools=None, timeout=60, on_usage=None):
            return self._fail_gen()

        async def _fail_gen(self):
            raise ProviderError("down", ProviderStatus.UNAVAILABLE)
            yield "never"

    class _NoVision(_Stub):
        def capabilities(self) -> ProviderCapabilities:
            return ProviderCapabilities(function_calling=False)

    monkeypatch.setattr(settings, "ASSISTANT_PROVIDER_ORDER", "bad,good")
    router = _router_with({"bad": _BadStream("bad"), "good": _Stub("good", text="streamed")})
    out = [d async for _, _, d in router.stream([ChatMessage(role="user", content="hi")])]
    assert out == ["streamed"]


async def test_service_disabled_and_failed(monkeypatch):
    from services.assistant.service import AssistantService

    service = AssistantService()
    monkeypatch.setattr(settings, "ASSISTANT_ENABLED", False)
    result = await service.chat("hi", {})
    assert result["text"] or result.get("provider") == {"name": "none", "model": ""}
    assert "disabled" in result["text"].lower()

    streamed = [item async for item in service.stream("hi", {})]
    assert streamed[0]["event"] == "error"

    monkeypatch.setattr(settings, "ASSISTANT_ENABLED", True)

    async def _boom(*args, **kwargs):
        raise ProviderError("no model", ProviderStatus.UNAVAILABLE)

    monkeypatch.setattr("services.assistant.service.run_agent", _boom)
    result = await service.chat("hi", {})
    assert "no model" in result["text"]
    streamed = [item async for item in service.stream("hi", {})]
    assert streamed[0] == {"event": "error", "data": "no model"}


async def test_health_endpoint_shape(api_client):
    response = await api_client.get("/api/v1/assistant/health")
    assert response.status_code in (200, 503)
    data = response.json()
    assert "enabled" in data
    assert "configured_providers" in data or "providers" in data


# --------------------------------------- Phase B: latency (dynamic tools)


def test_specs_for_filters_families():
    from services.assistant.tools_definitions import assistant_tools  # noqa: F401
    from services.assistant.tools_registry import tool_registry

    all_specs = tool_registry.specs()
    assert len(all_specs) == 16
    market_specs = tool_registry.specs_for({"market"})
    assert 0 < len(market_specs) < len(all_specs)
    assert {s["name"] for s in market_specs} >= {"market_latest", "market_list_states"}
    assert all("weather" not in s["name"] for s in market_specs)
    assert len(tool_registry.specs_for(None)) == len(all_specs)
    assert len(tool_registry.specs_for(set())) == len(all_specs)


def test_families_for_routing():
    import services.assistant.agent as agent_mod

    assert agent_mod._families_for("tomato price in Nalgonda") == {"market"}
    assert agent_mod._families_for("will it rain tomorrow?") == {"weather"}
    assert agent_mod._families_for("PM-KISAN benefits?") == {"schemes"}
    assert agent_mod._families_for("Explain PMFBY") == {"schemes"}
    assert agent_mod._families_for("paddy blast disease treatment?") == {"disease"}
    # No family matched: everything except schemes (a crop name alone
    # must not route to scheme tools).
    assert agent_mod._families_for("hello") == set(agent_mod._FAMILY_RES) - {"schemes"}
    assert "schemes" not in agent_mod._families_for("Best practices for wheat cultivation.")
    multi = agent_mod._families_for("profit for paddy at current market price")
    assert {"market", "planning"} <= multi


def test_classify_intent_step11():
    """STEP 11 regression: intent categories for routing."""
    import services.assistant.agent as agent_mod

    classify = agent_mod.classify_intent
    assert classify("Best practices for wheat cultivation.") == "GENERAL_AGRICULTURAL_KNOWLEDGE"
    assert classify("How should I prepare soil for paddy?") == "GENERAL_AGRICULTURAL_KNOWLEDGE"
    assert classify("What government schemes are available for wheat farmers?") == "GOVERNMENT_SCHEME"
    assert classify("Explain PMFBY") == "GOVERNMENT_SCHEME"
    assert classify("Am I eligible for PMFBY?") == "GOVERNMENT_SCHEME"
    assert classify("What subsidy is available for wheat?") == "GOVERNMENT_SCHEME"
    assert classify("Show me the latest paddy price in Telangana.") == "MARKET"
    assert classify("Show tomato prices in Nalgonda.") == "MARKET"
    assert classify("What's the weather tomorrow?") == "WEATHER"
    assert classify("Open the market page.") == "UI_NAVIGATION"
    assert classify("Hello") == "OTHER"


def test_resolve_names_canonical():
    """Pure entity-resolution unit tests (no DB)."""
    from services.assistant.tools_market import _resolve_names
    candidates = ["Paddy(Common)", "Paddy(Basmati)", "Wheat", "Tomato"]
    assert _resolve_names("Paddy(Common)", candidates) == ["Paddy(Common)"]
    assert _resolve_names("paddy(common)", candidates) == ["Paddy(Common)"]
    assert _resolve_names("Wheat", candidates) == ["Wheat"]
    assert _resolve_names("paddy", ["Paddy(Common)", "Wheat"]) == ["Paddy(Common)"]
    assert _resolve_names("paddy", candidates) == ["Paddy(Common)", "Paddy(Basmati)"]
    assert _resolve_names("Nakrekal", ["Nakrekal APMC", "Nalgonda APMC"]) == ["Nakrekal APMC"]
    assert _resolve_names("Bajra", candidates) == []
    assert _resolve_names("", candidates) == []
    assert _resolve_names(None, candidates) == []


def test_resolve_names_multilingual_aliases():
    """V1.3 §7: te/hi/transliterated terms resolve to canonical bases."""
    from services.assistant.tools_market import _resolve_names

    candidates = ["Paddy(Common)", "Paddy(Basmati)", "Wheat", "Tomato",
                  "Cotton", "Turmeric", "Chillies", "Groundnut"]
    assert _resolve_names("వరి", candidates) == ["Paddy(Common)", "Paddy(Basmati)"]
    assert _resolve_names("धान", candidates) == ["Paddy(Common)", "Paddy(Basmati)"]
    assert _resolve_names("dhan", candidates) == ["Paddy(Common)", "Paddy(Basmati)"]
    assert _resolve_names("టమాటా", candidates) == ["Tomato"]
    assert _resolve_names("टमाटर", candidates) == ["Tomato"]
    assert _resolve_names("गेहूं", candidates) == ["Wheat"]
    assert _resolve_names("कपास", candidates) == ["Cotton"]
    assert _resolve_names("हल्दी", candidates) == ["Turmeric"]
    states = ["Telangana", "Andhra Pradesh", "Karnataka", "Maharashtra"]
    assert _resolve_names("తెలంగాణ", states) == ["Telangana"]
    assert _resolve_names("तेलंगाना", states) == ["Telangana"]
    districts = ["Nalgonda", "Karimnagar", "Khammam", "Warangal"]
    assert _resolve_names("నల్గొండ", districts) == ["Nalgonda"]
    assert _resolve_names("नलगोंडा", districts) == ["Nalgonda"]
    # Unknown scripts/terms fall through unchanged (no false matches).
    assert _resolve_names("xyzzy", candidates) == []


async def test_general_knowledge_offers_no_tools(monkeypatch):
    """General agri knowledge offers zero tools (no scheme misuse)."""
    from services.assistant.tools_definitions import assistant_tools  # noqa: F401

    import services.assistant.agent as agent_mod

    seen: list = []

    class _SpyRouter(_ScriptRouter):
        async def chat(self, messages, tools=None, requirements=None, tool_choice=None):
            seen.append(tools)
            return await super().chat(messages, tools, requirements, tool_choice)

    monkeypatch.setattr(agent_mod, "router", _SpyRouter([_assistant_text_result("general advice")]))
    result = await agent_mod.run_agent("Best practices for wheat cultivation.", context={})
    assert result["text"] == "general advice"
    assert seen and seen[0] is None  # specs=[] passed as None
    assert result["tool_events"] == []


def test_decide_route_skips_retry_for_general_knowledge():
    """General answers are accepted directly: no tools to force."""
    import services.assistant.agent as agent_mod

    state = {
        "messages": [{"role": "user", "content": "Best practices for wheat cultivation."}],
        "steps": 0,
    }
    assert agent_mod.decide_route(state) == "finalize"  # type: ignore[arg-type]


async def test_fast_path_greeting_offers_no_tools(monkeypatch):
    from services.assistant.tools_definitions import assistant_tools  # noqa: F401

    import services.assistant.agent as agent_mod

    seen: list = []

    class _SpyRouter(_ScriptRouter):
        async def chat(self, messages, tools=None, requirements=None, tool_choice=None):
            seen.append(tools)
            return await super().chat(messages, tools, requirements, tool_choice)

    monkeypatch.setattr(agent_mod, "router", _SpyRouter([_assistant_text_result("Namaste!")]))
    result = await agent_mod.run_agent("hello", context={})
    assert result["text"] == "Namaste!"
    assert seen and seen[0] is None  # specs=[] passed as None: smaller prompt


async def test_overlap_retry_forces_tool_once(monkeypatch):
    from services.assistant.tools_definitions import assistant_tools  # noqa: F401

    import services.assistant.agent as agent_mod

    profit_args = {
        "crop": "wheat",
        "area_hectares": 1.0,
        "expected_yield_per_hectare": 40.0,
        "market_price_per_quintal": 2400.0,
        "cost_per_hectare": 30000.0,
    }
    script_router = _ScriptRouter(
        [
            _assistant_text_result("thinking..."),  # step 0 dodges forced tool
            _tool_call_result("crop_profit", profit_args),  # retry forces call
            _assistant_text_result("done"),
        ]
    )
    monkeypatch.setattr(agent_mod, "router", script_router)
    result = await agent_mod.run_agent("profit for wheat?", context={})
    assert result["text"] == "done"
    assert script_router.calls == 3
    assert len(result["tool_events"]) == 1


def test_decide_route_retry_then_finalize():
    import services.assistant.agent as agent_mod

    state = {
        "messages": [{"role": "user", "content": "wheat price today?"}],
        "steps": 0,
    }
    assert agent_mod.decide_route(state) == "retry"  # type: ignore[arg-type]
    state["overlap_retried"] = True
    assert agent_mod.decide_route(state) == "finalize"  # type: ignore[arg-type]


def test_ollama_payload_keep_alive(monkeypatch):
    from services.assistant.providers import OllamaProvider
    from services.assistant.types import ChatMessage

    provider = OllamaProvider("http://ollama:11434", "llama3.1:8b")
    messages = [ChatMessage(role="user", content="hi")]
    monkeypatch.setattr(settings, "OLLAMA_KEEP_ALIVE", "30m")
    assert provider._payload(messages, None, stream=False)["keep_alive"] == "30m"
    monkeypatch.setattr(settings, "OLLAMA_KEEP_ALIVE", "")
    assert "keep_alive" not in provider._payload(messages, None, stream=False)


def test_market_ui_action_derivation():
    """Pure mapping: market tool + filter args -> apply-market-filters."""
    import services.assistant.agent as agent_mod

    got = agent_mod._market_ui_action(
        "market_latest", {"commodity": "Wheat", "state": "Telangana", "limit": 5}
    )
    assert got == {
        "action": "apply-market-filters",
        "payload": {"commodity": "Wheat", "state": "Telangana"},
    }
    assert agent_mod._market_ui_action("market_latest", {"limit": 5}) is None
    assert agent_mod._market_ui_action("crop_profit", {"crop": "wheat"}) is None
    assert agent_mod._market_ui_action("market_latest", "not-a-dict") is None  # type: ignore[arg-type]
    # Resolved canonical commodity overrides the raw model arg so the
    # deep-link lands on the same data the tool read.
    got = agent_mod._market_ui_action(
        "market_latest",
        {"commodity": "paddy", "state": "Telangana"},
        {"resolved_commodity": ["Paddy(Common)"]},
    )
    assert got == {
        "action": "apply-market-filters",
        "payload": {"commodity": "Paddy(Common)", "state": "Telangana"},
    }
    got = agent_mod._market_ui_action(
        "market_history",
        {"commodity": "paddy", "state": "Telangana"},
        {"resolved_commodity": "Paddy(Common)"},
    )
    assert got is not None and got["payload"]["commodity"] == "Paddy(Common)"
    # Dropped (unresolvable) filters are stripped so the deep-link never
    # points at a guaranteed-empty view.
    got = agent_mod._market_ui_action(
        "market_latest",
        {"commodity": "Tomato", "district": "Haldondorf"},
        {"resolved_commodity": ["Tomato"], "dropped_filters": ["district='Haldondorf'"]},
    )
    assert got == {
        "action": "apply-market-filters",
        "payload": {"commodity": "Tomato"},
    }
    # Resolved scope (state/district/market) overrides misassigned args:
    # the model put a district ("Nalgonda") in state.
    got = agent_mod._market_ui_action(
        "market_latest",
        {"commodity": "tomato", "state": "Nalgonda"},
        {"resolved_commodity": ["Tomato"],
         "resolved_scope": {"state": "Telangana", "district": "Nalgonda"}},
    )
    assert got == {
        "action": "apply-market-filters",
        "payload": {"commodity": "Tomato", "state": "Telangana", "district": "Nalgonda"},
    }


async def test_execute_tools_emits_market_action_on_success(monkeypatch):
    """Successful market tool calls stash a deep-link action in state."""
    import services.assistant.agent as agent_mod
    from services.assistant.types import ToolEvent

    async def fake_execute(name, args, context):
        return ({"ok": True}, ToolEvent(tool=name, status="succeeded"))

    monkeypatch.setattr(agent_mod.tool_registry, "execute", fake_execute)
    state = {
        "messages": [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "c1",
                        "name": "market_latest",
                        "args": {"commodity": "Wheat", "state": "Telangana"},
                    }
                ],
            }
        ],
        "tool_events": [],
        "ui_actions": [],
        "steps": 0,
    }
    out = await agent_mod.execute_tools(state, {})  # type: ignore[arg-type]
    assert out["ui_actions"] == [
        {
            "action": "apply-market-filters",
            "payload": {"commodity": "Wheat", "state": "Telangana"},
        }
    ]
    assert out["tool_events"][0]["status"] == "succeeded"


async def test_execute_tools_no_action_on_failure(monkeypatch):
    """Failed market calls must not deep-link anywhere."""
    import services.assistant.agent as agent_mod
    from services.assistant.types import ToolEvent

    async def fake_execute(name, args, context):
        return ({"error": "db down"}, ToolEvent(tool=name, status="failed"))

    monkeypatch.setattr(agent_mod.tool_registry, "execute", fake_execute)
    state = {
        "messages": [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "c1",
                        "name": "market_latest",
                        "args": {"commodity": "Wheat", "state": "Telangana"},
                    }
                ],
            }
        ],
        "tool_events": [],
        "ui_actions": [],
        "steps": 0,
    }
    out = await agent_mod.execute_tools(state, {})  # type: ignore[arg-type]
    assert out["ui_actions"] == []


async def test_execute_tools_collects_citations(monkeypatch):
    """RAG citations embedded in tool output reach the turn result."""
    import services.assistant.agent as agent_mod
    from services.assistant.types import ToolEvent

    async def fake_execute(name, args, context):
        return (
            {"ok": True, "matches": [],
             "citations": [
                 {"source": "scheme:PMFBY", "title": "PMFBY", "snippet": "crop insurance"},
                 {"source": "scheme:PMFBY", "title": "PMFBY", "snippet": "dupe"},
                 {"source": "", "title": ""},
             ]},
            ToolEvent(tool=name, status="succeeded"),
        )

    monkeypatch.setattr(agent_mod.tool_registry, "execute", fake_execute)
    state = {
        "messages": [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"id": "c1", "name": "scheme_search", "args": {"query": "PMFBY"}}],
            }
        ],
        "tool_events": [],
        "citations": [],
        "ui_actions": [],
        "steps": 0,
    }
    out = await agent_mod.execute_tools(state, {})  # type: ignore[arg-type]
    assert out["citations"] == [
        {"source": "scheme:PMFBY", "title": "PMFBY", "snippet": "crop insurance"}
    ]


def test_language_registry_canonical():
    """V1.3 §3: 23 locales, stable codes, honest capability flags."""
    from services.assistant.languages import (
        LANGUAGES,
        get_language,
        resolve_language,
    )

    assert len(LANGUAGES) == 23
    codes = [lang.code for lang in LANGUAGES]
    assert len(set(codes)) == 23  # stable, unique
    assert codes[0] == "en"
    te = get_language("te")
    assert te is not None and te.locale == "te-IN" and te.rtl is False
    ur = get_language("ur")
    assert ur is not None and ur.rtl is True
    assert ur.asr_available is False and ur.tts_available is False  # honest
    assert get_language("xx") is None
    assert resolve_language("xx").code == "en"
    assert resolve_language("hi").code == "hi"


def test_command_actions_deterministic():
    """V1.3 §26-28: language-switch and open-page commands."""
    from services.assistant.commands import command_actions

    assert command_actions("Switch to Telugu") == [
        {"action": "assistant.set_language", "payload": {"language": "te"}}
    ]
    assert command_actions("Open markets page") == [
        {"action": "navigation.open_page", "payload": {"page": "markets"}}
    ]
    assert command_actions("hindi mein dikhao") == [
        {"action": "assistant.set_language", "payload": {"language": "hi"}}
    ]
    # Ordinary domain queries emit no commands.
    assert command_actions("Show tomato prices in Nalgonda.") == []
    assert command_actions("Best practices for wheat cultivation.") == []


def test_action_value_validation():
    """V1.3 §27: closed-set payloads reject unknown pages/languages."""
    from services.assistant.ui_actions import validate_ui_actions

    ok = validate_ui_actions([
        {"action": "assistant.set_language", "payload": {"language": "te"}},
        {"action": "navigation.open_page", "payload": {"page": "markets"}},
        {"action": "navigation.open_page", "payload": {"page": "https://evil.com"}},
        {"action": "navigation.open_page", "payload": {"page": "../admin"}},
        {"action": "assistant.set_language", "payload": {"language": "xx"}},
        {"action": "assistant.set_language", "payload": {}},
    ])
    assert [(a.action, a.payload) for a in ok] == [
        ("assistant.set_language", {"language": "te"}),
        ("navigation.open_page", {"page": "markets"}),
    ]


def test_page_context_allow_list():
    """V1.3 §15/32: only safe page fields pass; secrets never do."""
    from api.v1.endpoints.assistant import _page_context
    from schemas.assistant import AssistantChatRequest

    body = AssistantChatRequest(
        message="hi",
        route="/markets",
        page="markets",
        page_filters={"state": "Telangana", "token": "x" * 200},
    )
    ctx = _page_context(body)
    assert ctx["route"] == "/markets" and ctx["page"] == "markets"
    assert ctx["page_filters"]["state"] == "Telangana"
    assert "token" not in ctx["page_filters"]  # >128 chars dropped

    evil = AssistantChatRequest(
        message="hi", route="https://evil.com/x", page="../admin",
        page_filters={"__import__": "os", ("k" * 40): "v"},
    )
    ctx = _page_context(evil)
    assert "route" not in ctx and "page" not in ctx
    # Scalar values pass (never evaluated server-side); keys are truncated.
    assert ctx["page_filters"] == {"__import__": "os", "k" * 32: "v"}
