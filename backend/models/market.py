import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import Date, DateTime, Float, JSON, String, UniqueConstraint, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base

# JSONB on PostgreSQL, plain JSON on SQLite (test) dialects.
JSON_VARIANT = JSONB().with_variant(JSON(), "sqlite")


class MarketPrice(Base):
    __tablename__ = "market_prices"
    __table_args__ = (
        UniqueConstraint(
            "state",
            "district",
            "market",
            "commodity",
            "variety",
            "grade",
            "arrival_date",
            name="uq_market_prices_observation",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    commodity: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    variety: Mapped[str] = mapped_column(String(255), nullable=True)
    grade: Mapped[str] = mapped_column(String(100), nullable=True)
    market: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    district: Mapped[str] = mapped_column(String(100), nullable=True)
    state: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    min_price: Mapped[float] = mapped_column(Float, nullable=False)
    max_price: Mapped[float] = mapped_column(Float, nullable=False)
    modal_price: Mapped[float] = mapped_column(Float, nullable=False)
    price_per_unit: Mapped[str] = mapped_column(String(50), default="INR/quintal")
    arrival_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    arrivals: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    arrival_unit: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    source: Mapped[str] = mapped_column(String(50), default="AGMARKNET")
    source_resource_id: Mapped[str] = mapped_column(
        String(64), nullable=True, default=None
    )
    raw_record: Mapped[dict[str, Any]] = mapped_column(
        JSON_VARIANT, nullable=False, default=dict, server_default="{}"
    )
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MarketIngestion(Base):
    __tablename__ = "market_ingestions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    resource_id: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="agmarknet")
    state_filter: Mapped[str] = mapped_column(String(100), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    fetched_count: Mapped[int] = mapped_column(nullable=False, default=0)
    stored_count: Mapped[int] = mapped_column(nullable=False, default=0)
    skipped_count: Mapped[int] = mapped_column(nullable=False, default=0)
    min_observation_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    max_observation_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")
    error: Mapped[str | None] = mapped_column(String(2000), nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
