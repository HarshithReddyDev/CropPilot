from fastapi import APIRouter

from api.v1.endpoints import (
    ai,
    assistant,
    auth,
    disease_analyze,
    diseases,
    farms,
    health,
    map,
    market_data,
    markets,
    notifications,
    plots,
    schemes,
    telemetry,
    users,
    weather,
)

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(health.router)
v1_router.include_router(auth.router)
v1_router.include_router(users.router)
v1_router.include_router(farms.router)
v1_router.include_router(plots.router)
v1_router.include_router(telemetry.router)
v1_router.include_router(diseases.router)
v1_router.include_router(disease_analyze.router)
v1_router.include_router(weather.router)
v1_router.include_router(map.router)
v1_router.include_router(markets.router)
v1_router.include_router(market_data.router)
v1_router.include_router(schemes.router)
v1_router.include_router(notifications.router)
v1_router.include_router(ai.router)
v1_router.include_router(assistant.router)
