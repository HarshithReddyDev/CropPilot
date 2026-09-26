"""Typed result contract for disease diagnosis (API + agent friendly)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

DiagnosisStatus = Literal[
    "diagnosed", "probable", "uncertain",
    "insufficient_image", "unsupported_crop", "error",
]
QualityStatus = Literal["good", "acceptable", "poor", "rejected"]
ConfidenceBand = Literal["high", "medium", "low", "unverified", "unknown"]


class ImageQuality(BaseModel):
    status: QualityStatus
    score: float = Field(ge=0.0, le=1.0)
    reasons: list[str] = Field(default_factory=list)
    width: int = 0
    height: int = 0
    format: str = "unknown"


class CropInfo(BaseModel):
    name: str | None = None
    confidence_band: ConfidenceBand = "unknown"
    # source: "user" = farmer-selected hint (routing context only, never
    # model evidence); "model" reserved for a future real crop classifier;
    # "unknown" = no reliable crop signal. status mirrors the same truth.
    source: Literal["user", "model", "unknown"] = "unknown"
    status: Literal["known", "unknown", "unsupported"] = "unknown"


class Region(BaseModel):
    kind: Literal["full", "center_crop", "crop", "detector"] = "full"
    x1: float = 0.0
    y1: float = 0.0
    x2: float = 1.0
    y2: float = 1.0
    score: float | None = None
    source: str = "deterministic"


class SpecialistRun(BaseModel):
    model_id: str
    latency_ms: float
    ok: bool
    error: str | None = None
    error_code: str | None = None


class Finding(BaseModel):
    disease_id: str
    display_name: str
    region: Region = Field(default_factory=Region)
    raw_score: float | None = None
    calibrated_score: float | None = None
    score_type: Literal["raw_model_score", "calibrated"] = "raw_model_score"
    confidence_band: ConfidenceBand = "unverified"
    evidence_level: str = "unknown"
    model_ids: list[str] = Field(default_factory=list)
    agreement_count: int = 1
    field_validation: str = "Not verified"
    notes: str | None = None


class RoutingInfo(BaseModel):
    routing_mode: Literal[
        "registry_fallback", "embedding_retrieval", "learned_dinov2_router"
    ] = "registry_fallback"
    specialists_considered: list[str] = Field(default_factory=list)
    specialists_run: list[str] = Field(default_factory=list)
    crop_hint: str | None = None
    crop_status: Literal["known", "unknown", "unsupported"] = "unknown"
    eligible_specialists: list[str] = Field(default_factory=list)
    # model_id -> human-readable exclusion reason (e.g. "crop-mismatch",
    # "needs-crop-hint", "blocked", "research-gated").
    excluded_specialists: dict[str, str] = Field(default_factory=dict)


class EvidenceItem(BaseModel):
    model_id: str
    license_status: str = "unknown"
    evidence_level: str = "unknown"
    field_validation: str = "Not verified"
    metric_context: str | None = None
    research_only: bool = False


class KnowledgeItem(BaseModel):
    disease_id: str
    title: str
    symptoms: list[str] = Field(default_factory=list)
    similar_conditions: list[str] = Field(default_factory=list)
    management: list[str] = Field(default_factory=list)
    prevention: list[str] = Field(default_factory=list)
    source: str
    language: str = "en"


class PipelineTimings(BaseModel):
    routing_mode: str = "registry_fallback"
    specialists_considered: list[str] = Field(default_factory=list)
    specialists_run: list[str] = Field(default_factory=list)
    specialist_latencies_ms: dict[str, float] = Field(default_factory=dict)
    quality_latency_ms: float = 0.0
    router_latency_ms: float = 0.0
    fusion_latency_ms: float = 0.0
    vlm_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
    vlm_used: bool = False
    rag_used: bool = False


class DiseaseAnalysisResult(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    status: DiagnosisStatus
    crop: CropInfo = Field(default_factory=CropInfo)
    image_quality: ImageQuality
    findings: list[Finding] = Field(default_factory=list)
    alternatives: list[Finding] = Field(default_factory=list)
    routing: RoutingInfo = Field(default_factory=RoutingInfo)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    knowledge: list[KnowledgeItem] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    next_action: str
    pipeline: PipelineTimings = Field(default_factory=PipelineTimings)
    error_code: str | None = None
    # Machine-readable outcome reason (may accompany any status, including
    # healthy no-diagnosis states). Never a raw exception.
    reason_code: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def diagnosis_summary(self) -> str:
        if self.findings:
            top = self.findings[0]
            return (
                f"{self.status}: {top.display_name} "
                f"(confidence band: {top.confidence_band}; "
                f"evidence: {top.evidence_level})"
            )
        return f"{self.status}: no finding ({self.next_action[:120]})"
