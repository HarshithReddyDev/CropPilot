from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MarketPriceQuery(BaseModel):
    commodity: str | None = None
    state: str | None = None
    market: str | None = None
    days_back: int = Field(default=7, ge=1, le=365)


class MarketPriceResponse(BaseModel):
    id: UUID
    commodity: str
    variety: str | None
    market: str
    district: str | None
    state: str
    min_price: float
    max_price: float
    modal_price: float
    price_per_unit: str
    arrival_date: date
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}
