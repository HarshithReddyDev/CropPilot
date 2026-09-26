from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MarketPriceQuery(BaseModel):
    commodity: str | None = None
    state: str | None = None
    market: str | None = None
    district: str | None = None
    variety: str | None = None
    grade: str | None = None
    days_back: int = Field(default=7, ge=1, le=365)


class MarketPriceResponse(BaseModel):
    id: UUID
    commodity: str
    variety: str | None
    grade: str | None = None
    market: str
    district: str | None
    state: str
    min_price: float
    max_price: float
    modal_price: float
    price_per_unit: str
    arrival_date: date
    arrivals: float | None = None
    arrival_unit: str | None = None
    source: str
    source_resource_id: str | None = None
    fetched_at: datetime | None = None
    ingested_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SourceProvenance(BaseModel):
    name: str = "AGMARKNET"
    resource_id: str
    retrieved_at: datetime


class FreshnessInfo(BaseModel):
    latest_observation_date: date | None = None
    oldest_observation_date: date | None = None
    age_days: int | None = None
    is_stale: bool = False
    observation_count: int = 0


class LatestPricesResponse(BaseModel):
    items: list[MarketPriceResponse]
    provenance: SourceProvenance
    freshness: FreshnessInfo


class HistoryPoint(BaseModel):
    arrival_date: date
    min_price: float
    max_price: float
    modal_price: float
    market: str
    variety: str | None = None
    grade: str | None = None
    price_per_unit: str
    arrivals: float | None = None
    arrival_unit: str | None = None


class HistoryStats(BaseModel):
    point_count: int
    first_modal_price: float | None = None
    last_modal_price: float | None = None
    change: float | None = None
    change_percent: float | None = None
    min_modal_price: float | None = None
    max_modal_price: float | None = None


class HistoryResponse(BaseModel):
    points: list[HistoryPoint]
    stats: HistoryStats
    provenance: SourceProvenance
    freshness: FreshnessInfo


class ComparisonRow(BaseModel):
    market: str
    district: str | None = None
    state: str
    commodity: str
    variety: str | None = None
    grade: str | None = None
    min_price: float
    max_price: float
    modal_price: float
    price_per_unit: str
    arrival_date: date
    arrivals: float | None = None
    arrival_unit: str | None = None
    source: str


class ComparisonResponse(BaseModel):
    rows: list[ComparisonRow]
    group: dict[str, str]
    provenance: SourceProvenance
    freshness: FreshnessInfo


class MetaListResponse(BaseModel):
    values: list[str]
    provenance: SourceProvenance


class MarketOverview(BaseModel):
    states_reporting: int
    markets_reporting: int
    commodities_reported: int
    oldest_observation_date: date | None = None
    latest_observation_date: date | None = None
    provenance: SourceProvenance
