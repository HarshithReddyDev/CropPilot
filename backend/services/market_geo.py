"""AGMARKNET geography synchronization into the local catalog.

Independent of price ingestion: geography stays available even when price
ingestion fails, and vice versa. Idempotent: safe to rerun daily.
"""

from __future__ import annotations

import structlog

from repositories.market_geo import geo_repository

logger = structlog.get_logger(__name__)


def _strip(value: object) -> str:
    return str(value).strip() if value is not None else ""


async def sync_agmarknet_geography(db) -> dict[str, int]:
    """Fetch AGMARKNET metadata and upsert states/districts/markets.

    Returns counts {states, districts, markets, created, updated}.
    Raises AgmarknetError subclasses on upstream failure; callers audit it.
    """
    from services import agmarknet_client
    from services.market_providers import agmarknet_provider

    created = updated = 0

    states = await agmarknet_provider.get_states()
    for state in states:
        _, is_new = await geo_repository.upsert_state(db, int(state.id), state.name)
        created, updated = created + is_new, updated + (not is_new)

    filters = await agmarknet_client.fetch_filters()
    data = filters.get("data", {})
    state_names = {
        s.get("state_id"): _strip(s.get("state_name"))
        for s in data.get("state_data", [])
        if isinstance(s, dict)
    }
    categories = {}
    try:
        for entry in await agmarknet_client.list_market_categories():
            if isinstance(entry, dict):
                categories[entry.get("id")] = _strip(
                    entry.get("name") or entry.get("code")
                )
    except Exception as exc:
        logger.warning("agmarknet_categories_skipped", error=str(exc)[:200])

    for entry in data.get("district_data", []):
        if not isinstance(entry, dict) or entry.get("id") is None:
            continue
        name = _strip(entry.get("district_name"))
        if not name or "all districts" in name.lower():
            continue
        state_id = entry.get("state_id")
        _, is_new = await geo_repository.upsert_district(
            db,
            source_id=int(entry["id"]),
            name=name,
            state_id=int(state_id) if state_id is not None else -1,
            state_name=state_names.get(state_id, ""),
        )
        created, updated = created + is_new, updated + (not is_new)

    district_names = {
        d.get("id"): _strip(d.get("district_name"))
        for d in data.get("district_data", [])
        if isinstance(d, dict)
    }

    for entry in data.get("market_data", []):
        if not isinstance(entry, dict) or entry.get("id") is None:
            continue
        name = _strip(entry.get("mkt_name"))
        if not name or "all markets" in name.lower():
            continue
        district_id = entry.get("district_id")
        state_id = entry.get("state_id")
        district_name = district_names.get(district_id, "")
        _, is_new = await geo_repository.upsert_market(
            db,
            source_id=int(entry["id"]),
            name=name,
            district_id=int(district_id) if district_id is not None else None,
            district_name=district_name,
            state_id=int(state_id) if state_id is not None else None,
            state_name=state_names.get(state_id, ""),
            category=categories.get(entry.get("category_id"), ""),
        )
        created, updated = created + is_new, updated + (not is_new)

    counts = await geo_repository.counts(db)
    logger.info(
        "agmarknet_geo_sync_completed",
        states=counts["states"],
        districts=counts["districts"],
        markets=counts["markets"],
        created=created,
    )
    return {**counts, "created": created, "updated": updated}
