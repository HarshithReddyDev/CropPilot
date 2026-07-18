from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class FarmCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    total_area_hectares: float = 0.0
    soil_type: str | None = None
    irrigation_type: str | None = None


class FarmUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    total_area_hectares: float | None = None
    soil_type: str | None = None
    irrigation_type: str | None = None


class FarmResponse(BaseModel):
    id: UUID
    farmer_id: UUID
    name: str
    description: str | None
    address: str | None
    city: str | None
    state: str | None
    country: str
    total_area_hectares: float
    soil_type: str | None
    irrigation_type: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
