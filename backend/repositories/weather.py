from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.weather import WeatherRecord, WeatherForecast
from repositories.base import BaseRepository


class WeatherRepository(BaseRepository):
    def __init__(self):
        super().__init__(WeatherRecord)

    async def get_latest_by_h3(
        self, db: AsyncSession, h3_index: str
    ) -> WeatherRecord | None:
        stmt = (
            select(WeatherRecord)
            .where(WeatherRecord.h3_index == h3_index)
            .order_by(WeatherRecord.recorded_at.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


class WeatherForecastRepository(BaseRepository):
    def __init__(self):
        super().__init__(WeatherForecast)

    async def get_latest_by_h3(
        self, db: AsyncSession, h3_index: str
    ) -> WeatherForecast | None:
        stmt = (
            select(WeatherForecast)
            .where(WeatherForecast.h3_index == h3_index)
            .order_by(WeatherForecast.created_at.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


weather_repository = WeatherRepository()
weather_forecast_repository = WeatherForecastRepository()
