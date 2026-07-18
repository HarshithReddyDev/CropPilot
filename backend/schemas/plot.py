from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PlotCreate(BaseModel):
    farm_id: UUID
    name: str = Field(min_length=1, max_length=255)
    crop_type: str | None = None
    crop_variety: str | None = None
    sowing_date: datetime | None = None
    expected_harvest_date: datetime | None = None
    area_hectares: float = 0.0
    geometry: dict | None = None
    centroid: dict | None = None
    h3_index: str = Field(min_length=1, max_length=50)
    soil_ph: float | None = None
    soil_moisture: float | None = None
    irrigation_type: str | None = None


class PlotUpdate(BaseModel):
    name: str | None = None
    crop_type: str | None = None
    crop_variety: str | None = None
    sowing_date: datetime | None = None
    expected_harvest_date: datetime | None = None
    area_hectares: float | None = None
    geometry: dict | None = None
    centroid: dict | None = None
    soil_ph: float | None = None
    soil_moisture: float | None = None
    irrigation_type: str | None = None
    status: str | None = None


class PlotResponse(BaseModel):
    id: UUID
    farm_id: UUID
    farmer_id: UUID
    name: str
    crop_type: str | None
    crop_variety: str | None
    sowing_date: datetime | None
    expected_harvest_date: datetime | None
    area_hectares: float
    h3_index: str
    h3_resolution: int
    soil_ph: float | None
    soil_moisture: float | None
    irrigation_type: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
