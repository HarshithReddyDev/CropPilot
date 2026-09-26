"""Market tools for the assistant. DB read-only via MarketService.

Every tool returns small JSON-serializable dicts. No raw SQL anywhere:
all access goes through the repository-backed service layer, so the
natural-key grain and provenance rules stay in one place.

Entity resolution: the model passes natural language ("paddy",
"Nalgonda") but the database holds canonical AGMARKNET spellings
("Paddy(Common)", "Nakrekal APMC"). Repository filters are exact
(case-insensitive) matches, so an unresolved name silently returns zero
rows. Every tool therefore resolves requested dimension values against
real metadata before querying, and discloses what it resolved or dropped
in the output (resolved_*/dropped_filters) so the answer can cite real
values and the UI deep-link lands on the same data.
"""

from __future__ import annotations

from datetime import date

from db.session import async_session_factory
from services.market import MarketService, STALE_AFTER_DAYS

_market = MarketService()

_DEFAULT_STATE = "Telangana"


def _dump(obj) -> dict:
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    if isinstance(obj, dict):
        return obj
    if isinstance(obj, list):
        return {"items": [_dump(i) for i in obj]}
    return {"value": obj}


def _compact_latest(payload: dict, limit: int) -> dict:
    items = payload.get("items", [])[:limit]
    rows = [
        {
            "market": i.get("market"),
            "district": i.get("district"),
            "commodity": i.get("commodity"),
            "variety": i.get("variety"),
            "grade": i.get("grade"),
            "min_price": i.get("min_price"),
            "max_price": i.get("max_price"),
            "modal_price": i.get("modal_price"),
            "price_per_unit": i.get("price_per_unit"),
            "arrival_date": i.get("arrival_date"),
            "arrivals": i.get("arrivals"),
            "arrival_unit": i.get("arrival_unit"),
            "source": i.get("source"),
        }
        for i in items
    ]
    return {
        "rows": rows,
        "freshness": payload.get("freshness"),
        "provenance": payload.get("provenance"),
    }


async def market_latest(
    commodity: str,
    state: str | None = None,
    district: str | None = None,
    market: str | None = None,
    variety: str | None = None,
    grade: str | None = None,
    limit: int = 5,
) -> dict:
    """Latest mandi prices for a commodity. State defaults to Telangana.

    Natural-language dimension values are resolved to canonical metadata
    spellings first ("paddy" -> "Paddy(Common)"). Unresolvable filters are
    dropped (disclosed) instead of forcing an empty result; multiple
    canonical commodities merge as labeled rows, never averages.
    """
    limit = max(1, min(int(limit or 5), 10))
    async with async_session_factory() as db:
        state_q, district_q, market_q, dropped, scope = await _resolve_scope(
            db, state, district, market
        )
        commodities = await _resolve_dimension(
            db, "commodity", commodity, state=state_q,
            district=district_q or district, market=market_q or market,
        )
        if (commodity or "").strip() and not commodities:
            dropped.append(f"commodity={commodity!r}")
        queries = commodities or ([commodity] if (commodity or "").strip() else [])
        item_lists: list[list[dict]] = []
        provenance: dict | None = None
        for canonical in queries:
            resp = await _market.get_latest(
                db,
                state=state_q,
                district=district_q,
                commodity=canonical,
                market=market_q,
                variety=variety,
                grade=grade,
                limit=limit,
            )
            dumped = _dump(resp)
            item_lists.append(dumped.get("items", []))
            if provenance is None:
                provenance = dumped.get("provenance")
        merged = _merge_latest_items(item_lists, limit)
        payload = {
            "items": merged,
            "freshness": _freshness_from_items(merged),
            "provenance": provenance,
        }
        out = _compact_latest(payload, limit)
        out["resolved_commodity"] = commodities
        if scope:
            out["resolved_scope"] = scope
        if dropped:
            out["dropped_filters"] = dropped
        return out


