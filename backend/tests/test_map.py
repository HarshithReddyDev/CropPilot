"""Map service tests: validation, haversine, search blend, nearby/viewport
markets, coordinate exclusion, reverse degradation. Geocoder is mocked at
the service boundary (no network). DB tables are created selectively to
avoid unrelated PostGIS-only models."""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from models.market import MarketPrice
from models.market_geo import GeoDistrict, GeoMarket, GeoState


@pytest_asyncio.fixture
async def map_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    from db.base import Base
    tables = [t for t in Base.metadata.tables.values()
              if t.name in {"geo_states", "geo_districts", "geo_markets", "market_prices",
                            "soil_cache", "crop_context_cache"}]
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=tables)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


async def _seed(db):
    db.add(GeoState(source_id=1, name="Telangana"))
    db.add(GeoDistrict(source_id=10, name="Nalgonda", state_id=1, state_name="Telangana"))
    db.add(GeoMarket(source_id=100, name="Nalgonda Market", district_id=10,
                     district_name="Nalgonda", state_id=1, state_name="Telangana",
                     latitude=17.06, longitude=79.27, coordinate_source="test"))
    db.add(GeoMarket(source_id=101, name="Distant Market", district_id=10,
                     district_name="Nalgonda", state_id=1, state_name="Telangana",
                     latitude=28.61, longitude=77.20, coordinate_source="test"))
    db.add(GeoMarket(source_id=102, name="Unmapped Market", district_id=10,
                     district_name="Nalgonda", state_id=1, state_name="Telangana"))
    await db.flush()


def test_haversine_sanity():
    from services.map_service import haversine_km

    assert haversine_km(17.38, 78.48, 17.38, 78.48) == 0.0
    d = haversine_km(17.38, 78.48, 17.06, 79.27)  # Hyderabad -> Nalgonda
    assert 50.0 < d < 150.0


def test_validate_coords():
    import pytest as _pytest
    from fastapi import HTTPException
    from services.map_service import validate_coords

    validate_coords(17.0, 78.0)
    with _pytest.raises(HTTPException):
        validate_coords(91.0, 78.0)
    with _pytest.raises(HTTPException):
        validate_coords(17.0, 181.0)


@pytest.mark.asyncio
async def test_search_blends_local_and_provider(map_db, monkeypatch):
    from services import map_service

    async def fake_search(query, limit=5):
        from services.map_geocoder import GeocodeResult
        return [GeocodeResult(name="Nalgonda", latitude=17.06, longitude=79.27,
                              district="Nalgonda", state="Telangana")]

    monkeypatch.setattr(map_service.geocoder, "search", fake_search)
    await _seed(map_db)
    out = await map_service.search_places(map_db, "Nalgonda")
    kinds = {(r["type"], r["source"]) for r in out}
    assert ("district", "croppilot-geo-catalog") in kinds
    assert ("market", "croppilot-geo-catalog") in kinds
    assert ("place", "nominatim/osm") in kinds
    for r in out:
        assert r["name"]


@pytest.mark.asyncio
async def test_nearby_filters_sorts_and_excludes_unmapped(map_db, monkeypatch):
    from services import map_service

    async def no_resolve(db, market, budget):
        return None

    monkeypatch.setattr(map_service, "_ensure_market_coords", no_resolve)
    await _seed(map_db)
    res = await map_service.nearby_markets(map_db, 17.06, 79.27, radius_km=50.0, limit=10)
    names = [m["name"] for m in res["markets"]]
    assert names == ["Nalgonda Market"]  # distant excluded by radius
    assert res["markets"][0]["distance_km"] == 0.0
    assert res["unmapped_count"] == 1  # counted, never placed
    assert res["markets"][0]["latest"] is None  # no price rows seeded


@pytest.mark.asyncio
async def test_nearby_district_mode_needs_no_coords(map_db, monkeypatch):
    from services import map_service

    async def no_resolve(db, market, budget):
        return None

    monkeypatch.setattr(map_service, "_ensure_market_coords", no_resolve)
    await _seed(map_db)
    res = await map_service.nearby_markets(map_db, None, None, district="Nalgonda")
    assert {m["name"] for m in res["markets"]} == {"Nalgonda Market", "Distant Market"}
    assert all(m["distance_km"] is None for m in res["markets"])
    assert res["unmapped_count"] == 1


