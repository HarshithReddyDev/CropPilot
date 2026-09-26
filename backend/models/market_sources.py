"""Source-aware market data layer.

Each source keeps its own semantics: mandi/spot prices, auction trades,
consumer prices, statistical series, trade statistics, and exchange
observations are different observations and live in different tables.
`market_prices` remains the mandi/spot table (AGMARKNET).
"""

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, JSON, String, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base

JSON_VARIANT = JSONB().with_variant(JSON(), "sqlite")


class MarketDataSource(Base):
    """Registry of legitimate market data sources. No scraping targets."""

    __tablename__ = "market_data_sources"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    organization: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    category: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    base_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    access_type: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    attribution_text: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MarketMaster(Base):
    """Canonical market; never collapsed across sources by display name."""

    __tablename__ = "market_master"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(100), nullable=False, default="", index=True)
    district: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SourceMarketMapping(Base):
    """Source identity for a canonical market (IDs win over names)."""

    __tablename__ = "source_market_mappings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    market_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    source_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source_market_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source_market_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CommodityMaster(Base):
    """Canonical commodity; mappings are verified, never invented."""

    __tablename__ = "commodity_master"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SourceCommodityMapping(Base):
    __tablename__ = "source_commodity_mappings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    commodity_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    source_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source_commodity_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    source_commodity_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="unmapped")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ConsumerPrice(Base):
    """Retail/wholesale consumer price observation (e.g. DCA PMD)."""

    __tablename__ = "consumer_prices"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    source_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source_record_id: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    centre: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    commodity: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    price_type: Mapped[str] = mapped_column(String(32), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="INR")
    observation_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(
        JSON_VARIANT, nullable=False, default=dict, server_default="{}"
    )
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class TradeObservation(Base):
    """Auction/trade observation (e.g. eNAM): never a mandi modal price."""

    __tablename__ = "trade_observations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    source_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source_record_id: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    market: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    commodity: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    variety: Mapped[str] = mapped_column(String(255), nullable=True)
    grade: Mapped[str] = mapped_column(String(100), nullable=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    trade_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    trade_type: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    raw_payload: Mapped[dict[str, Any]] = mapped_column(
        JSON_VARIANT, nullable=False, default=dict, server_default="{}"
    )
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AgriPriceSeries(Base):
    """Statistical price series (e.g. DES wholesale/retail/farm-harvest)."""

    __tablename__ = "agri_price_series"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    source_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source_record_id: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    series: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    commodity: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    geography: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    price: Mapped[float] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    observation_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(
        JSON_VARIANT, nullable=False, default=dict, server_default="{}"
    )
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class TradeStat(Base):
    """Import/export observation (e.g. TradeStat/DGCIS). Never a price."""

    __tablename__ = "trade_stats"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    source_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source_record_id: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    commodity: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    hs_code: Mapped[str] = mapped_column(String(16), nullable=False, default="", index=True)
    country: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    region: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    trade_type: Mapped[str] = mapped_column(String(16), nullable=False)
    month: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=True)
    quantity_unit: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    value: Mapped[float] = mapped_column(Float, nullable=True)
    value_unit: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    raw_payload: Mapped[dict[str, Any]] = mapped_column(
        JSON_VARIANT, nullable=False, default=dict, server_default="{}"
    )
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ExchangeObservation(Base):
    """Exchange instrument observation (MCX/NCDEX public data only)."""

    __tablename__ = "exchange_observations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    source_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source_record_id: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    instrument: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    commodity: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    contract: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    expiry: Mapped[date] = mapped_column(Date, nullable=True)
    open: Mapped[float] = mapped_column(Float, nullable=True)
    high: Mapped[float] = mapped_column(Float, nullable=True)
    low: Mapped[float] = mapped_column(Float, nullable=True)
    close: Mapped[float] = mapped_column(Float, nullable=True)
    ltp: Mapped[float] = mapped_column(Float, nullable=True)
    volume: Mapped[float] = mapped_column(Float, nullable=True)
    open_interest: Mapped[float] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    observation_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(
        JSON_VARIANT, nullable=False, default=dict, server_default="{}"
    )
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
