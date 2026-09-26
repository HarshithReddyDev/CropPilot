"""Scheme tools for the assistant.

`schemes_list` reads the structured schemes table. `scheme_search` runs
hybrid retrieval (vector + keyword rerank) with citations behind one name.
"""

from __future__ import annotations

from db.session import async_session_factory
from services.scheme import scheme_service


def _compact(s: dict) -> dict:
    return {
        "name": s.get("name"),
        "state": s.get("state"),
        "category": s.get("category"),
        "benefits": s.get("benefits"),
        "eligibility": s.get("eligibility"),
        "how_to_apply": s.get("how_to_apply"),
        "source_url": s.get("source_url"),
    }


async def schemes_list(
    state: str | None = None, category: str | None = None
) -> dict:
    """List government schemes, optionally filtered by state/category."""
    from services.assistant.tools_market import _resolve_dimension

    async with async_session_factory() as db:
        resolved_state, dropped = state, []
        if (state or "").strip():
            hit = await _resolve_dimension(db, "state", state)
            if hit:
                resolved_state = hit[0]
            else:
                resolved_state, dropped = None, [f"state={state!r}"]
        if resolved_state:
            rows = await scheme_service.get_schemes_by_state(db, resolved_state)
        elif category:
            rows = await scheme_service.get_schemes_by_category(db, category)
        else:
            rows = await scheme_service.get_schemes_by_state(db, "Telangana")
    items = [r.model_dump(mode="json") for r in rows][:10]
    out = {"schemes": [_compact(s) for s in items], "count": len(items)}
    if dropped:
        out["dropped_filters"] = dropped
    return out


async def scheme_search(query: str, state: str | None = None) -> dict:
    """Hybrid search over scheme documents. Returns matches + citations."""
    from .retrieval import retrieve_schemes
    from services.assistant.tools_market import _resolve_dimension

    dropped: list[str] = []
    if (state or "").strip():
        try:
            async with async_session_factory() as db:
                hit = await _resolve_dimension(db, "state", state)
            if hit:
                state = hit[0]
            else:
                state, dropped = None, [f"state={state!r}"]
        except Exception:
            pass
    try:
        payload_text, citations = await retrieve_schemes(query, state=state)
    except Exception as e:
        return {"ok": False, "error": f"scheme search unavailable: {e}"}
    import json

    payload = json.loads(payload_text)
    out = {
        "ok": True,
        "matches": [
            {"name": r.get("scheme"), "snippet": r.get("snippet")}
            for r in payload.get("results", [])
        ],
        "citations": [c.model_dump() for c in citations],
    }
    if payload.get("scope") and payload["scope"] != (state or "Telangana"):
        out["scope"] = payload["scope"]
    if dropped:
        out["dropped_filters"] = dropped
    return out