async def market_history(
    commodity: str,
    state: str | None = None,
    market: str | None = None,
    district: str | None = None,
    variety: str | None = None,
    grade: str | None = None,
    days: int = 30,
) -> dict:
    """Price history series for a commodity at one market lineage.

    Commodity names resolve as in market_latest. Multiple canonical
    lineages keep the most current series and disclose the rest in
    other_lineages (a series never mixes lineages).
    """
    days = max(1, min(int(days or 30), 90))
    async with async_session_factory() as db:
        state_q, district_q, market_q, dropped, scope = await _resolve_scope(
            db, state, district, market
        )
        commodities = await _resolve_dimension(
            db, "commodity", commodity, state=state_q,
            district=district_q or district, market=market_q or market,
        )
        if (commodity or "").strip() and not commodities:
            dropped.append(f"commodity={commodity!r}")
        queries = commodities or ([commodity] if (commodity or "").strip() else [])
        best: dict | None = None
        for canonical in queries:
            resp = await _market.get_history(
                db,
                commodity=canonical,
                state=state_q,
                district=district_q,
                market=market_q,
                variety=variety,
                grade=grade,
                days=days,
            )
            dumped = _dump(resp)
            points = dumped.get("points", dumped.get("items", []))[:days]
            fresh = dumped.get("freshness") or {}
            key = str(fresh.get("latest_observation_date") or "")
            if best is None or key > str((best.get("freshness") or {}).get("latest_observation_date") or ""):
                best = {
                    "canonical": canonical,
                    "points": points,
                    "group": dumped.get("group"),
                    "freshness": fresh,
                    "provenance": dumped.get("provenance"),
                }
        best = best or {"canonical": None, "points": [], "group": None, "freshness": {}, "provenance": None}
        series = [
            {
                "arrival_date": p.get("arrival_date"),
                "modal_price": p.get("modal_price"),
                "min_price": p.get("min_price"),
                "max_price": p.get("max_price"),
                "price_per_unit": p.get("price_per_unit"),
            }
            for p in best["points"]
        ]
        out = {
            "commodity": commodity,
            "resolved_commodity": best["canonical"],
            "group": best["group"],
            "points": series,
            "freshness": best["freshness"],
            "provenance": best["provenance"],
        }
        others = [c for c in queries if c != best["canonical"]]
        if others:
            out["other_lineages"] = others
        if scope:
            out["resolved_scope"] = scope
        if dropped:
            out["dropped_filters"] = dropped
        return out


async def market_compare(
    commodity: str,
    state: str | None = None,
    district: str | None = None,
    variety: str | None = None,
    grade: str | None = None,
) -> dict:
    """Compare latest modal prices across markets for one commodity.

    Commodity names resolve as in market_latest; multiple lineages merge
    as labeled rows (commodity key kept on every row), never averaged.
    """
    state = state or _DEFAULT_STATE
    async with async_session_factory() as db:
        state_q, district_q, _market_q, dropped, scope = await _resolve_scope(
            db, state, district, None
        )
        commodities = await _resolve_dimension(
            db, "commodity", commodity, state=state_q,
            district=district_q or district,
        )
        if (commodity or "").strip() and not commodities:
            dropped.append(f"commodity={commodity!r}")
        queries = commodities or ([commodity] if (commodity or "").strip() else [])
        rows: list[dict] = []
        group: dict | None = None
        provenance: dict | None = None
        for canonical in queries:
            resp = await _market.get_comparison(
                db,
                commodity=canonical,
                state=state_q,
                district=district_q,
                variety=variety,
                grade=grade,
            )
            dumped = _dump(resp)
            rows.extend(dumped.get("rows", [])[:10])
            if group is None:
                group = dumped.get("group")
            if provenance is None:
                provenance = dumped.get("provenance")
        rows = sorted(rows, key=lambda r: (r.get("modal_price") or 0, r.get("market") or ""))[:10]
        out_rows = [
            {
                "market": r.get("market"),
                "district": r.get("district"),
                "commodity": r.get("commodity"),
                "modal_price": r.get("modal_price"),
                "price_per_unit": r.get("price_per_unit"),
                "arrival_date": r.get("arrival_date"),
                "arrivals": r.get("arrivals"),
                "source": r.get("source"),
            }
            for r in rows
        ]
        out = {
            "commodity": commodity,
            "resolved_commodity": commodities,
            "rows": out_rows,
            "group": group,
            "provenance": provenance,
        }
        if scope:
            out["resolved_scope"] = scope
        if dropped:
            out["dropped_filters"] = dropped
        return out


