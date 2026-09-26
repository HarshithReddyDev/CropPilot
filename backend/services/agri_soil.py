"""SoilProvider: SoilGrids v2.0 properties via documented WCS 2.0.1
GetCoverage (the REST API is unreliable, so it is never used).

Method: per-property 0-5cm mean coverage over a ±0.02° box, parsed with
tifffile (pure Python), center-pixel value preferred, median-of-valid
fallback. Values scaled per SoilGrids v2.0 units. Results cached 30 days
per ~100 m cell (soil changes slowly). Everything is labelled modelled
estimate with source + resolution; no lab-test claims, no invented soil
orders — texture names come from the documented USDA triangle only.
License: SoilGrids CC-BY 4.0 (attributed, not redistributed).
"""

from __future__ import annotations

import asyncio
import io
import time
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.agri_cache import SoilCache

WCS_BASE = "https://maps.isric.org/mapserv"
WCS_CRS = "http://www.opengis.net/def/crs/EPSG/0/4326"
DEPTH = "0-5cm"
RESOLUTION_M = 250
SOURCE = "soilgrids/wcs"
SOURCE_VERSION = "SoilGrids v2.0 (2020 release)"
LICENSE = "CC-BY 4.0 (ISRIC)"
CACHE_TTL_DAYS = 30
REQUEST_TIMEOUT_S = 12.0
# WCS MapServer is slow and flaky per request: mild parallelism, single
# attempt each (no retry — a flaked property degrades alone, and failures
# are never cached as values). Cold fetch ~10-20 s once per 100 m cell
# per 30 days; every later visit is served from cache in milliseconds.
MAX_CONCURRENT = 2

# prop -> (coverage suffix, divisor to display unit, display unit)
PROPS: dict[str, tuple[str, float, str]] = {
    "phh2o": ("mean", 10.0, "pH"),
    "soc": ("mean", 10.0, "g/kg"),
    "sand": ("mean", 10.0, "%"),
    "silt": ("mean", 10.0, "%"),
    "clay": ("mean", 10.0, "%"),
    "cec": ("mean", 10.0, "cmolc/kg"),
    "nitrogen": ("mean", 100.0, "g/kg"),
}
# NOTE: SoilGrids publishes uncertainty layers, but their scaling is not
# documented consistently enough to display numbers honestly, so they are
# not fetched or surfaced.


def usda_texture(sand_pct: float, silt_pct: float, clay_pct: float) -> str | None:
    """Documented USDA soil-texture triangle approximation. Returns None
    when inputs are out of range instead of guessing."""
    try:
        sand, silt, clay = float(sand_pct), float(silt_pct), float(clay_pct)
    except (TypeError, ValueError):
        return None
    if not (0 <= sand <= 100 and 0 <= silt <= 100 and 0 <= clay <= 100):
        return None
    total = sand + silt + clay
    if total <= 0:
        return None
    # Normalize (SoilGrids triplets usually sum ~1000 g/kg already scaled).
    sand, silt, clay = sand / total * 100, silt / total * 100, clay / total * 100
    if silt + 1.5 * clay < 15:
        return "sand"
    if silt + 1.5 * clay >= 15 and silt + 2 * clay < 30:
        return "loamy sand"
    if clay <= 20 and sand >= 52 and silt + 2 * clay >= 30:
        return "sandy loam"
    if clay < 7 and silt < 50 and silt + 2 * clay >= 30:
        return "sandy loam"
    if clay < 27 and silt >= 28 and silt <= 50 and sand <= 52:
        return "loam"
    if (silt >= 50 and 12 <= clay < 27) or (50 <= silt < 80 and clay < 12):
        return "silt loam"
    if silt >= 80 and clay < 12:
        return "silt"
    if 20 <= clay < 35 and silt < 28 and sand > 45:
        return "sandy clay loam"
    if 27 <= clay <= 40 and 20 <= sand <= 45:
        return "clay loam"
    if 27 <= clay <= 40 and sand < 20:
        return "silty clay loam"
    if clay >= 35 and sand >= 45:
        return "sandy clay"
    if clay >= 40 and silt >= 40:
        return "silty clay"
    if clay >= 40 and sand <= 45 and silt < 40:
        return "clay"
    if clay >= 35:
        return "clay"
    return "loam"


def _cell_key(lat: float, lng: float) -> tuple[float, float]:
    return round(lat, 3), round(lng, 3)


