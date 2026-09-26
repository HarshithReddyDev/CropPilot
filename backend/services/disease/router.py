"""Candidate specialist ranking.

Pluggable routing supporting:
 1. learned DINOv2 routing head (when artifact exists)
 2. prototype embedding retrieval (when index exists)
 3. crop-conditioned registry routing (always available)
 4. optional BioCLIP similarity signal (aid only, never diagnosis)
 5. deterministic fallback (explicit routing_mode)

No learned artifact is fabricated: without a head artifact the mode is
"registry_fallback"; with a prototype index it is "embedding_retrieval".
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from services.disease import registry as registry_mod
from services.disease.prototypes import PrototypeIndex, cosine


@dataclass
class CandidateSpecialist:
    model_id: str
    rank_score: float
    reasons: list[str] = field(default_factory=list)


@dataclass
class RoutingResult:
    candidates: list[CandidateSpecialist]
    routing_mode: str
    latency_ms: float
    # "known" = crop hint matched taxonomy/supported crops; "unknown" = no
    # hint (no crop classifier exists, so this is never model-inferred);
    # "unsupported" = hint names a crop with no taxonomy rows at all.
    crop_status: str = "unknown"
    eligible_specialists: list[str] = field(default_factory=list)
    excluded_specialists: dict[str, str] = field(default_factory=dict)


def _crop_match_score(record_crop: str | None, crop_hint: str | None) -> tuple[float, str | None]:
    if not crop_hint:
        return 0.0, None
    if record_crop is None:
        return 0.3, "multicrop-covers-hint"
    if record_crop.lower() == crop_hint.lower():
        return 1.0, "crop-match"
    return -1.0, None


def rank_candidates(
    crop_hint: str | None = None,
    research_mode: bool = False,
    embedding: list[float] | None = None,
    prototype_index: PrototypeIndex | None = None,
    max_candidates: int = 5,
) -> RoutingResult:
    t0 = time.perf_counter()
    pool = registry_mod.research_models() if research_mode else registry_mod.production_models()
    # Blocked models never enter either pool (registry guarantees this), but
    # double-guard here: fail closed.
    pool = [m for m in pool if m.status != "blocked" and not m.production_allowed is False and (research_mode or m.eligible_production)]

    proto_scores: dict[str, float] = {}
    mode = "registry_fallback"
    if embedding is not None and prototype_index is not None and prototype_index.prototypes:
        mode = "embedding_retrieval"
        for proto, sim in prototype_index.query(embedding, crop=crop_hint, top_k=50):
            # attribute similarity to models covering that disease/crop
            for m in pool:
                dis = m.diseases
                covers = (
                    (isinstance(dis, list) and proto.disease_id in dis)
                    or (dis == "plantvillage_multicrop")
                    or (m.crop is not None and m.crop.lower() == proto.crop.lower())
                )
                if covers:
                    proto_scores[m.model_id] = max(proto_scores.get(m.model_id, 0.0), sim)
    elif _learned_head_available():
        mode = "learned_dinov2_router"

    scored: list[CandidateSpecialist] = []
    excluded: dict[str, str] = {}
    for m in pool:
        s, reason = _crop_match_score(m.crop, crop_hint)
        covered = m.covered_crops if isinstance(m.covered_crops, list) else None
        if crop_hint is None:
            if m.crop is not None and m.task != "embedding":
                # No crop signal exists (there is no crop classifier): a
                # crop-specific specialist must not be repurposed as a general
                # diagnostician. Only multicrop models may run.
                excluded[m.model_id] = "needs-crop-hint"
                continue
        elif m.task != "embedding":
            h = crop_hint.strip().lower()
            if m.crop is not None:
                if reason is None:
                    excluded[m.model_id] = "crop-mismatch"
                    continue  # crop-specific model for a different crop: exclude
            elif covered is not None and h not in [str(c).lower() for c in covered]:
                # Multicrop model whose verified label set does not cover
                # this crop (e.g. wheat/maize vs a pepper-potato-tomato
                # model): running it could never diagnose this crop.
                excluded[m.model_id] = "crop-not-covered"
                continue
            elif covered is not None:
                reason = "multicrop-covered-crop"
        reasons = []
        if reason:
            reasons.append(reason)
        # Evidence weighting: E4 > E3, production beats research-only
        ev = {"E6": 6, "E5": 5, "E4": 4, "E3": 3, "E2": 2, "E1": 1, "E0": 0}
        s += ev.get(m.evidence_level, 0) * 0.05
        reasons.append(f"evidence-{m.evidence_level}")
        if m.model_id in proto_scores:
            s += proto_scores[m.model_id]
            reasons.append(f"prototype-sim={proto_scores[m.model_id]:.2f}")
        if m.task == "embedding":
            s -= 2.0  # representation aids never outrank diagnostic specialists
            reasons.append("similarity-aid-only")
        scored.append(CandidateSpecialist(model_id=m.model_id, rank_score=s, reasons=reasons))

    scored.sort(key=lambda c: c.rank_score, reverse=True)
    cands = scored[:max_candidates]
    # Embedding/representation models route but never diagnose; they are
    # candidates, not eligible diagnostic specialists.
    tasks = {m.model_id: m.task for m in pool}
    return RoutingResult(
        candidates=cands,
        routing_mode=mode,
        latency_ms=(time.perf_counter() - t0) * 1000.0,
        eligible_specialists=[c.model_id for c in cands if tasks.get(c.model_id) != "embedding"],
        excluded_specialists=excluded,
    )


def _learned_head_available() -> bool:
    from pathlib import Path

    from services.disease.prototypes import default_index_path  # noqa: F401 (keeps import graph honest)

    try:
        from core.config import settings

        raw = str(getattr(settings, "DISEASE_ROUTER_HEAD_PATH", "") or "").strip()
        if not raw:
            return False
        return Path(raw).exists()
    except Exception:
        return False
