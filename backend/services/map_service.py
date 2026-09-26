"""Map experience orchestration: search, reverse, nearby markets, weather.

All data is real or explicitly absent:
- place search blends the local AGMARKNET geo catalog with server-side
  Nominatim (India-biased); every result carries its source.
- market markers only exist for coordinates from a verified source
  (persisted with provenance in geo_markets.coordinate_source).
- weather reuses the existing Open-Meteo-backed weather service.
- prices are latest reported market_prices rows (never "live").
"""

from __future__ import annotations

import math
from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.market import MarketPrice
from models.market_geo import GeoDistrict, GeoMarket, GeoState
from repositories.market_geo import geo_repository
from services.map_geocoder import ReverseResult, geocoder

EARTH_KM = 6371.0
NEARBY_DEFAULT_KM = 25.0
NEARBY_MAX_RESOLVE_PER_CALL = 5
WEATHER_REFRESH_HOURS = 3


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_KM * math.asin(math.sqrt(a))


def validate_coords(lat: float, lng: float) -> None:
    from fastapi import HTTPException, status

    if not (-90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "INVALID_COORDINATES",
                    "message": "Latitude must be -90..90 and longitude -180..180."},
        )


async def search_places(db: AsyncSession, q: str) -> list[dict]:
    """Local catalog first (states/districts/markets), then Nominatim for
    villages/towns/cities/PINs. Bounded, source-labeled."""
    query = (q or "").strip()
    out: list[dict] = []
    like = f"%{query}%"
    states = (await db.execute(
        select(GeoState).where(GeoState.name.ilike(like)).order_by(GeoState.name).limit(3)
    )).scalars().all()
    for s in states:
        out.append({"type": "state", "name": s.name, "district": None,
                    "state": s.name, "latitude": None, "longitude": None,
                    "source": "croppilot-geo-catalog"})
    districts = (await db.execute(
        select(GeoDistrict).where(GeoDistrict.name.ilike(like))
        .order_by(GeoDistrict.name).limit(5)
    )).scalars().all()
    for d in districts:
        out.append({"type": "district", "name": d.name, "district": d.name,
                    "state": d.state_name or None, "latitude": None,
                    "longitude": None, "source": "croppilot-geo-catalog"})
    markets = (await db.execute(
        select(GeoMarket).where(GeoMarket.name.ilike(like))
        .order_by(GeoMarket.name).limit(5)
    )).scalars().all()
    for m in markets:
        out.append({"type": "market", "name": m.name,
                    "district": m.district_name or None,
                    "state": m.state_name or None,
                    "latitude": m.latitude, "longitude": m.longitude,
                    "source": "croppilot-geo-catalog"})
    for r in await geocoder.search(query, limit=5):
        out.append({"type": "place", "name": r.name, "district": r.district,
                    "state": r.state, "latitude": r.latitude,
                    "longitude": r.longitude, "source": r.source})
    return out[:15]


async def reverse_place(lat: float, lng: float) -> dict:
    """Reverse geocode without ever failing the map: nulls on any error."""
    validate_coords(lat, lng)
    rev: ReverseResult | None = await geocoder.reverse(lat, lng)
    if rev is None:
        return {"latitude": lat, "longitude": lng, "display_name": None,
                "locality": None, "district": None, "state": None,
                "country": None, "postcode": None, "source": None}
    return {"latitude": rev.latitude, "longitude": rev.longitude,
            "display_name": rev.display_name, "locality": rev.locality,
            "district": rev.district, "state": rev.state,
            "country": rev.country, "postcode": rev.postcode,
            "source": rev.source}


def _district_variants(district: str | None) -> list[str]:
    """Reverse-geocoders return names like 'Nalgonda mandal' while the
    catalog stores 'Nalgonda'. Try the raw value plus de-suffixed cores."""
    if not district:
        return []
    out = [district.strip()]
    core = district.strip()
    for suffix in (" mandal", " district", " zilla", " division", " taluk", " tehsil"):
        if core.lower().endswith(suffix):
            core = core[: -len(suffix)].strip()
    if core and core.lower() not in {v.lower() for v in out}:
        out.append(core)
    return out


