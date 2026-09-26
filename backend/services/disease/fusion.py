"""Evidence fusion across specialists.

Never averages raw scores across models with different label semantics.
Strategy: rank within each model, accumulate agreement on canonical
disease_ids, penalize cross-model comparison, require corroboration
for high bands.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from services.disease import taxonomy as taxonomy_mod
from services.disease.base import DiseasePrediction
from services.disease.calibration import calibrate


@dataclass
class FusedFinding:
    disease_id: str
    display_name: str
    raw_score: float | None
    score_type: str
    confidence_band: str
    evidence_level: str
    model_ids: list[str] = field(default_factory=list)
    agreement_count: int = 1
    field_validation: str = "Not verified"
    notes: str | None = None
    # Region of the strongest supporting prediction. Only kind="detector"
    # (real detector output) may be rendered as a bounding box.
    region_kind: str = "full"
    region_box: tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0)


@dataclass
class FusionResult:
    findings: list[FusedFinding]
    latency_ms: float


def fuse(
    predictions: list[DiseasePrediction],
    evidence_level_of: dict[str, str] | None = None,
    top_k: int = 3,
) -> FusionResult:
    t0 = time.perf_counter()
    ev_of = evidence_level_of or {}
    # Group by canonical disease_id: within-model rank order preserved.
    groups: dict[str, dict] = {}
    for pred in predictions:
        ordered = sorted(pred.predictions, key=lambda p: p.rank)
        for p in ordered[:top_k]:
            g = groups.setdefault(p.disease_id, {"scores": [], "models": [], "regions": []})
            g["scores"].append(p.raw_score)
            g["models"].append(pred.model_id)
            g["regions"].append((p.region_kind, p.region_box))
    fused: list[FusedFinding] = []
    for did, g in groups.items():
        best = max(g["scores"]) if g["scores"] else None
        models = sorted(set(g["models"]))
        # Region follows the strongest supporting prediction. A detector
        # box is preferred only when a real detector produced it.
        best_idx = g["scores"].index(best) if best in g["scores"] else 0
        det_idx = next((i for i, (k, _) in enumerate(g["regions"]) if k == "detector"), None)
        rk, rb = g["regions"][det_idx if det_idx is not None else best_idx]
        _, score_type, band = calibrate(best)
        # Penalize single-model high claims: agreement required for "high".
        if band == "unverified" and len(models) < 2:
            band = "medium"
            note = "Single-model support; corroboration required for a high band."
        elif len(models) >= 2:
            note = f"{len(models)} models/regions agree."
        else:
            note = None
        evs = [ev_of.get(m, "unknown") for m in models]
        ev = sorted(set(evs), reverse=True)[0] if evs else "unknown"
        fused.append(
            FusedFinding(
                disease_id=did,
                display_name=taxonomy_mod.display_name(did),
                raw_score=best,
                score_type=score_type,  # type: ignore[arg-type]
                confidence_band=band,  # type: ignore[arg-type]
                evidence_level=ev,
                model_ids=models,
                agreement_count=len(models),
                notes=note,
                region_kind=rk,
                region_box=tuple(rb),  # type: ignore[arg-type]
            )
        )
    # Order: agreement first, then score.
    fused.sort(key=lambda f: (f.agreement_count, f.raw_score or 0.0), reverse=True)
    return FusionResult(findings=fused, latency_ms=(time.perf_counter() - t0) * 1000.0)
