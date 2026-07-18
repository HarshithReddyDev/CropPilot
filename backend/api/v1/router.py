from fastapi import APIRouter

from api.v1.endpoints import (
    ai,
    auth,
    diseases,
    farms,
    health,
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
v1_router.include_router(weather.router)
v1_router.include_router(markets.router)
v1_router.include_router(schemes.router)
v1_router.include_router(notifications.router)
v1_router.include_router(ai.router)
