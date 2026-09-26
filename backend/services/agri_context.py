"""Aggregated agricultural context for one map selection.

One endpoint, service-level separation, bounded concurrency: every
provider runs under its own timeout and fails to an explicit
{status: unavailable} section instead of failing the response.
Nothing here invents data — see each provider's module for provenance.
"""

from __future__ import annotations

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from services import agri_crops, agri_rain, agri_soil, agri_water, map_service

PROVIDER_TIMEOUT_S = 75.0


async def _section(coro, name: str) -> dict:
    try:
        async with asyncio.timeout(PROVIDER_TIMEOUT_S):
            return await coro
    except Exception as e:
        return {"status": "unavailable", "data": None, "source": name,
                "reason": f"{type(e).__name__}"}


async def agricultural_context(db: AsyncSession, lat: float, lng: float,
                               district: str | None = None,
                               state: str | None = None) -> dict:
    map_service.validate_coords(lat, lng)

    # One session per DB-touching provider: SQLAlchemy AsyncSession forbids
    # concurrent use, and providers fan out concurrently below. `db`
    # (request session) is used sequentially afterwards.
    from db.session import async_session_factory

    soil_db = async_session_factory()
    wx_db = async_session_factory()
    try:
        rev_task = map_service.reverse_place(lat, lng)
        rain_task = agri_rain.get_rainfall(lat, lng)
        soil_task = agri_soil.get_soil(soil_db, lat, lng)
        wx_task = map_service.location_weather(wx_db, lat, lng)
        water_task = agri_water.get_water_context(db, lat, lng, district, state)
        rev, rain, soil, wx, water = await asyncio.gather(
            _section(rev_task, "nominatim"),
            _section(rain_task, "open-meteo"),
            _section(soil_task, "soilgrids"),
            _section(wx_task, "open-meteo"),
            _section(water_task, "water"),
            return_exceptions=False,
        )
        # Provider sessions are private: commit what they staged (soil and
        # weather caches) so later visits hit cache. Failures roll back.
        for s in (soil_db, wx_db):
            try:
                await s.commit()
            except Exception:
                try:
                    await s.rollback()
                except Exception:
                    pass
    finally:
        for s in (soil_db, wx_db):
            try:
                await s.close()
            except Exception:
                pass
    eff_district = district or (rev.get("district") if isinstance(rev, dict) else None)
    eff_state = state or (rev.get("state") if isinstance(rev, dict) else None)
    crops = await _section(agri_crops.get_crop_context(db, eff_district, eff_state),
                           "agmarknet")

    soil_d = soil.get("data") or {}
    rain_d = rain.get("data") or {}
    # Suitability needs a representative season total: with <70% of the
    # season observed (archive window limits), rainfall is unknown rather
    # than misleadingly low.
    season_cov = 0.0
    if rain_d.get("season_days_total"):
        season_cov = (rain_d.get("season_days_covered") or 0) / rain_d["season_days_total"]
    season_rain = rain_d.get("season_mm") if season_cov >= 0.7 else None
    wx_temp = (wx.get("temperature_c") if isinstance(wx, dict) else None)
    common_names = [c.get("commodity") for c in (crops.get("data") or {}).get("common", [])
                    if c.get("commodity")] if isinstance(crops, dict) else []
    suitability = agri_crops.estimate_suitability(
        common_names,
        season_rain,
        wx_temp,
        soil_d.get("texture"),
        soil_d.get("ph"),
        (soil_d.get("organic_carbon_pct")),
    ) if isinstance(crops, dict) and crops.get("status") == "available" else []
    disease = agri_water.get_disease_context(common_names)

    wx_section = wx if isinstance(wx, dict) and wx.get("status") == "unavailable" \
        else ({"status": "available", "data": wx} if isinstance(wx, dict) else wx)
    snapshot_crops = [c for c in common_names[:3]]
    return {
        "location": {"latitude": lat, "longitude": lng,
                     "locality": rev.get("locality"), "district": eff_district,
                     "state": eff_state, "country": rev.get("country")},
        "snapshot": {
            "common_crops": snapshot_crops,
            "soil": {"texture": soil_d.get("texture"), "ph": soil_d.get("ph")},
            "season_rain_mm": season_rain,
            "season_label": rain_d.get("season_label"),
            "disease_names": [d["display_name"] for r in
                              (disease.get("data") or {}).get("crop_risks", [])[:2]
                              for d in r.get("diseases", [])[:2]],
        },
        "weather": wx_section,
        "rainfall": rain,
        "soil": soil,
        "crops": crops,
        "suitability": {"status": "available" if suitability else "unavailable",
                        "data": {"estimates": suitability,
                                 "disclaimer": agri_crops.DISCLAIMER} if suitability else None,
                        "source": "CropPilot suitability engine (rule-based)",
                        "mode": "derived",
                        "mode_note": ("Environmental estimate from soil + rainfall + temperature "
                                      "thresholds; no weights or scores.")},
        "water": water,
        "disease_context": disease,
        "sources": ["open-meteo", "soilgrids", "agmarknet", "nominatim",
                    "croppilot-taxonomy"],
    }