@pytest.mark.asyncio
async def test_nearby_requires_location_or_scope(map_db):
    import pytest as _pytest
    from fastapi import HTTPException
    from services import map_service

    await _seed(map_db)
    with _pytest.raises(HTTPException):
        await map_service.nearby_markets(map_db, None, None)


@pytest.mark.asyncio
async def test_viewport_bbox_and_inclusion(map_db):
    import pytest as _pytest
    from fastapi import HTTPException
    from services import map_service

    await _seed(map_db)
    with _pytest.raises(HTTPException):
        await map_service.viewport_markets(map_db, -100.0, 0.0, 10.0, 10.0)
    res = await map_service.viewport_markets(map_db, 16.0, 78.0, 18.0, 80.0)
    assert [m["name"] for m in res["markets"]] == ["Nalgonda Market"]


@pytest.mark.asyncio
async def test_reverse_degrades_to_nulls(map_db, monkeypatch):
    from services import map_service

    async def fail_reverse(lat, lng):
        return None

    monkeypatch.setattr(map_service.geocoder, "reverse", fail_reverse)
    out = await map_service.reverse_place(17.06, 79.27)
    assert out["latitude"] == 17.06 and out["district"] is None


def test_district_variants():
    from services.map_service import _district_variants

    assert _district_variants("Nalgonda mandal") == ["Nalgonda mandal", "Nalgonda"]
    assert _district_variants("Nalgonda") == ["Nalgonda"]
    assert _district_variants(None) == []


@pytest.mark.asyncio
async def test_nearby_matches_mandal_to_catalog(map_db, monkeypatch):
    from services import map_service

    async def no_resolve(db, market, budget):
        return None

    monkeypatch.setattr(map_service, "_ensure_market_coords", no_resolve)
    await _seed(map_db)
    res = await map_service.nearby_markets(
        map_db, 17.06, 79.27, district="Nalgonda mandal", state="Telangana")
    assert {m["name"] for m in res["markets"]} == {"Nalgonda Market", "Distant Market"}


def test_map_market_schema_requires_coords():
    import pytest as _pytest
    from pydantic import ValidationError
    from api.v1.endpoints.map import MapMarket

    with _pytest.raises(ValidationError):
        MapMarket(name="X")  # type: ignore[call-arg]
    ok = MapMarket(name="X", latitude=17.0, longitude=79.0)
    assert ok.coordinate_source == "unknown"


# --- agricultural intelligence ---

def test_usda_texture_triangle():
    from services.agri_soil import usda_texture

    assert usda_texture(90, 5, 5) == "sand"
    assert usda_texture(30, 30, 40) == "clay loam"
    assert usda_texture(10, 85, 5) == "silt"
    assert usda_texture(20, 20, 60) == "clay"
    assert usda_texture(40, 40, 20) == "loam"
    assert usda_texture(-5, 50, 50) is None
    assert usda_texture(0, 0, 0) is None
    assert usda_texture("x", 50, 50) is None  # type: ignore[arg-type]


def test_suitability_rules_no_weights():
    from services.agri_crops import estimate_suitability

    # Paddy with ample rain + fine texture + neutral pH: capped at Moderate
    # because irrigation access is unknown (water-demanding crop rule).
    out = estimate_suitability(["paddy"], rain_mm=1400.0, temp_c=28.0,
                               texture="clay loam", ph=7.0, oc_pct=0.8)
    assert out and out[0]["suitability_band"] == "Moderate"
    assert any("irrigation" in lim.lower() for lim in out[0]["limitations"])
    # Maize (no standing-water need) with good inputs: genuinely High.
    out = estimate_suitability(["maize"], rain_mm=800.0, temp_c=25.0,
                               texture="loam", ph=6.5, oc_pct=0.5)
    assert out[0]["suitability_band"] == "High"
    # Cotton drowned by drought: Low with explicit limitation.
    out = estimate_suitability(["cotton"], rain_mm=200.0, temp_c=28.0,
                               texture="clay", ph=7.0, oc_pct=0.5)
    assert out[0]["suitability_band"] == "Low"
    assert any("rain" in lim.lower() for lim in out[0]["limitations"])
    # Water-demanding paddy can never exceed Moderate without irrigation info.
    out = estimate_suitability(["paddy"], rain_mm=2000.0, temp_c=28.0,
                               texture="clay", ph=7.0, oc_pct=0.8)
    assert out[0]["suitability_band"] == "Moderate"
    assert any("irrigation" in lim.lower() for lim in out[0]["limitations"])
    # Unknown crops are skipped, never invented; empty inputs -> empty.
    assert estimate_suitability(["durian"], 1000.0, 25.0, "loam", 7.0, 0.5) == []
    assert estimate_suitability([], 1000.0, 25.0, "loam", 7.0, 0.5) == []
    assert estimate_suitability(["maize"], None, None, None, None, None)[0]["suitability_band"] == "Moderate"
    # Traded names with parentheticals normalize to requirement keys.
    out = estimate_suitability(["Bhindi(Ladies Finger)"], rain_mm=800.0, temp_c=28.0,
                               texture="sandy loam", ph=6.5, oc_pct=0.4)
    assert out and out[0]["crop"] == "Bhindi(Ladies Finger)"
    assert out[0]["suitability_band"] == "Moderate"  # irrigation-capped


