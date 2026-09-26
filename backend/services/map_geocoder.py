"""Geocoder provider adapter for the map experience.

Default provider: OpenStreetMap Nominatim (documented, no API key).
All network interaction is server-side; browsers never see provider URLs.
Coordinates returned here are real third-party geodata with provenance —
never invented. Provider failures return None (callers degrade gracefully).

Nominatim usage policy is respected: single-flight throttling (>=1.1s
between requests), proper User-Agent, bounded timeouts, in-memory TTL
cache, and conservative result limits.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

NOMINATIM_BASE = "https://nominatim.openstreetmap.org"
USER_AGENT = "CropPilot/1.0 (agricultural map; contact: admin@croppilot.local)"
MIN_INTERVAL_S = 1.1
CACHE_TTL_S = 24 * 3600
REQUEST_TIMEOUT_S = 10.0
SOURCE_NAME = "nominatim/osm"


@dataclass
class GeocodeResult:
    name: str
    latitude: float
    longitude: float
    locality: str | None = None
    district: str | None = None
    state: str | None = None
    country: str | None = None
    postcode: str | None = None
    source: str = SOURCE_NAME
    raw_type: str = "place"


@dataclass
class ReverseResult:
    latitude: float
    longitude: float
    display_name: str | None = None
    locality: str | None = None
    district: str | None = None
    state: str | None = None
    country: str | None = None
    postcode: str | None = None
    source: str = SOURCE_NAME


def _pick_address(addr: dict) -> dict[str, str | None]:
    locality = (
        addr.get("village") or addr.get("town") or addr.get("city")
        or addr.get("municipality") or addr.get("hamlet") or addr.get("suburb")
    )
    district = addr.get("district") or addr.get("county") or addr.get("state_district")
    return {
        "locality": locality,
        "district": district,
        "state": addr.get("state"),
        "country": addr.get("country"),
        "postcode": addr.get("postcode"),
    }


class NominatimGeocoder:
    """Rate-limited, cached Nominatim client. Never raises on provider
    errors — returns None / [] so the map degrades instead of failing."""

    def __init__(self, base_url: str = NOMINATIM_BASE,
                 user_agent: str = USER_AGENT):
        self.base_url = base_url.rstrip("/")
        self.user_agent = user_agent
        self._lock = asyncio.Lock()
        self._last_call = 0.0
        self._cache: dict[str, tuple[float, object]] = {}

    def _get_cached(self, key: str):
        hit = self._cache.get(key)
        if hit and (time.monotonic() - hit[0]) < CACHE_TTL_S:
            return hit[1]
        return None

    def _put_cached(self, key: str, value: object) -> None:
        if len(self._cache) > 2000:
            self._cache.clear()
        self._cache[key] = (time.monotonic(), value)

    async def _get(self, path: str, params: dict) -> object | None:
        import httpx

        async with self._lock:
            wait = MIN_INTERVAL_S - (time.monotonic() - self._last_call)
            if wait > 0:
                await asyncio.sleep(wait)
            try:
                async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_S) as client:
                    resp = await client.get(
                        self.base_url + path, params=params,
                        headers={"User-Agent": self.user_agent,
                                 "Accept": "application/json"},
                    )
                    if resp.status_code != 200:
                        return None
                    return resp.json()
            except Exception:
                return None
            finally:
                self._last_call = time.monotonic()

    @staticmethod
    def _valid_coords(lat: float | None, lng: float | None) -> bool:
        return (
            lat is not None and lng is not None
            and -90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0
        )

    async def search(self, query: str, limit: int = 5) -> list[GeocodeResult]:
        q = (query or "").strip()
        if len(q) < 2:
            return []
        key = f"search:{q.lower()}:{limit}"
        hit = self._get_cached(key)
        if hit is not None:
            return hit  # type: ignore[return-value]
        data = await self._get("/search", {
            "q": q, "format": "jsonv2", "addressdetails": 1,
            "countrycodes": "in", "limit": max(1, min(limit, 10)),
            "viewbox": "68.0,37.5,97.5,6.0", "bounded": 0,
        })
        out: list[GeocodeResult] = []
        if isinstance(data, list):
            for item in data:
                try:
                    lat, lng = float(item["lat"]), float(item["lon"])
                except (KeyError, TypeError, ValueError):
                    continue
                if not self._valid_coords(lat, lng):
                    continue
                addr = item.get("address") or {}
                parts = _pick_address(addr if isinstance(addr, dict) else {})
                name = str(item.get("name") or parts["locality"]
                           or item.get("display_name", "").split(",")[0] or q)
                out.append(GeocodeResult(
                    name=name, latitude=lat, longitude=lng,
                    locality=parts["locality"], district=parts["district"],
                    state=parts["state"], country=parts["country"],
                    postcode=parts["postcode"],
                    raw_type=str(item.get("type") or item.get("class") or "place"),
                ))
        self._put_cached(key, out)
        return out

    async def reverse(self, lat: float, lng: float) -> ReverseResult | None:
        if not self._valid_coords(lat, lng):
            return None
        key = f"reverse:{round(lat, 4)}:{round(lng, 4)}"
        hit = self._get_cached(key)
        if hit is not None:
            return hit  # type: ignore[return-value]
        data = await self._get("/reverse", {
            "lat": lat, "lon": lng, "format": "jsonv2", "addressdetails": 1,
        })
        if not isinstance(data, dict):
            return None
        addr = data.get("address") or {}
        parts = _pick_address(addr if isinstance(addr, dict) else {})
        res = ReverseResult(
            latitude=lat, longitude=lng,
            display_name=(str(data.get("display_name"))[:300]
                          if data.get("display_name") else None),
            locality=parts["locality"], district=parts["district"],
            state=parts["state"], country=parts["country"],
            postcode=parts["postcode"],
        )
        self._put_cached(key, res)
        return res

    async def geocode_market(self, market: str, district: str | None,
                             state: str | None) -> GeocodeResult | None:
        """Resolve a mandi's coordinates for marker placement.

        Market names carry type suffixes ("APMC", "Rythu Bazar", ...) and
        parenthetical qualifiers ("Chandur(Mungodu)"); those are stripped /
        expanded into place-name queries so Nominatim returns the actual
        town — not a district-centroid fallback. No fallback is applied:
        returning None (unmapped) is always preferred over a false point.
        """
        import re

        base = (market or "").strip()
        variants = [base]
        paren = re.findall(r"\(([^)]+)\)", base)
        variants.extend(p.strip() for p in paren if p.strip())
        cleaned = []
        for v in variants:
            v = re.sub(r"\([^)]*\)", " ", v)
            v = re.sub(r"(?i)\b(apmc|rythu\s*baza?ar|market|mandi|yard|vegetable|fruit|onion|potato)\b",
                       " ", v)
            v = re.sub(r"\s+", " ", v).strip(" -,")
            if v and v.lower() not in {c.lower() for c in cleaned}:
                cleaned.append(v)
        ctx = ", ".join(b for b in [district, state, "India"] if b)
        for place in cleaned:
            results = await self.search(f"{place}, {ctx}" if ctx else place, limit=1)
            if results:
                return results[0]
        return None


geocoder = NominatimGeocoder()