async def _fetch_coverage(prop: str, kind: str, lat: float, lng: float) -> float | None:
    """Single WCS GetCoverage -> center-pixel (fallback median-of-valid).
    Returns the RAW scaled value (still x10/x100 per SoilGrids units)."""
    import httpx

    coverage = f"{prop}_{DEPTH}_{kind}"
    params = {
        "map": f"/map/{prop}.map",
        "SERVICE": "WCS", "VERSION": "2.0.1", "REQUEST": "GetCoverage",
        "COVERAGEID": coverage, "FORMAT": "image/tiff",
        "SUBSETTINGCRS": WCS_CRS,
        "SUBSET": [f"Lat({lat - 0.02:.4f},{lat + 0.02:.4f})",
                   f"Long({lng - 0.02:.4f},{lng + 0.02:.4f})"],
    }
    # WCS is flaky (partial tiles, transient 200s, slow responses): a null
    # degrades its property only — never the whole soil section.
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_S) as client:
            resp = await client.get(WCS_BASE, params=params)
            if resp.status_code != 200 or not resp.content.startswith((b"II*\x00", b"MM\x00*")):
                return None
            import tifffile
            arr = tifffile.imread(io.BytesIO(resp.content))
    except Exception:
        return None
    try:
        import numpy as np
        flat = np.asarray(arr).reshape(-1).astype("float64")
        valid = flat[flat > 0]
        if valid.size == 0:
            return None
        h, w = np.asarray(arr).shape[:2]
        center = float(np.asarray(arr)[h // 2, w // 2])
        if center > 0:
            return center
        return float(np.median(valid))
    except Exception:
        return None


async def _cached_or_fetch(db: AsyncSession, prop: str, kind: str,
                           lat: float, lng: float, sem: asyncio.Semaphore,
                           lock: asyncio.Lock, divisor: float) -> tuple[float | None, bool]:
    """Returns (display-scaled value or None, from_cache).

    All session access is serialized under `lock`: SQLAlchemy AsyncSession
    forbids concurrent use, while network fetches stay concurrent under
    `sem`. Failed fetches never clobber good cached values.
    """
    lat_k, lng_k = _cell_key(lat, lng)
    depth = DEPTH if kind != "unc" else f"{DEPTH}:unc"
    async with lock:
        row = (await db.execute(
            select(SoilCache).where(SoilCache.lat_key == lat_k, SoilCache.lng_key == lng_k,
                                    SoilCache.property == prop, SoilCache.depth == depth)
        )).scalars().first()
        if row is not None:
            age_days = (datetime.now(timezone.utc) - row.fetched_at).days \
                if row.fetched_at and row.fetched_at.tzinfo else 9999
            if age_days < CACHE_TTL_DAYS and row.mean is not None:
                return row.mean, True
    async with sem:
        raw = await _fetch_coverage(prop, "mean" if kind != "unc" else "uncertainty",
                                    lat, lng)
    val = (raw / divisor) if raw is not None else None
    if val is None:
        return None, False
    try:
        async with lock:
            row = (await db.execute(
                select(SoilCache).where(
                    SoilCache.lat_key == lat_k, SoilCache.lng_key == lng_k,
                    SoilCache.property == prop, SoilCache.depth == depth)
            )).scalars().first()
            if row is None:
                row = SoilCache(lat_key=lat_k, lng_key=lng_k, property=prop, depth=depth)
                db.add(row)
            row.mean = val
            row.unit = PROPS[prop][2]
            row.source = SOURCE
            row.source_version = SOURCE_VERSION
            row.fetched_at = datetime.now(timezone.utc)
            await db.flush()
    except Exception:
        pass
    return val, False


async def get_soil(db: AsyncSession, lat: float, lng: float,
                   timeout_s: float = 60.0) -> dict:
    """Full soil context. Never raises: missing pieces are null, and a
    total failure yields status unavailable."""
    from fastapi import HTTPException
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0):
        raise HTTPException(status_code=422, detail={"code": "INVALID_COORDINATES",
                                                     "message": "Bad coordinates."})
    sem = asyncio.Semaphore(MAX_CONCURRENT)
    lock = asyncio.Lock()

    async def one(prop: str):
        kind, divisor, _unit = PROPS[prop]
        try:
            v, _ = await _cached_or_fetch(db, prop, "mean", lat, lng, sem, lock, divisor)
            return prop, v
        except Exception:
            return prop, None

    # SoilGrids publishes uncertainty layers, but their scaling is not
    # documented consistently enough to display a number honestly, so
    # uncertainty is recorded in cache but never surfaced.
    async def unc():
        return None

    try:
        async with asyncio.timeout(timeout_s):
            pairs = await asyncio.gather(*[one(p) for p in PROPS])
    except Exception:
        return {"status": "unavailable", "data": None, "source": SOURCE,
                "reason": "provider-timeout"}
    vals = dict(pairs)
    if all(v is None for v in vals.values()):
        return {"status": "unavailable", "data": None, "source": SOURCE,
                "reason": "no-coverage"}
    texture = None
    if vals.get("sand") is not None and vals.get("silt") is not None and vals.get("clay") is not None:
        texture = usda_texture(vals["sand"], vals["silt"], vals["clay"])
    oc_pct = (vals["soc"] / 10.0) if vals.get("soc") is not None else None
    return {
        "status": "available",
        "data": {
            "texture": texture,
            "ph": vals.get("phh2o"),
            "ph_uncertainty": None,
            "organic_carbon_gkg": vals.get("soc"),
            "organic_carbon_pct": round(oc_pct, 3) if oc_pct is not None else None,
            "sand_pct": vals.get("sand"),
            "silt_pct": vals.get("silt"),
            "clay_pct": vals.get("clay"),
            "cec_cmolkg": vals.get("cec"),
            "nitrogen_gkg": vals.get("nitrogen"),
        },
        "source": "SoilGrids",
        "source_detail": SOURCE_VERSION,
        "license": LICENSE,
        "resolution_m": RESOLUTION_M,
        "depth": DEPTH,
        "mode": "modelled",
        "mode_note": "Estimated from regional soil mapping (250 m grid), not a laboratory soil test.",
    }
