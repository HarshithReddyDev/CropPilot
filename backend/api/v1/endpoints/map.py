"""Geographic map API: search, reverse geocode, nearby/viewport markets,
location weather. All responses are real data or explicit nulls — no fake
coordinates, prices, or weather. Auth uses the existing dependency."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_user, get_db
from models.user import User
from services import map_service

router = APIRouter(prefix="/map", tags=["Map"])


class MapSearchResult(BaseModel):
    type: str
    name: str
    district: str | None = None
    state: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    source: str


class MapReverseResult(BaseModel):
    latitude: float
    longitude: float
    display_name: str | None = None
    locality: str | None = None
    district: str | None = None
    state: str | None = None
    country: str | None = None
    postcode: str | None = None
    source: str | None = None


class MapMarketPrice(BaseModel):
    commodity: str | None = None
    variety: str | None = None
    grade: str | None = None
    modal_price: float | None = None
    price_per_unit: str | None = None
    arrival_date: str | None = None
    arrivals: float | None = None
    source: str | None = None


class MapMarket(BaseModel):
    name: str
    district: str | None = None
    state: str | None = None
    latitude: float
    longitude: float
    coordinate_source: str = "unknown"
    distance_km: float | None = None
    latest: MapMarketPrice | None = None


class MapMarketsResponse(BaseModel):
    markets: list[MapMarket] = Field(default_factory=list)
    unmapped_count: int = 0
    radius_km: float | None = None
    district: str | None = None
    state: str | None = None


class MapWeather(BaseModel):
    latitude: float
    longitude: float
    h3_index: str
    temperature_c: float | None = None
    feels_like_c: float | None = None
    humidity_pct: float | None = None
    rain_mm: float | None = None
    wind_speed: float | None = None
    wind_deg: float | None = None
    condition: str | None = None
    recorded_at: str | None = None
    fetched_now: bool = False
    source: str = "open-meteo"


@router.get("/search", response_model=list[MapSearchResult])
async def search(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    q: str = Query(..., min_length=2, max_length=100),
):
    return await map_service.search_places(db, q.strip())


@router.get("/reverse", response_model=MapReverseResult)
async def reverse(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    lat: float = Query(...),
    lng: float = Query(...),
):
    _ = db
    return await map_service.reverse_place(lat, lng)


@router.get("/markets", response_model=MapMarketsResponse)
async def markets(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    lat: float | None = Query(default=None),
    lng: float | None = Query(default=None),
    radius_km: float = Query(default=25.0),
    state: str | None = Query(default=None, max_length=100),
    district: str | None = Query(default=None, max_length=100),
    commodity: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=10, ge=1, le=50),
):
    if lat is not None and lng is not None:
        return await map_service.nearby_markets(
            db, lat, lng, radius_km=radius_km, district=district,
            state=state, commodity=commodity, limit=limit)
    return await map_service.nearby_markets(
        db, None, None, radius_km=radius_km, district=district,
        state=state, commodity=commodity, limit=limit)


@router.get("/viewport-markets", response_model=MapMarketsResponse)
async def viewport_markets(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    min_lat: float = Query(...),
    min_lng: float = Query(...),
    max_lat: float = Query(...),
    max_lng: float = Query(...),
    commodity: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=200, ge=1, le=200),
):
    return await map_service.viewport_markets(
        db, min_lat, min_lng, max_lat, max_lng, commodity=commodity, limit=limit)


@router.get("/weather", response_model=MapWeather)
async def weather(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    lat: float = Query(...),
    lng: float = Query(...),
):
    return await map_service.location_weather(db, lat, lng)


@router.get("/agricultural-context")
async def agricultural_context(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    lat: float = Query(...),
    lng: float = Query(...),
    district: str | None = Query(default=None, max_length=100),
    state: str | None = Query(default=None, max_length=100),
):
    """Aggregated agri-intelligence: soil, rainfall, crops, suitability,
    water, disease context, weather. Sections degrade independently;
    see docs/map-data-sources.md for provenance."""
    from services import agri_context as agri_context_mod

    return await agri_context_mod.agricultural_context(
        db, lat, lng, district=district, state=state)


@router.get("/data-sources")
async def data_sources(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    _ = db
    from services import map_data_sources as sources_mod

    return {"sources": sources_mod.source_registry()}
