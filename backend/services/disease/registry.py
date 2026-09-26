"""Runtime model registry: load, validate, license-gate, query.

Backed by backend/data/disease_model_registry.json (machine-readable).
The markdown forensic report remains the research authority.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

ALLOWED_TASKS = {"classification", "detection", "embedding"}
ALLOWED_STATUSES = {"production", "research_only", "blocked", "similarity_aid"}

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
REGISTRY_PATH = DATA_DIR / "disease_model_registry.json"


@dataclass
class ModelRecord:
    model_id: str
    source: str
    artifact_type: str
    task: str
    architecture: str
    crop: str | None
    diseases: object  # str tag or list[str]
    labels_verified: bool
    weights_verified: bool
    license: str | None
    license_status: str  # permissive | unknown | blocked
    evidence_level: str
    field_validated: bool
    india_validated: bool
    telangana_validated: bool
    production_allowed: bool
    research_only: bool
    download_required: bool
    deployment_format: str | None
    input_size: object = None
    expected_channels: int = 3
    supports_batch: bool = True
    supports_detection: bool = False
    supports_classification: bool = False
    estimated_memory_mb: int | None = None
    reported_metrics: object = None
    metric_context: str | None = None
    source_date: str | None = None
    status: str = "production"
    status_reason: str | None = None
    raw: dict = field(default_factory=dict)
    # Label-verified crop coverage for multicrop classifiers (e.g. read
    # from class_names.json). None = unrestricted. When set, the model is
    # only eligible for these crops (or an unknown crop, as an open attempt).
    covered_crops: object = None

    @property
    def eligible_production(self) -> bool:
        return (
            self.production_allowed
            and not self.research_only
            and self.status == "production"
            and (self.license_status or "") == "permissive"
        )

    @property
    def eligible_research(self) -> bool:
        return self.status in {"production", "research_only"} and self.status != "blocked"


def _load_doc() -> dict:
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def all_models() -> list[ModelRecord]:
    doc = _load_doc()
    out: list[ModelRecord] = []
    for m in doc.get("models", []):
        known = {f for f in ModelRecord.__dataclass_fields__ if f != "raw"}
        kwargs = {k: v for k, v in m.items() if k in known}
        out.append(ModelRecord(raw=dict(m), **kwargs))  # type: ignore[arg-type]
    return out


def production_models() -> list[ModelRecord]:
    return [m for m in all_models() if m.eligible_production]


def research_models() -> list[ModelRecord]:
    return [m for m in all_models() if m.eligible_research]


def get_model(model_id: str) -> ModelRecord | None:
    for m in all_models():
        if m.model_id == model_id:
            return m
    return None


def validate_registry() -> tuple[list[str], list[str]]:
    """Return (errors, warnings). Errors fail production; warnings allow research notes."""
    errors: list[str] = []
    warnings: list[str] = []
    try:
        doc = _load_doc()
    except Exception as e:
        return [f"registry unreadable: {e}"], []
    models = doc.get("models", [])
    seen: set[str] = set()
    for i, m in enumerate(models):
        tag = m.get("model_id", f"<index {i}>")
        if not m.get("model_id") or "/" not in str(m.get("model_id")):
            errors.append(f"{tag}: malformed model_id (expected 'org/name')")
        if tag in seen:
            errors.append(f"{tag}: duplicate model_id")
        seen.add(tag)
        if m.get("task") not in ALLOWED_TASKS:
            errors.append(f"{tag}: incompatible task {m.get('task')!r}")
        if m.get("status") not in ALLOWED_STATUSES:
            errors.append(f"{tag}: unknown status {m.get('status')!r}")
        if not m.get("artifact_files"):
            errors.append(f"{tag}: no artifact files listed")
        if m.get("production_allowed"):
            if (m.get("license_status") or "") != "permissive":
                errors.append(
                    f"{tag}: production_allowed but license_status="
                    f"{m.get('license_status')!r} (must be 'permissive')"
                )
            if m.get("status") != "production":
                errors.append(f"{tag}: production_allowed but status={m.get('status')!r}")
        if m.get("status") == "blocked" and m.get("production_allowed"):
            errors.append(f"{tag}: blocked model must not be production_allowed")
        if not m.get("labels_verified") and m.get("task") == "classification":
            warnings.append(f"{tag}: labels not runtime-verified (content not opened)")
        if m.get("status") in {"research_only"}:
            warnings.append(f"{tag}: research-only (license/metrics unresolved)")
    return errors, warnings


@lru_cache(maxsize=1)
def registry_version() -> str:
    try:
        return str(_load_doc().get("registry_version", "unknown"))
    except Exception:
        return "unknown"