async def _catalog_markets(db: AsyncSession, state: str | None,
                           district: str | None, limit: int = 500) -> list[GeoMarket]:
    from sqlalchemy import or_

    if district or state:
        conds = []
        for v in _district_variants(district):
            conds.append(GeoMarket.district_name.ilike(v))
        if state:
            conds.append(GeoMarket.state_name.ilike(state.strip()))
        stmt = (select(GeoMarket).where(or_(*conds)).order_by(GeoMarket.name).limit(limit))
        rows = (await db.execute(stmt)).scalars().all()
        # Prefer exact district matches first (state-only fallback last).
        cores = {v.lower() for v in _district_variants(district)}
        rows = sorted(rows, key=lambda m: (
            0 if (m.district_name or "").strip().lower() in cores else 1, m.name))
        return list(rows)
    res = await db.execute(select(GeoMarket).order_by(GeoMarket.name).limit(limit))
    return list(res.scalars().all())


async def _latest_price(db: AsyncSession, state: str | None, district: str | None,
                        market: str, commodity: str | None) -> dict | None:
    stmt = select(MarketPrice).where(MarketPrice.market.ilike(market))
    if state:
        stmt = stmt.where(MarketPrice.state.ilike(state))
    if district:
        stmt = stmt.where(MarketPrice.district.ilike(district))
    if commodity:
        stmt = stmt.where(MarketPrice.commodity.ilike(commodity))
    stmt = stmt.order_by(desc(MarketPrice.arrival_date)).limit(1)
    row = (await db.execute(stmt)).scalars().first()
    if row is None:
        return None
    return {"commodity": row.commodity, "variety": row.variety,
            "grade": row.grade, "modal_price": row.modal_price,
            "price_per_unit": row.price_per_unit or "INR/quintal",
            "arrival_date": row.arrival_date.isoformat() if row.arrival_date else None,
            "arrivals": row.arrivals, "source": row.source or "AGMARKNET"}


async def _ensure_market_coords(db: AsyncSession, market: GeoMarket,
                                budget: list[int]) -> None:
    """Resolve missing market coordinates via the geocoder (bounded per
    call), persist with provenance. Never invents coordinates."""
    if market.latitude is not None and market.longitude is not None:
        return
    if budget[0] <= 0:
        return
    budget[0] -= 1
    res = await geocoder.geocode_market(market.name, market.district_name or None,
                                        market.state_name or None)
    if res is None:
        return
    market.latitude = res.latitude
    market.longitude = res.longitude
    market.coordinate_source = res.source
    market.coordinates_updated_at = datetime.now(timezone.utc)
    await db.flush()


async def nearby_markets(db: AsyncSession, lat: float | None, lng: float | None,
                         radius_km: float = NEARBY_DEFAULT_KM,
                         district: str | None = None, state: str | None = None,
                         commodity: str | None = None,
                         limit: int = 10) -> dict:
    """Markets near a location with latest reported prices.

    Candidate set comes from the geo catalog (district/state match when
    known, else a bounded national slice); distances use haversine over
    verified coordinates only. Without coordinates there is no distance:
    district/state-anchored listings return catalog markets sorted by name
    with distance omitted. Markets without coordinates are reported in
    `unmapped_count` — listed, never placed on the map."""
    if (lat is None) != (lng is None):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "MISSING_LOCATION",
                    "message": "Provide both lat and lng, or neither (with district/state)."})
    if lat is not None:
        validate_coords(lat, lng)
    if lat is None and not (district or state):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "MISSING_LOCATION",
                    "message": "Provide lat+lng or a state/district filter."})
    radius_km = max(1.0, min(float(radius_km or NEARBY_DEFAULT_KM), 100.0))
    limit = max(1, min(int(limit or 10), 50))

    candidates: list[GeoMarket] = await _catalog_markets(db, state, district)

    budget = [NEARBY_MAX_RESOLVE_PER_CALL]
    # Converging resolution: markets that already have verified coordinates
    # cost nothing. Live geocoding only runs while the mapped set is still
    # smaller than the requested limit, so repeat visits stay fast and the
    # district cache fills in over time instead of re-resolving forever.
    already = [m for m in candidates if m.latitude is not None and m.longitude is not None]
    need = max(0, limit - len(already))
    if need:
        for m in candidates:
            if m.latitude is not None and m.longitude is not None:
                continue
            if need <= 0:
                break
            await _ensure_market_coords(db, m, budget)
            need -= 1
    scored: list[tuple[float | None, GeoMarket]] = []
    unmapped = 0
    for m in candidates:
        if m.latitude is None or m.longitude is None:
            unmapped += 1
            continue
        dist = (haversine_km(lat, lng, float(m.latitude), float(m.longitude))
                if lat is not None else None)
        if lat is not None and not (district or state) and dist is not None and dist > radius_km:
            continue
        scored.append((dist, m))
    if lat is not None:
        scored.sort(key=lambda t: t[0] if t[0] is not None else 0.0)
    else:
        scored.sort(key=lambda t: (t[1].state_name or "", t[1].district_name or "", t[1].name))
    mapped: list[dict] = []
    for dist, m in scored[:limit]:
        price = await _latest_price(db, m.state_name or None,
                                    m.district_name or None, m.name, commodity)
        mapped.append({"name": m.name, "district": m.district_name or None,
                       "state": m.state_name or None,
                       "latitude": float(m.latitude), "longitude": float(m.longitude),
                       "coordinate_source": m.coordinate_source or "unknown",
                       "distance_km": round(dist, 1) if dist is not None else None,
                       "latest": price})
    return {"markets": mapped, "unmapped_count": unmapped,
            "radius_km": radius_km,
            "district": district, "state": state}


