import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class WeatherRecord(Base):
    __tablename__ = "weather_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    plot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("plots.id", ondelete="CASCADE"), nullable=True, index=True
    )
    h3_index: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    temperature: Mapped[float] = mapped_column(Float, nullable=True)
    feels_like: Mapped[float] = mapped_column(Float, nullable=True)
    humidity: Mapped[int] = mapped_column(Integer, nullable=True)
    pressure: Mapped[int] = mapped_column(Integer, nullable=True)
    wind_speed: Mapped[float] = mapped_column(Float, nullable=True)
    wind_deg: Mapped[int] = mapped_column(Integer, nullable=True)
    cloud_cover: Mapped[int] = mapped_column(Integer, nullable=True)
    visibility: Mapped[int] = mapped_column(Integer, nullable=True)
    weather_main: Mapped[str] = mapped_column(String(100), nullable=True)
    weather_description: Mapped[str] = mapped_column(String(255), nullable=True)
    rain_1h: Mapped[float] = mapped_column(Float, default=0.0)
    snow_1h: Mapped[float] = mapped_column(Float, default=0.0)
    raw_response: Mapped[dict] = mapped_column(JSONB, default=dict)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class WeatherForecast(Base):
    __tablename__ = "weather_forecasts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    h3_index: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    forecast_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    forecasted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
