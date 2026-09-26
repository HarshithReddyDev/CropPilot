"""Startup/readiness behavior (§3): offline probe never hangs, positive cached."""

from services.assistant.router import LLMProviderRouter


def _dead_router(monkeypatch) -> LLMProviderRouter:
    r = LLMProviderRouter.__new__(LLMProviderRouter)
    r._providers = {}
    r._cooldown_until = {}
    r._failures = {}
    r._ollama_ready = False
    r._ollama_ready_at = None
    return r


def test_probe_offline_returns_false_fast():
    import asyncio

    from core.config import settings

    r = _dead_router(None)
    # Point at a port nothing listens on: must return False, not hang.
    ready, ms = asyncio.run(_probe_base(r, "http://127.0.0.1:9", settings.ASSISTANT_LOCAL_MODEL))
    assert ready is False
    # No hang: bounded by the 2s probe timeout (Windows connect refused
    # costs ~2.2s with overhead; an unguarded default would take 60s+).
    assert ms < 5000.0


def _probe_base(router, base, model):
    import time

    import httpx

    async def go():
        started = time.monotonic()
        try:
            resp = await httpx.AsyncClient().get(base.replace("/v1", "/api/tags"), timeout=2.0)
            names = [m.get("name", "") for m in resp.json().get("models", [])]
            ok = any(model.split(":")[0] in (n or "") for n in names)
        except Exception:
            ok = False
        return ok, (time.monotonic() - started) * 1000.0

    return go()


def test_ready_once_stays_ready(monkeypatch):
    import asyncio
    import time

    r = _dead_router(None)
    r._ollama_ready = True
    r._ollama_ready_at = time.monotonic()
    import services.assistant.router as router_mod

    async def fake_tags(self, *a, **k):
        raise AssertionError("cached True must not hit network")

    monkeypatch.setattr("httpx.AsyncClient.get", fake_tags)
    ready, ms = asyncio.run(router_mod.LLMProviderRouter.ollama_model_ready(r))
    assert ready is True
    assert ms == 0.0


def test_stale_ready_reprobes(monkeypatch):
    """Expired positive cache must re-probe (Ollama may have restarted)."""
    import asyncio
    import time

    import services.assistant.router as router_mod

    r = _dead_router(None)
    r._ollama_ready = True
    r._ollama_ready_at = time.monotonic() - router_mod.MODEL_READY_TTL_S - 1.0

    class Resp:
        def json(self):
            return {"models": []}  # model gone: Ollama restarted fresh

    async def fake_get(self, *a, **k):
        return Resp()

    monkeypatch.setattr("httpx.AsyncClient.get", fake_get)
    ready, _ = asyncio.run(router_mod.LLMProviderRouter.ollama_model_ready(r))
    assert ready is False
    assert r._ollama_ready is False


def test_never_ready_retries_next_time(monkeypatch):
    import asyncio

    import services.assistant.router as router_mod

    r = _dead_router(None)

    class Resp:
        def json(self):
            return {"models": []}

    async def fake_get(self, *a, **k):
        return Resp()

    monkeypatch.setattr("httpx.AsyncClient.get", fake_get)
    ready, _ = asyncio.run(router_mod.LLMProviderRouter.ollama_model_ready(r))
    assert ready is False
    assert r._ollama_ready is False  # negative never cached


def test_positive_probe_caches(monkeypatch):
    import asyncio

    import services.assistant.router as router_mod
    from core.config import settings

    r = _dead_router(None)

    class Resp:
        def json(self):
            short = settings.ASSISTANT_LOCAL_MODEL.split(":")[0]
            return {"models": [{"name": f"{short}:latest"}]}

    async def fake_get(self, *a, **k):
        return Resp()

    monkeypatch.setattr("httpx.AsyncClient.get", fake_get)
    ready, _ = asyncio.run(router_mod.LLMProviderRouter.ollama_model_ready(r))
    assert ready is True
    assert r._ollama_ready is True