async def viewport_markets(db: AsyncSession, min_lat: float, min_lng: float,
                           max_lat: float, max_lng: float,
                           commodity: str | None = None,
                           limit: int = 200) -> dict:
    """Markets with verified coordinates inside a viewport bbox. Only
    cached coordinates are used here (no live geocoding at pan/zoom)."""
    for v, lo, hi in ((min_lat, -90, 90), (max_lat, -90, 90),
                      (min_lng, -180, 180), (max_lng, -180, 180)):
        if not (lo <= v <= hi):
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "INVALID_BBOX", "message": "Viewport bounds out of range."})
    limit = max(1, min(int(limit or 200), 200))
    stmt = (select(GeoMarket)
            .where(GeoMarket.latitude.is_not(None), GeoMarket.longitude.is_not(None),
                   GeoMarket.latitude >= min(min_lat, max_lat),
                   GeoMarket.latitude <= max(min_lat, max_lat),
                   GeoMarket.longitude >= min(min_lng, max_lng),
                   GeoMarket.longitude <= max(min_lng, max_lng))
            .order_by(GeoMarket.name).limit(limit))
    rows = (await db.execute(stmt)).scalars().all()
    out = []
    for m in rows:
        price = await _latest_price(db, m.state_name or None,
                                    m.district_name or None, m.name, commodity)
        out.append({"name": m.name, "district": m.district_name or None,
                    "state": m.state_name or None,
                    "latitude": float(m.latitude), "longitude": float(m.longitude),
                    "coordinate_source": m.coordinate_source or "unknown",
                    "distance_km": None, "latest": price})
    return {"markets": out, "unmapped_count": 0, "radius_km": None,
            "district": None, "state": None}


async def location_weather(db: AsyncSession, lat: float, lng: float) -> dict:
    """Summarized weather for map coordinates via the existing weather
    service (Open-Meteo, H3-indexed). Refreshes from the provider when no
    record exists or the latest is stale; otherwise serves the stored row
    with its real timestamp (never "live")."""
    from repositories.weather import weather_repository
    from services.weather import weather_service

    validate_coords(lat, lng)
    try:
        import h3 as h3lib
        cell = h3lib.latlng_to_cell(lat, lng, 7)
    except Exception:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "WEATHER_UNAVAILABLE",
                    "message": "Weather information is temporarily unavailable."})
    record = await weather_repository.get_latest_by_h3(db, cell)
    fetched_now = False
    if record is None or _stale(record):
        try:
            record = await weather_service.fetch_and_store_weather(db, lat, lon=lng, h3_index=cell)
            fetched_now = True
        except Exception:
            if record is None:
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail={"code": "WEATHER_UNAVAILABLE",
                            "message": "Weather information is temporarily unavailable."})
    return {"latitude": lat, "longitude": lng, "h3_index": cell,
            "temperature_c": getattr(record, "temperature", None),
            "feels_like_c": getattr(record, "feels_like", None),
            "humidity_pct": getattr(record, "humidity", None),
            "rain_mm": getattr(record, "rain_1h", None),
            "wind_speed": getattr(record, "wind_speed", None),
            "wind_deg": getattr(record, "wind_deg", None),
            "condition": getattr(record, "weather_main", None),
            "recorded_at": (record.recorded_at.isoformat()
                            if getattr(record, "recorded_at", None) else None),
            "fetched_now": fetched_now, "source": "open-meteo"}


def _stale(record) -> bool:
    ts = getattr(record, "recorded_at", None)
    if ts is None:
        return True
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - ts).total_seconds() > WEATHER_REFRESH_HOURS * 3600
