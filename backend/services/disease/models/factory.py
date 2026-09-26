"""Adapter factory: registry is the allow-list. Unknown IDs refused."""

from __future__ import annotations

from services.disease import errors
from services.disease.errors import DiseaseError
from services.disease.registry import get_model


def build(model_id: str, cache_dir: str | None = None, research_mode: bool = False):
    rec = get_model(model_id)
    if rec is None:
        raise DiseaseError(errors.NO_VALID_MODEL, f"Unknown model id (not in registry): {model_id}")
    if rec.status == "blocked":
        raise DiseaseError(errors.NO_VALID_MODEL, f"Model is blocked (license): {model_id}")
    if rec.status == "similarity_aid":
        raise DiseaseError(errors.NO_VALID_MODEL, f"Model is a similarity aid, not a diagnostic: {model_id}")
    if rec.research_only and not research_mode:
        raise DiseaseError(errors.NO_VALID_MODEL, f"Model is research-only; enable research mode: {model_id}")
    if rec.production_allowed is False and not research_mode and rec.status != "production":
        raise DiseaseError(errors.NO_VALID_MODEL, f"Model not eligible for production: {model_id}")

    if model_id == "imaflower/plantvillage-mobilenetv3":
        from services.disease.models.plantvillage_mobilenetv3 import PlantVillageMobileNetV3

        return PlantVillageMobileNetV3(cache_dir=cache_dir)
    if model_id == "surprisedPikachu007/tomato-disease-detection_V2":
        from services.disease.models.tomato_vit import TomatoViT

        return TomatoViT(cache_dir=cache_dir)
    if model_id == "musheijaa/rice-blast-disease-detection-yolo11":
        from services.disease.models.rice_blast_yolo import RiceBlastYOLO

        return RiceBlastYOLO(cache_dir=cache_dir, enabled=research_mode)
    raise DiseaseError(errors.NO_VALID_MODEL, f"No adapter implemented for registered model: {model_id}")