async def market_overview(state: str | None = None) -> dict:
    """Coverage overview: states/markets/commodities and date bounds."""
    async with async_session_factory() as db:
        data = await _market.get_overview(db, state=state)
    return _dump(data)


async def _meta_list(values: list[str]) -> dict:
    """Cap metadata lists so entity resolution stays cheap."""
    return {"values": list(values)[:200], "count": len(values)}


def _resolve_names(requested: str | None, candidates: list[str]) -> list[str]:
    """Natural language -> canonical spelling(s), order-stable.

    Exact case-insensitive match wins; else base-name match (text before
    "(" — "paddy" -> "Paddy(Common)"); else substring match. Empty list
    means the requested value exists nowhere in scope.
    """
    req = _alias_normalize(requested)
    if not req:
        return []
    exact = [c for c in candidates if c.strip().lower() == req]
    if exact:
        return exact
    base = [c for c in candidates if c.split("(")[0].strip().lower() == req]
    if base:
        return base
    return [c for c in candidates if req in c.lower()]


#: Multilingual aliases -> English base names for entity resolution
#: (V1.3 §7). Telugu/Hindi forms plus common transliterations, verified
#: against the registry scripts. Canonical DB values stay untouched;
#: aliases only normalize the REQUEST before matching. Unknown terms
#: fall through to the existing match tiers unchanged.
ENTITY_ALIASES: dict[str, str] = {
    # commodities
    "వరి": "paddy", "धान": "paddy", "dhan": "paddy", "vari": "paddy",
    "biyyam": "paddy", "चावल": "paddy", "chawal": "paddy",
    "టమాటా": "tomato", "टमाटर": "tomato", "tamata": "tomato",
    "tamaatar": "tomato", "takkali": "tomato",
    "గోధుమ": "wheat", "गेहूं": "wheat", "gehun": "wheat",
    "godhuma": "wheat", "godhi": "wheat",
    "పత్తి": "cotton", "कपास": "cotton", "kapas": "cotton",
    "పసుపు": "turmeric", "हल्दी": "turmeric", "haldi": "turmeric",
    "మిరప": "chilli", "मिर्च": "chilli", "mirch": "chilli", "mirap": "chilli",
    "వేరుశనగ": "groundnut", "मूंगफली": "groundnut", "mungfali": "groundnut",
    # states
    "తెలంగాణ": "telangana", "तेलंगाना": "telangana",
    "ఆంధ్రప్రదేశ్": "andhra pradesh", "आंध्र प्रदेश": "andhra pradesh",
    "కర్ణాటక": "karnataka", "कर्नाटक": "karnataka",
    "మహారాష్ట్ర": "maharashtra", "महाराष्ट्र": "maharashtra",
    # districts (Telangana + neighbors)
    "నల్గొండ": "nalgonda", "नलगोंडा": "nalgonda",
    "కరీంనగర్": "karimnagar", "करीमनगर": "karimnagar",
    "ఖమ్మం": "khammam", "खम्मम": "khammam",
    "వరంగల్": "warangal", "वारंगल": "warangal",
    "నిజామాబాద్": "nizamabad", "निज़ामाबाद": "nizamabad",
    "ఆదిలాబాద్": "adilabad", "आदिलाबाद": "adilabad",
    "మెదక్": "medak", "मेदक": "medak",
}


def _alias_normalize(requested: str | None) -> str:
    req = (requested or "").strip().lower()
    return ENTITY_ALIASES.get(req, req)


