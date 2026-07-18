from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class VisionSyncRequest(BaseModel):
    timestamp: datetime
    h3_spatial_index: str = Field(min_length=1, max_length=50)
    detections: list[dict] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    image_url: str | None = None
    raw_payload: dict = Field(default_factory=dict)


class DiseaseDetectionResponse(BaseModel):
    id: UUID
    disease_log_id: UUID
    class_name: str
    confidence: float
    bbox: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DiseaseLogResponse(BaseModel):
    id: UUID
    plot_id: UUID
    farmer_id: UUID
    h3_spatial_index: str
    detected_disease: str | None
    confidence: float
    detections: list
    image_url: str | None
    severity: str
    recommendation: str | None
    is_resolved: bool
    created_at: datetime
    detections_rel: list[DiseaseDetectionResponse] = []

    model_config = {"from_attributes": True}