@pytest.mark.asyncio
async def test_rainfall_aggregates_with_gaps(monkeypatch):
    from services import agri_rain

    async def fake_daily(lat, lng, start, end):
        from datetime import date, timedelta
        out = {}
        d = date.fromisoformat(start)
        e = date.fromisoformat(end)
        while d <= e:
            # Simulate a 2-day observation gap.
            if d.day % 5 not in (0, 1):
                out[d.isoformat()] = 2.0
            d += timedelta(days=1)
        return out

    monkeypatch.setattr(agri_rain, "_daily", fake_daily)
    res = await agri_rain.get_rainfall(17.05, 79.27)
    assert res["status"] == "available"
    assert res["mode"] == "modelled"
    assert "reanalysis" in res["mode_note"].lower()
    assert res["data"]["last_7d_mm"] is not None
    assert res["data"]["last_7d_coverage"].endswith("/7 days")


def test_disease_context_is_risks_not_outbreaks():
    from services import agri_water

    res = agri_water.get_disease_context(["paddy", "cotton"])
    assert res["status"] == "available"
    assert res["mode"] == "knowledge-derived"
    crops = {r["crop"] for r in res["data"]["crop_risks"]}
    assert {"rice", "cotton"} <= crops
    blob = str(res)
    assert "outbreak" not in blob.lower() or "not confirmed" in blob.lower()
    assert "%" not in blob
    assert agri_water.get_disease_context([])["status"] == "unavailable"
    assert agri_water.get_disease_context(["durian"])["status"] == "unavailable"


@pytest.mark.asyncio
async def test_water_context_honestly_unavailable(map_db):
    from services import agri_water

    res = await agri_water.get_water_context(map_db, 17.05, 79.27, "Nalgonda", "Telangana")
    assert res["status"] == "unavailable"
    assert res["groundwater"]["source"] == "CGWB"
    assert res["reservoirs"]["source"] == "CWC"


@pytest.mark.asyncio
async def test_crop_context_from_mandi_arrivals(map_db):
    from datetime import date, timedelta
    from services import agri_crops

    today = date.today()
    map_db.add(MarketPrice(
        commodity="Paddy", variety="Common", market="Nalgonda APMC",
        district="Nalgonda", state="Telangana", min_price=2000.0,
        max_price=2200.0, modal_price=2100.0, arrival_date=today - timedelta(days=10),
        arrivals=500.0, source="AGMARKNET", raw_record={}))
    map_db.add(MarketPrice(
        commodity="Cotton", variety=None, market="Nalgonda APMC",
        district="Nalgonda", state="Telangana", min_price=6000.0,
        max_price=6500.0, modal_price=6200.0, arrival_date=today - timedelta(days=5),
        arrivals=100.0, source="AGMARKNET", raw_record={}))
    await map_db.flush()
    res = await agri_crops.get_crop_context(map_db, "Nalgonda", "Telangana")
    assert res["status"] == "available"
    assert res["data"]["common"][0]["commodity"] == "Paddy"
    assert "not a farm survey" in res["data"]["interpretation"]
    assert (await agri_crops.get_crop_context(map_db, None, None))["status"] == "unavailable"


