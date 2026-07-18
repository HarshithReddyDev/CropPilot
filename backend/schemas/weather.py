from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class WeatherRecordResponse(BaseModel):
    id: UUID
    plot_id: UUID | None
    h3_index: str
    temperature: float | None
    feels_like: float | None
    humidity: int | None
    pressure: int | None
    wind_speed: float | None
    weather_main: str | None
    weather_description: str | None
    recorded_at: datetime

    model_config = {"from_attributes": True}


class WeatherForecastResponse(BaseModel):
    id: UUID
    h3_index: str
    forecast_data: dict
    forecasted_at: datetime

    model_config = {"from_attributes": True}
