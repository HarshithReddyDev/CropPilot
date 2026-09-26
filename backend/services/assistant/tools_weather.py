"""Weather tools for the assistant. Stored records only, no live fetch.

Forecast/current reads hit the local weather tables keyed by H3 index.
A missing row returns an error dict (the agent then says so) instead of
fabricating a forecast.
"""

from __future__ import annotations

from fastapi import HTTPException

from db.session import async_session_factory
from services.weather import WeatherService

_weather = WeatherService()


def _dump(obj):
    return obj.model_dump(mode="json") if hasattr(obj, "model_dump") else obj


async def _safe(coro) -> dict:
    try:
        return {"ok": True, "data": _dump(await coro)}
    except HTTPException as e:
        return {"ok": False, "error": e.detail}
    except Exception as e:  # storage failure: report, never invent weather
        return {"ok": False, "error": f"weather lookup failed: {e}"}


async def weather_current(h3_index: str) -> dict:
    """Current stored weather for an H3 cell index."""
    async with async_session_factory() as db:
        return await _safe(_weather.get_current_weather(db, h3_index))


async def weather_forecast(h3_index: str) -> dict:
    """Stored forecast for an H3 cell index."""
    async with async_session_factory() as db:
        return await _safe(_weather.get_forecast(db, h3_index))
