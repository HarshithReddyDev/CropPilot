"""CropContextProvider + transparent suitability engine.

Common crops: derived from CropPilot's own AGMARKNET mandi arrivals
(top commodities by arrival volume per district over the trailing 12
months). This is MARKET-OBSERVED trade mix — labelled exactly as such —
not a claim about what is grown, and never "best".

Suitability: rule-based environmental estimate from explicit,
textbook crop-requirement thresholds (rainfall, temperature, texture,
pH, organic carbon). No weights, no scores — each factor yields
suitable/marginal/unsuitable, the band is the worst factor, and every
limitation is listed. Irrigation access is unknown to the map, so any
water-demanding crop carries that limitation by construction.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.agri_cache import CropContextCache
from models.market import MarketPrice

SOURCE = "agmarknet"
CACHE_TTL_DAYS = 7
LOOKBACK_DAYS = 365
TOP_N = 8


async def get_crop_context(db: AsyncSession, district: str | None,
                           state: str | None) -> dict:
    """Top traded commodities for a district. District required (crops are
    district statistics); without one the section is honestly empty."""
    if not district:
        return {"status": "unavailable", "data": None, "source": SOURCE,
                "reason": "district-required"}
    key_d, key_s = district.strip(), (state or "").strip()
    row = (await db.execute(
        select(CropContextCache).where(CropContextCache.district.ilike(key_d),
                                       CropContextCache.state.ilike(key_s or "%"))
    )).scalars().first()
    if row is not None and row.payload:
        age = (datetime.now(timezone.utc) - row.fetched_at).days \
            if row.fetched_at and row.fetched_at.tzinfo else 9999
        if age < CACHE_TTL_DAYS:
            return {"status": "available", "data": row.payload, "source": SOURCE,
                    "from_cache": True, "data_year": row.data_year}
    since = date.today() - timedelta(days=LOOKBACK_DAYS)
    stmt = (select(MarketPrice.commodity,
                   func.sum(MarketPrice.arrivals).label("arrivals"),
                   func.count(MarketPrice.id).label("obs"))
            .where(MarketPrice.district.ilike(key_d),
                   MarketPrice.arrival_date >= since)
            .group_by(MarketPrice.commodity)
            .order_by(func.sum(MarketPrice.arrivals).desc().nullslast())
            .limit(TOP_N))
    if key_s:
        stmt = stmt.where(MarketPrice.state.ilike(key_s))
    rows = (await db.execute(stmt)).all()
    if not rows:
        return {"status": "unavailable", "data": None, "source": SOURCE,
                "reason": "no-arrivals"}
    total = sum(float(r.arrivals or 0) for r in rows) or 1.0
    common = [{"commodity": r.commodity,
               "arrival_share": round(float(r.arrivals or 0) / total, 3),
               "observations": int(r.obs)} for r in rows]
    payload = {"common": common,
               "window_days": LOOKBACK_DAYS,
               "district": key_d, "state": key_s or None,
               "interpretation": ("Commodities recently traded in this district's mandis "
                                  "(share of arrival volume). Market-observed trade mix — "
                                  "not a farm survey of what is grown.")}
    data_year = f"{(date.today() - timedelta(days=LOOKBACK_DAYS)).year}–{date.today().year}"
    try:
        if row is None:
            row = CropContextCache(district=key_d, state=key_s)
            db.add(row)
        row.payload = payload
        row.data_year = data_year
        row.source = SOURCE
        row.row_count = len(rows)
        row.fetched_at = datetime.now(timezone.utc)
        await db.flush()
    except Exception:
        pass
    return {"status": "available", "data": payload, "source": SOURCE,
            "from_cache": False, "data_year": data_year}


# ---------------------------------------------------------------------------
# Suitability engine. Requirement tables are explicit agronomic thresholds
# (rainfall mm/season, mean temperature °C, texture classes, pH range,
# organic-carbon % floor). A factor outside its range caps the band; the
# final band is the minimum across factors. No weights, no numeric scores.
# ---------------------------------------------------------------------------

CROP_REQUIREMENTS: dict[str, dict] = {
    "paddy": {"rain_min": 1000, "rain_opt": 1250, "temp": (20, 35),
              "textures": {"clay", "clay loam", "silty clay loam", "silty clay", "loam"},
              "ph": (5.5, 8.0), "oc_min": 0.4, "needs_water": True,
              "note": "Standing water needed; without known irrigation, rainfall must do the work."},
    "cotton": {"rain_min": 500, "rain_opt": 1000, "temp": (18, 32),
               "textures": {"clay", "clay loam", "sandy clay loam", "loam"},
               "ph": (6.0, 8.0), "oc_min": 0.3, "needs_water": False,
               "note": "Prefers deep moisture-retentive soils; waterlogging harmful."},
    "maize": {"rain_min": 500, "rain_opt": 750, "temp": (18, 30),
              "textures": {"loam", "silt loam", "sandy loam", "clay loam"},
              "ph": (5.5, 7.5), "oc_min": 0.3, "needs_water": False,
              "note": "Needs well-drained soils; sensitive to waterlogging."},
    "groundnut": {"rain_min": 500, "rain_opt": 700, "temp": (22, 32),
                  "textures": {"sandy loam", "loam", "loamy sand"},
                  "ph": (6.0, 7.5), "oc_min": 0.2, "needs_water": False,
                  "note": "Needs light, well-drained soils for pegging."},
    "soybean": {"rain_min": 600, "rain_opt": 900, "temp": (20, 30),
                "textures": {"loam", "silt loam", "clay loam"},
                "ph": (6.0, 7.5), "oc_min": 0.3, "needs_water": False,
                "note": "Needs assured moisture at flowering/pod-filling."},
    "sorghum": {"rain_min": 400, "rain_opt": 600, "temp": (22, 34),
                "textures": {"loam", "clay loam", "sandy loam", "silt loam"},
                "ph": (5.5, 8.5), "oc_min": 0.2, "needs_water": False,
                "note": "Drought-tolerant; suits low-rainfall areas."},
    "chickpea": {"rain_min": 300, "rain_opt": 500, "temp": (15, 28),
                 "textures": {"loam", "silt loam", "clay loam", "sandy loam"},
                 "ph": (6.0, 8.0), "oc_min": 0.2, "needs_water": False,
                 "note": "Rabi crop; grown on residual moisture, sensitive to excess rain."},
    "wheat": {"rain_min": 350, "rain_opt": 600, "temp": (12, 25),
              "textures": {"loam", "silt loam", "clay loam"},
              "ph": (6.0, 8.0), "oc_min": 0.3, "needs_water": True,
              "note": "Rabi crop; needs cool season and usually irrigation."},
    "sugarcane": {"rain_min": 1200, "rain_opt": 1500, "temp": (20, 35),
                  "textures": {"loam", "clay loam", "silt loam"},
                  "ph": (6.0, 8.0), "oc_min": 0.4, "needs_water": True,
                  "note": "Year-long high water demand; assured irrigation normally required."},
    "potato": {"rain_min": 400, "rain_opt": 600, "temp": (12, 24),
               "textures": {"sandy loam", "loam", "silt loam"},
               "ph": (5.0, 7.0), "oc_min": 0.3, "needs_water": False,
               "note": "Needs cool nights and loose, well-drained soils."},
    "tomato": {"rain_min": 400, "rain_opt": 600, "temp": (18, 28),
               "textures": {"sandy loam", "loam", "silt loam", "clay loam"},
               "ph": (5.5, 7.5), "oc_min": 0.3, "needs_water": True,
               "note": "Needs reliable moisture and well-drained soils."},
    "chilli": {"rain_min": 600, "rain_opt": 850, "temp": (20, 30),
               "textures": {"sandy loam", "loam", "silt loam", "clay loam"},
               "ph": (5.5, 7.0), "oc_min": 0.3, "needs_water": True,
               "note": "Needs warm conditions and well-drained soils."},
    "brinjal": {"rain_min": 600, "rain_opt": 900, "temp": (20, 30),
                "textures": {"sandy loam", "loam", "silt loam", "clay loam"},
                "ph": (5.5, 7.0), "oc_min": 0.3, "needs_water": True,
                "note": "Needs warm conditions and reliable moisture."},
    "bhindi": {"rain_min": 600, "rain_opt": 800, "temp": (20, 30),
               "textures": {"sandy loam", "loam", "silt loam"},
               "ph": (6.0, 7.5), "oc_min": 0.2, "needs_water": True,
               "note": "Okra needs warm conditions and reliable moisture."},
    "onion": {"rain_min": 350, "rain_opt": 450, "temp": (12, 24),
              "textures": {"sandy loam", "loam", "silt loam"},
              "ph": (6.0, 7.0), "oc_min": 0.2, "needs_water": True,
              "note": "Rabi crop; needs cool season and reliable moisture."},
}

# Traded-commodity names rarely match requirement keys verbatim.
CROP_ALIASES = {
    "ladies finger": "bhindi", "ladies_finger": "bhindi", "okra": "bhindi",
    "eggplant": "brinjal", "mirchi": "chilli", "dhan": "rice",
    "makka": "maize", "jowar": "sorghum", "bajra": "pearl_millet",
    "tur": "pigeon_pea", "chana": "chickpea", "urad": "black_gram",
    "moong": "green_gram", "til": "sesame",
}


def _crop_key(name: str) -> str:
    import re

    base = re.sub(r"\([^)]*\)", "", name or "").strip().lower()
    base = base.replace(" ", "_")
    return CROP_ALIASES.get(base, base)

DISCLAIMER = ("Suitability is an environmental estimate, not a guarantee of yield or "
              "profitability. Local soil tests, irrigation access and farm conditions "
              "can change the result.")


def _band_for(crop: str, req: dict, rain_mm: float | None,
              temp_c: float | None, texture: str | None,
              ph: float | None, oc_pct: float | None) -> dict:
    factors: list[str] = []
    limits: list[str] = []
    level = 2  # 2 high, 1 moderate, 0 low

    def cap(to: int, why: str):
        nonlocal level
        if to < level:
            level = to
        if to < 2:
            limits.append(why)
        else:
            factors.append(why)

    if rain_mm is None:
        cap(1, "seasonal rainfall unknown")
    elif rain_mm < req["rain_min"]:
        cap(0, f"season rainfall {rain_mm:.0f} mm below {req['rain_min']} mm minimum")
    elif rain_mm < req["rain_opt"]:
        cap(1, f"season rainfall {rain_mm:.0f} mm below {req['rain_opt']} mm optimum")
    else:
        factors.append(f"season rainfall {rain_mm:.0f} mm in range")
    if req.get("needs_water"):
        # Irrigation access is unknown to the map: a water-demanding crop
        # can never exceed Moderate on rainfall evidence alone.
        if level == 2:
            level = 1
        limits.append("irrigation access unknown to the map")
    if temp_c is None:
        cap(1, "temperature unknown")
    else:
        lo, hi = req["temp"]
        if temp_c < lo - 3 or temp_c > hi + 3:
            cap(0, f"mean temperature {temp_c:.1f}°C outside {lo}–{hi}°C range")
        elif temp_c < lo or temp_c > hi:
            cap(1, f"mean temperature {temp_c:.1f}°C at edge of {lo}–{hi}°C range")
        else:
            factors.append(f"temperature {temp_c:.1f}°C in range")
    if not texture:
        cap(1, "soil texture unknown")
    elif texture not in req["textures"]:
        cap(0, f"{texture} soil outside preferred textures")
    else:
        factors.append(f"{texture} soil suitable")
    if ph is None:
        cap(1, "soil pH unknown")
    else:
        lo, hi = req["ph"]
        if ph < lo - 0.5 or ph > hi + 0.5:
            cap(0, f"soil pH {ph:.1f} outside {lo}–{hi} range")
        elif ph < lo or ph > hi:
            cap(1, f"soil pH {ph:.1f} at edge of {lo}–{hi} range")
        else:
            factors.append(f"soil pH {ph:.1f} in range")
    if oc_pct is None:
        cap(1, "organic carbon unknown")
    elif oc_pct < req["oc_min"]:
        cap(1, f"organic carbon {oc_pct:.2f}% below {req['oc_min']}% guide")
    else:
        factors.append(f"organic carbon {oc_pct:.2f}% adequate")
    band = ["Low", "Moderate", "High"][level]
    return {"crop": crop, "suitability_band": band, "factors": factors,
            "limitations": limits, "note": req["note"]}


def estimate_suitability(common: list[str], rain_mm: float | None,
                         temp_c: float | None, texture: str | None,
                         ph: float | None, oc_pct: float | None) -> list[dict]:
    """Suitability for the district's traded crops only (never invents
    candidates). Empty inputs -> empty list (no estimate), never defaults."""
    out = []
    for crop in common:
        key = _crop_key(crop)
        req = CROP_REQUIREMENTS.get(key)
        if req is None:
            continue
        out.append(_band_for(crop, req, rain_mm, temp_c, texture, ph, oc_pct))
    order = {"High": 0, "Moderate": 1, "Low": 2}
    out.sort(key=lambda e: (order[e["suitability_band"]], e["crop"]))
    return out