async def _resolve_dimension(
    db,
    kind: str,
    requested: str | None,
    state: str | None = None,
    district: str | None = None,
    market: str | None = None,
    commodity: str | None = None,
) -> list[str]:
    """Canonical spellings for one requested dimension value in scope.

    Falls back to state-only scope when the narrower scope has no
    candidates at all (a bad sibling filter must not hide a good value).
    Never raises: resolution failure means [], and the caller drops the
    filter instead of forcing an empty result.
    """
    if not (requested or "").strip():
        return []
    # Normalize scope values through multilingual aliases so a Telugu
    # district ("నల్గొండ") scopes correctly; canonical values pass
    # through unchanged. Commodity scope is never narrowed here by
    # callers (see _resolve_scope), so base-name mapping stays safe.
    state = _alias_normalize(state) or None
    district = _alias_normalize(district) or None
    market = _alias_normalize(market) or None
    try:
        if kind == "state":
            resp = await _market.get_states(db)
        elif kind == "commodity":
            resp = await _market.get_commodities(db, state=state, district=district, market=market)
        elif kind == "district":
            resp = await _market.get_districts(db, state=state)
        elif kind == "market":
            resp = await _market.get_markets(db, state=state, district=district, commodity=commodity)
        else:
            return []
        candidates = _dump(resp).get("values", [])
        hit = _resolve_names(requested, candidates)
        if hit or kind == "district":
            return hit
        # Narrow scope may be poisoned by another bad filter: retry state-wide.
        if kind == "commodity":
            resp = await _market.get_commodities(db, state=state)
        elif kind == "market":
            resp = await _market.get_markets(db, state=state, district=district)
        return _resolve_names(requested, _dump(resp).get("values", []))
    except Exception:
        return []


async def _states_with_district(db, district_name: str | None) -> list[str]:
    """States having a district with this exact (case-insensitive) name.

    Price-driven (market_prices), so adoption always leads to real rows.
    """
    from repositories.market import market_repository

    raw = _alias_normalize(district_name)
    if not raw:
        return []
    try:
        return list(await market_repository.distinct_values(db, "state", district=raw))
    except Exception:
        return []


async def _resolve_scope(
    db, state: str | None, district: str | None, market: str | None
) -> tuple[str | None, str | None, str | None, list[str], dict[str, str]]:
    """Resolve (state, district, market) to canonical query values.

    Returns (state_q, district_q, market_q, dropped, scope) where
    state_q None means national scope. Rules:
    - No state given -> Telangana default (existing contract).
    - Unresolvable state naming a unique district ("Nalgonda") ->
      that district's state + district (disclosed in scope).
    - Unresolvable state otherwise -> national scope + dropped entry.
    - Unresolvable district under a defaulted (not explicit) state ->
      retry nationally; a unique state adopts it, multi-state keeps the
      district filter nationally, none drops it.
    - Unresolvable market naming a district (no district given) ->
      moved to district.
    """
    dropped: list[str] = []
    scope: dict[str, str] = {}
    state_explicit = bool((state or "").strip())
    # -- state --
    if state_explicit:
        states = await _resolve_dimension(db, "state", state)
        if states:
            state_q: str | None = states[0]
            scope["state"] = states[0]
        else:
            having = await _states_with_district(db, state)
            if len(having) == 1:
                state_q = having[0]
                scope["state"] = having[0]
                if not (district or "").strip():
                    district = state  # reinterpret as district below
                    scope["note"] = f"state {state!r} interpreted as district"
            else:
                state_q = None
                dropped.append(f"state={state!r}")
    else:
        state_q = _DEFAULT_STATE
    # -- district --
    districts = await _resolve_dimension(db, "district", district, state=state_q)
    district_q = districts[0] if districts else None
    if district_q:
        scope["district"] = district_q
    elif (district or "").strip():
        if not state_explicit:
            having = await _states_with_district(db, district)
            if len(having) == 1:
                state_q = having[0]
                scope["state"] = having[0]
                districts = await _resolve_dimension(db, "district", district, state=state_q)
                district_q = districts[0] if districts else None
                if district_q:
                    scope["district"] = district_q
                else:
                    dropped.append(f"district={district!r}")
            elif not having:
                dropped.append(f"district={district!r}")
            else:
                state_q = None
                scope.pop("state", None)
                scope["district"] = district.strip()
                scope["note"] = f"district {district!r} spans states; national scope"
                district_q = district.strip()
        else:
            dropped.append(f"district={district!r}")
    # -- market --
    markets = await _resolve_dimension(
        db, "market", market, state=state_q, district=district_q or district,
    )
    market_q = markets[0] if markets else None
    if market_q:
        scope["market"] = market_q
    elif (market or "").strip():
        if not (district or "").strip() and not district_q:
            as_district = await _resolve_dimension(db, "district", market, state=state_q)
            if len(as_district) == 1:
                district_q = as_district[0]
                scope["district"] = district_q
                scope["note"] = f"market {market!r} interpreted as district"
            else:
                dropped.append(f"market={market!r}")
        else:
            dropped.append(f"market={market!r}")
    return state_q, district_q, market_q, dropped, scope


