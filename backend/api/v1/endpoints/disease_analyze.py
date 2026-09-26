"""Disease diagnosis API: analyze (multipart) + capabilities/models/health.

Auth: uses the existing get_current_user dependency. Upload validation is
fail-closed (MIME, size, decode). Never exposes secrets or paths.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel

from core.dependencies import get_current_user
from models.user import User
from services.disease import errors
from services.disease.errors import DiseaseError

router = APIRouter(prefix="/disease", tags=["Disease"])


class CapabilitiesResponse(BaseModel):
    enabled: bool
    production_models: list[str]
    research_models: list[str]
    crops_with_production_specialist: list[str]
    # Every crop in the disease taxonomy (selector source). Taxonomy
    # membership is NOT model coverage; compare against
    # crops_with_production_specialist for the coverage truth.
    taxonomy_crops: list[str] = []
    vlm_configured: bool
    research_mode: bool
    routing_modes: list[str]


def _cfg() -> dict:
    from core.config import settings

    return {
        "enabled": bool(getattr(settings, "DISEASE_ENABLED", True)),
        "research": bool(getattr(settings, "DISEASE_ENABLE_RESEARCH_MODELS", False)),
    }


@router.post("/analyze")
async def analyze(
    current_user: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(...),
    crop_hint: str | None = Form(default=None),
    language: str = Form(default="en"),
):
    from services.disease.pipeline import analyze_image

    cfg = _cfg()
    if not cfg["enabled"]:
        raise DiseaseError(errors.SYSTEM_ERROR, "Disease diagnosis is disabled on this deployment.")
    data = await file.read()
    try:
        return await analyze_image(
            data,
            content_type=file.content_type or "image/jpeg",
            crop_hint=crop_hint,
            language=(language or "en")[:8],
        )
    except DiseaseError as e:
        from fastapi import HTTPException

        status = 400 if e.code in {errors.IMAGE_INVALID, errors.IMAGE_TOO_LARGE,
                                   errors.IMAGE_POOR_QUALITY, errors.UNSUPPORTED_CROP} else 502
        if e.code in {errors.NO_VALID_MODEL, errors.MODEL_LOAD_FAILED}:
            status = 503
        raise HTTPException(status_code=status, detail={"code": e.code, "message": e.message})


@router.get("/capabilities", response_model=CapabilitiesResponse)
async def capabilities(current_user: Annotated[User, Depends(get_current_user)]):
    from services.disease import registry as registry_mod
    from services.disease import vlm_fallback as vlm_mod

    cfg = _cfg()
    prod = registry_mod.production_models() if cfg["enabled"] else []
    res = registry_mod.research_models() if cfg["enabled"] else []
    from services.disease import taxonomy as taxonomy_mod

    taxonomy_crops = set(taxonomy_mod.all_crops())
    covered: set[str] = set()
    for m in prod:
        if m.crop and str(m.crop).lower() in taxonomy_crops:
            covered.add(str(m.crop).lower())
        if isinstance(m.covered_crops, list):
            for c in m.covered_crops:
                if str(c).lower() in taxonomy_crops:
                    covered.add(str(c).lower())
    crops = sorted(covered)
    return CapabilitiesResponse(
        enabled=cfg["enabled"],
        production_models=[m.model_id for m in prod],
        research_models=[m.model_id for m in res if m.research_only or m.status == "research_only"],
        crops_with_production_specialist=crops,
        taxonomy_crops=taxonomy_mod.all_crops(),
        vlm_configured=vlm_mod.is_configured(),
        research_mode=cfg["research"],
        routing_modes=["registry_fallback", "embedding_retrieval", "learned_dinov2_router"],
    )


@router.get("/models")
async def list_models(current_user: Annotated[User, Depends(get_current_user)]):
    from services.disease import registry as registry_mod

    cfg = _cfg()
    out = []
    for m in registry_mod.all_models():
        if not cfg["research"] and (m.research_only or m.status == "blocked"):
            # Research entries are hidden unless research mode; blocked shows as blocked.
            if m.status == "blocked":
                out.append({"model_id": m.model_id, "status": "blocked",
                            "production_allowed": False, "license_status": m.license_status,
                            "evidence_level": m.evidence_level})
            continue
        out.append({
            "model_id": m.model_id, "task": m.task, "crop": m.crop,
            "status": m.status, "production_allowed": m.production_allowed,
            "license": m.license, "license_status": m.license_status,
            "evidence_level": m.evidence_level, "field_validated": m.field_validated,
            "metric_context": m.metric_context,
        })
    return {"registry_version": registry_mod.registry_version(), "models": out}


@router.get("/health")
async def health(current_user: Annotated[User, Depends(get_current_user)]):
    import os

    from services.disease import registry as registry_mod

    cfg = _cfg()
    errs, warns = registry_mod.validate_registry()
    cache_dir = ""
    writable = False
    try:
        from core.config import settings

        cache_dir = str(getattr(settings, "DISEASE_MODEL_CACHE_DIR", "") or "")
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)
            writable = os.access(cache_dir, os.W_OK)
    except Exception:
        writable = False
    ok = cfg["enabled"] and not errs
    return {"ok": ok, "enabled": cfg["enabled"], "registry_errors": errs,
            "registry_warnings": warns, "cache_writable": writable}
