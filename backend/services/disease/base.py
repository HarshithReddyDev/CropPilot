"""Model adapter interfaces. Adapters differ internally; they share this
prediction shape and lifecycle. No eval/exec/subprocess anywhere."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class RegionPrediction:
    disease_id: str
    display_name: str
    raw_score: float
    rank: int
    region_kind: str = "full"
    region_box: tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0)


@dataclass
class DiseasePrediction:
    model_id: str
    predictions: list[RegionPrediction] = field(default_factory=list)
    latency_ms: float = 0.0


class DiseaseModel(Protocol):
    model_id: str
    version: str
    crop: str | None
    diseases: list[str]
    license: str
    evidence_level: str
    production_allowed: bool

    def load(self) -> None: ...
    def is_loaded(self) -> bool: ...
    def predict(self, image, region_kind: str = "full",
                region_box: tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0)) -> DiseasePrediction: ...
    def unload(self) -> None: ...