def _natural_key(item: dict) -> tuple:
    return (
        item.get("state") or "",
        item.get("district") or "",
        item.get("market") or "",
        item.get("commodity") or "",
        item.get("variety") or "",
        item.get("grade") or "",
    )


def _merge_latest_items(lists: list[list[dict]], limit: int) -> list[dict]:
    """Merge per-lineage latest rows: dedupe by natural key, newest first."""
    seen: dict[tuple, dict] = {}
    for items in lists:
        for item in items:
            seen.setdefault(_natural_key(item), item)
    ordered = sorted(
        seen.values(),
        key=lambda r: (
            r.get("arrival_date") or "",
            r.get("state") or "",
            r.get("district") or "",
            r.get("market") or "",
            r.get("commodity") or "",
            r.get("variety") or "",
            r.get("grade") or "",
        ),
        reverse=True,
    )
    return ordered[:limit]


def _freshness_from_items(items: list[dict]) -> dict:
    """Freshness mirrored from services.market._freshness over dumped items."""
    dates = []
    for item in items:
        raw = item.get("arrival_date")
        try:
            dates.append(date.fromisoformat(str(raw)[:10]) if raw else None)
        except ValueError:
            continue
    dates = [d for d in dates if d]
    if not dates:
        return {}
    latest, oldest = max(dates), min(dates)
    age = (date.today() - latest).days
    return {
        "latest_observation_date": latest.isoformat(),
        "oldest_observation_date": oldest.isoformat(),
        "age_days": age,
        "is_stale": age > STALE_AFTER_DAYS,
        "observation_count": len(items),
    }


async def list_states() -> dict:
    """All reporting states. Use to resolve the farmer's state name."""
    async with async_session_factory() as db:
        resp = await _market.get_states(db)
    return await _meta_list(_dump(resp).get("values", []))


async def list_districts(state: str | None = None) -> dict:
    """Districts in scope, optionally filtered by state."""
    async with async_session_factory() as db:
        resp = await _market.get_districts(db, state=state)
    return await _meta_list(_dump(resp).get("values", []))


async def list_markets(
    state: str | None = None,
    district: str | None = None,
    commodity: str | None = None,
) -> dict:
    """Markets in scope for optional state/district/commodity filters."""
    async with async_session_factory() as db:
        resp = await _market.get_markets(
            db, state=state, district=district, commodity=commodity
        )
    return await _meta_list(_dump(resp).get("values", []))


async def list_commodities(
    state: str | None = None,
    district: str | None = None,
    market: str | None = None,
) -> dict:
    """Commodities in scope for optional state/district/market filters."""
    async with async_session_factory() as db:
        resp = await _market.get_commodities(
            db, state=state, district=district, market=market
        )
    return await _meta_list(_dump(resp).get("values", []))


async def list_varieties(
    state: str | None = None,
    district: str | None = None,
    market: str | None = None,
    commodity: str | None = None,
) -> dict:
    """Varieties in scope for optional filters."""
    async with async_session_factory() as db:
        resp = await _market.get_varieties(
            db, state=state, district=district, market=market, commodity=commodity
        )
    return await _meta_list(_dump(resp).get("values", []))


async def list_grades(
    state: str | None = None,
    district: str | None = None,
    market: str | None = None,
    commodity: str | None = None,
    variety: str | None = None,
) -> dict:
    """Grades in scope for optional filters."""
    async with async_session_factory() as db:
        resp = await _market.get_grades(
            db,
            state=state,
            district=district,
            market=market,
            commodity=commodity,
            variety=variety,
        )
    return await _meta_list(_dump(resp).get("values", []))