@pytest.mark.asyncio
async def test_aggregate_degrades_per_section(map_db, monkeypatch):
    from services import agri_context, agri_rain, agri_soil, map_service

    async def boom(*a, **k):
        raise RuntimeError("provider down")

    async def fake_reverse(lat, lng):
        return {"latitude": lat, "longitude": lng, "locality": "Nalgonda",
                "district": "Nalgonda", "state": "Telangana", "country": "India",
                "display_name": None, "postcode": None, "source": "test"}

    monkeypatch.setattr(map_service, "reverse_place", fake_reverse)
    monkeypatch.setattr(map_service, "location_weather", boom)
    monkeypatch.setattr(agri_rain, "get_rainfall", boom)
    monkeypatch.setattr(agri_soil, "get_soil", boom)
    res = await agri_context.agricultural_context(
        map_db, 17.05, 79.27, district="Nalgonda", state="Telangana")
    assert res["location"]["district"] == "Nalgonda"
    assert res["rainfall"]["status"] == "unavailable"
    assert res["soil"]["status"] == "unavailable"
    assert res["weather"]["status"] == "unavailable"
    assert res["water"]["status"] == "unavailable"
    # Crops still resolve from the DB; disease context follows.
    assert res["crops"]["status"] in {"available", "unavailable"}
    assert res["disease_context"]["status"] in {"available", "unavailable"}


def test_source_registry_marks_unverified():
    from services.map_data_sources import source_registry

    reg = {s["source_id"]: s for s in source_registry()}
    for sid in ("agmarknet", "open-meteo", "soilgrids", "nominatim", "carto",
                "croppilot-taxonomy"):
        assert reg[sid]["enabled"] is True, sid
    for sid in ("imd", "cgwb", "cwc", "des-ogd"):
        assert reg[sid]["enabled"] is False, sid
        assert reg[sid]["notes"]
    for s in reg.values():
        for f in ("source_id", "name", "provider", "type", "license",
                  "coverage", "granularity", "refresh_frequency", "enabled", "notes"):
            assert f in s, (s["source_id"], f)

@pytest.mark.asyncio
async def test_partial_season_rain_not_used_for_suitability(map_db, monkeypatch):
    from services import agri_context

    async def fake_reverse(lat, lng):
        return {"latitude": lat, "longitude": lng, "locality": "X",
                "district": "Nalgonda", "state": "Telangana", "country": "India",
                "display_name": None, "postcode": None, "source": "test"}

    async def fake_rain(lat, lng, timeout_s=30.0):
        return {"status": "available",
                "data": {"today_mm": 0.0, "last_7d_mm": 5.0, "month_mm": 40.0,
                         "season_mm": 150.0, "season_label": "Jun-Sep 2026",
                         "season_coverage": "50/118 days",
                         "season_days_total": 118, "season_days_covered": 50},
                "source": "Open-Meteo"}

    async def fake_soil(db, lat, lng, timeout_s=60.0):
        return {"status": "available",
                "data": {"texture": "clay loam", "ph": 7.0, "ph_uncertainty": None,
                         "organic_carbon_gkg": 8.0, "organic_carbon_pct": 0.8,
                         "sand_pct": 30.0, "silt_pct": 30.0, "clay_pct": 40.0,
                         "cec_cmolkg": 20.0, "nitrogen_gkg": 0.8},
                "source": "SoilGrids"}

    async def fake_crops(db, district, state):
        return {"status": "available",
                "data": {"common": [{"commodity": "Cotton", "arrival_share": 0.6,
                                     "observations": 10}]},
                "source": "agmarknet", "data_year": "2025-2026"}

    import services.agri_context as ctx_mod
    import services.agri_rain as rain_mod
    import services.agri_soil as soil_mod
    import services.agri_crops as crops_mod
    from services import map_service
    monkeypatch.setattr(map_service, "reverse_place", fake_reverse)

    async def fake_weather(db, lat, lng):
        return {"status": "unavailable", "data": None}

    monkeypatch.setattr(map_service, "location_weather", fake_weather)
    monkeypatch.setattr(rain_mod, "get_rainfall", fake_rain)
    monkeypatch.setattr(soil_mod, "get_soil", fake_soil)
    monkeypatch.setattr(crops_mod, "get_crop_context", fake_crops)
    res = await ctx_mod.agricultural_context(map_db, 17.05, 79.27)
    est = (res["suitability"].get("data") or {}).get("estimates", [])
    assert est and est[0]["crop"] == "Cotton"
    # 150 mm partial-season must NOT drive the band: rainfall unknown path.
    assert any("rainfall unknown" in lim.lower() or "seasonal rainfall unknown" in lim.lower()
               for lim in est[0]["limitations"])
    assert res["snapshot"]["season_rain_mm"] is None
