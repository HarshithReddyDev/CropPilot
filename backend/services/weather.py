from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from repositories.weather import weather_repository, weather_forecast_repository
from schemas.weather import WeatherRecordResponse, WeatherForecastResponse


class WeatherService:
    async def get_current_weather(
        self, db: AsyncSession, h3_index: str
    ) -> WeatherRecordResponse:
        record = await weather_repository.get_latest_by_h3(db, h3_index)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No weather data for H3 index {h3_index}",
            )
        return WeatherRecordResponse.model_validate(record)

    async def get_forecast(
        self, db: AsyncSession, h3_index: str
    ) -> WeatherForecastResponse:
        forecast = await weather_forecast_repository.get_latest_by_h3(db, h3_index)
        if not forecast:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No forecast for H3 index {h3_index}",
            )
        return WeatherForecastResponse.model_validate(forecast)

    async def fetch_and_store_weather(
        self, db: AsyncSession, lat: float, lon: float, h3_index: str
    ) -> WeatherRecordResponse:
        import httpx

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,weather_code,wind_speed_10m,wind_direction_10m",
            "timezone": "auto"
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        current = data.get("current", {})
        record = await weather_repository.create(
            db,
            h3_index=h3_index,
            temperature=current.get("temperature_2m"),
            feels_like=current.get("apparent_temperature"),
            humidity=current.get("relative_humidity_2m"),
            pressure=None,
            wind_speed=current.get("wind_speed_10m"),
            wind_deg=current.get("wind_direction_10m"),
            cloud_cover=None,
            visibility=None,
            weather_main=str(current.get("weather_code", "Unknown")),
            weather_description=f"WMO Code {current.get('weather_code')}",
            rain_1h=current.get("rain", 0),
            snow_1h=0,
            raw_response=data,
            recorded_at=datetime.utcnow().replace(tzinfo=timezone.utc),
        )
        return WeatherRecordResponse.model_validate(record)
