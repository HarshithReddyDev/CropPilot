"""Central diagnosis orchestrator: QA -> route -> specialists -> fuse ->
uncertainty -> (optional VLM) -> knowledge. CPU-first, lazy, bounded.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from uuid import uuid4

from services.disease import errors
from services.disease.base import DiseasePrediction
from services.disease.errors import DiseaseError
from services.disease.schemas import (
    CropInfo,
    DiseaseAnalysisResult,
    EvidenceItem,
    Finding,
    ImageQuality,
    KnowledgeItem,
    PipelineTimings,
    Region,
    RoutingInfo,
    SpecialistRun,
)

SUPPORTED_CROPS = {"rice", "wheat", "cotton", "tomato", "potato", "maize", "chilli", "sugarcane"}


def _settings() -> dict:
    try:
        from core.config import settings

        return {
            "cache_dir": str(getattr(settings, "DISEASE_MODEL_CACHE_DIR", "") or "") or None,
            "max_loaded": int(getattr(settings, "DISEASE_MAX_LOADED_MODELS", 3) or 3),
            "max_parallel": int(getattr(settings, "DISEASE_MAX_PARALLEL_SPECIALISTS", 3) or 3),
            "timeout_s": float(getattr(settings, "DISEASE_INFERENCE_TIMEOUT_SECONDS", 20) or 20),
            "max_mb": float(getattr(settings, "DISEASE_MAX_IMAGE_MB", 10) or 10),
            "max_pixels": int(getattr(settings, "DISEASE_MAX_PIXELS", 25_000_000) or 25_000_000),
            "research": bool(getattr(settings, "DISEASE_ENABLE_RESEARCH_MODELS", False)),
            "vlm": bool(getattr(settings, "DISEASE_ENABLE_VLM_FALLBACK", True)),
        }
    except Exception:
        return {"cache_dir": None, "max_loaded": 3, "max_parallel": 3,
                "timeout_s": 20.0, "max_mb": 10, "max_pixels": 25_000_000,
                "research": False, "vlm": True}


@dataclass
class Pipeline:
    cache: object = None
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def _get_cache(self):
        from services.disease.model_cache import ModelCache

        with self._lock:
            if self.cache is None:
                self.cache = ModelCache(max_loaded_models=_settings()["max_loaded"])
            return self.cache


_PIPELINE: Pipeline | None = None
_PIPELINE_LOCK = threading.Lock()


def get_pipeline() -> Pipeline:
    global _PIPELINE
    with _PIPELINE_LOCK:
        if _PIPELINE is None:
            _PIPELINE = Pipeline()
        return _PIPELINE


def _norm_crop(hint: str | None) -> str | None:
    if not hint:
        return None
    h = hint.strip().lower()
    aliases = {"paddy": "rice", "dhan": "rice", "mirchi": "chilli", "makka": "maize"}
    h = aliases.get(h, h)
    return h or None


async def analyze_image(
    data: bytes,
    content_type: str = "image/jpeg",
    crop_hint: str | None = None,
    language: str = "en",
    research_mode: bool | None = None,
) -> DiseaseAnalysisResult:
    from services.disease import fusion as fusion_mod
    from services.disease import knowledge as knowledge_mod
    from services.disease import metrics as metrics_mod
    from services.disease import quality_gate as quality_gate_mod
    from services.disease import registry as registry_mod
    from services.disease import router as router_mod
    from services.disease import uncertainty as uncertainty_mod
    from services.disease import vlm_fallback as vlm_mod
    from services.disease.image_pipeline import decode_image, make_regions
    from services.disease.specialist_runner import run_specialists

    cfg = _settings()
    if research_mode is None:
        research_mode = cfg["research"]
    request_id = str(uuid4())
    t_start = time.perf_counter()
    crop = _norm_crop(crop_hint)

    # --- upload validation (fail closed) ---
    ctype = (content_type or "").split(";")[0].strip().lower()
    if ctype not in {"image/jpeg", "image/png", "image/webp"}:
        raise DiseaseError(errors.IMAGE_INVALID, f"Unsupported media type: {content_type}")
    if len(data) > cfg["max_mb"] * 1024 * 1024:
        raise DiseaseError(errors.IMAGE_TOO_LARGE, f"Image exceeds {cfg['max_mb']:g} MB limit.")

    decoded = decode_image(data, max_pixels=cfg["max_pixels"])
    quality, q_ms = quality_gate_mod.assess_quality(decoded)
    metrics_mod.disease_quality_latency.observe(q_ms / 1000.0)

    import logging as _logging
    _log = _logging.getLogger("croppilot.disease")

    # Crop truth: only a farmer-provided hint counts ("user"). No crop
    # classifier exists, so without a hint the crop is "unknown" — never
    # guessed from filenames, EXIF, or model outputs.
    crop_source = "user" if crop else "unknown"

    def _crop_status() -> str:
        if not crop:
            return "unknown"
        from services.disease import taxonomy as taxonomy_mod

        if taxonomy_mod.diseases_for_crop(crop) or crop in SUPPORTED_CROPS:
            return "known"
        return "unsupported"

    def _base(status: str, action: str, code: str | None = None,
              reason: str | None = None,
              routing_mode: str = "registry_fallback",
              eligible: list | None = None,
              excluded: dict | None = None) -> DiseaseAnalysisResult:
        total = (time.perf_counter() - t_start) * 1000.0
        cstat = _crop_status()
        res = DiseaseAnalysisResult(
            request_id=request_id, status=status,  # type: ignore[arg-type]
            crop=CropInfo(name=crop, source=crop_source, status=cstat),  # type: ignore[arg-type]
            image_quality=quality,
            routing=RoutingInfo(routing_mode=routing_mode,  # type: ignore[arg-type]
                                crop_hint=crop, crop_status=cstat,  # type: ignore[arg-type]
                                eligible_specialists=eligible or [],
                                excluded_specialists=excluded or {}),
            next_action=action, error_code=code, reason_code=reason,
            pipeline=PipelineTimings(routing_mode=routing_mode,
                                     quality_latency_ms=q_ms,
                                     total_latency_ms=total),
        )
        metrics_mod.disease_requests_total.labels(status=status).inc()
        metrics_mod.disease_request_latency.observe(total / 1000.0)
        _log.info("disease request_id=%s status=%s reason=%s crop=%s crop_source=%s",
                  request_id, status, reason, crop, crop_source)
        return res

    if quality.status == "rejected":
        metrics_mod.disease_quality_rejected_total.inc()
        return _base("insufficient_image", quality_gate_mod.RETAKE_HINT,
                     errors.IMAGE_POOR_QUALITY, errors.POOR_IMAGE_QUALITY)

    # --- routing ---
    cstat = _crop_status()
    if cstat == "unsupported":
        # The hint names a crop with no taxonomy rows at all: unsupported
        # before any model runs. A generic multicrop model must not be
        # repurposed as a specialist.
        metrics_mod.disease_unsupported_crop_total.inc()
        return _base("unsupported_crop",
                     f"CropPilot does not yet have a verified specialist for '{crop}'. "
                     "Coverage status: requires_training. You can ask the assistant for general guidance.",
                     errors.UNSUPPORTED_CROP, errors.NO_VERIFIED_MODEL_FOR_CROP)
    routing = router_mod.rank_candidates(crop_hint=crop, research_mode=research_mode)
    routing.crop_status = cstat
    metrics_mod.disease_router_latency.observe(routing.latency_ms / 1000.0)
    considered = [c.model_id for c in routing.candidates]
    if not routing.eligible_specialists:
        # Routing correctly found nothing runnable: a coverage gap, NOT a
        # load failure. Known crops (e.g. wheat/maize/chilli) and unknown
        # crops both land here; no model is started or retried.
        metrics_mod.disease_no_eligible_specialist_total.inc()
        if crop:
            metrics_mod.disease_unsupported_crop_total.inc()
            return _base("unsupported_crop",
                         f"CropPilot does not yet have a verified production specialist for {crop} "
                         "(coverage_status: requires_training). " + quality_gate_mod.RETAKE_HINT,
                         errors.NO_VALID_MODEL, errors.NO_VERIFIED_MODEL_FOR_CROP,
                         routing_mode=routing.routing_mode,
                         eligible=[], excluded=routing.excluded_specialists)
        return _base("uncertain",
                     "CropPilot could not identify the crop from this photo, so no verified "
                     "disease model could be selected. " + quality_gate_mod.RETAKE_HINT
                     + " If you know the crop, select it and analyze again.",
                     errors.NO_VALID_MODEL, errors.NO_ELIGIBLE_SPECIALIST,
                     routing_mode=routing.routing_mode,
                     eligible=[], excluded=routing.excluded_specialists)

    # --- load (bounded LRU) + run ---
    # Reaching here means routing found eligible diagnostic specialists.
    # If every load fails, that is a genuine MODEL_LOAD_FAILED (infra),
    # never a coverage gap.
    from services.disease.models.factory import build

    pipe = get_pipeline()
    cache = pipe._get_cache()
    adapters = []
    load_failures: list[str] = []
    for cand in routing.candidates[:5]:
        mid = cand.model_id
        rec = registry_mod.get_model(mid)
        if rec is not None and rec.task == "embedding":
            continue  # representations route; they never diagnose
        try:
            cached = cache.get(mid)
            if cached is None:
                adapter = build(mid, cache_dir=cfg["cache_dir"], research_mode=research_mode)
                try:
                    cached = cache.get_or_load(mid, lambda a=adapter: (a.load(), a)[1])
                    metrics_mod.disease_model_load_total.labels(model_id=mid).inc()
                except DiseaseError:
                    metrics_mod.disease_model_load_errors_total.labels(model_id=mid).inc()
                    raise
                except Exception as e:
                    metrics_mod.disease_model_load_errors_total.labels(model_id=mid).inc()
                    raise DiseaseError(errors.MODEL_LOAD_FAILED, f"{mid} failed to load: {e}") from e
            adapters.append(cached)
        except DiseaseError as e:
            load_failures.append(f"{mid}: {e.message}")
            continue
    if not adapters:
        _log.warning("disease request_id=%s reason=%s failures=%s",
                     request_id, errors.MODEL_LOAD_FAILED, "; ".join(load_failures))
        return _base("error",
                     "A verified disease model is available, but it could not be loaded right now. "
                     "Please try again in a little while.",
                     errors.MODEL_LOAD_FAILED, errors.MODEL_LOAD_FAILED,
                     routing_mode=routing.routing_mode,
                     eligible=routing.eligible_specialists,
                     excluded=routing.excluded_specialists)

    regions = make_regions(decoded.image, max_crops=1)  # full + center
    preds: list[DiseasePrediction] = []
    latencies: dict[str, float] = {}
    run_records: list[dict] = []
    for reg in regions:
        box = (reg.box[0], reg.box[1], reg.box[2], reg.box[3])
        p, lat, runs = await run_specialists(adapters, reg.pixels, region_kind=reg.kind,
                                             region_box=box, max_parallel=cfg["max_parallel"],
                                             timeout_s=cfg["timeout_s"])
        preds.extend(p)
        for k, v in lat.items():
            latencies[f"{k}@{reg.kind}"] = v
            metrics_mod.disease_specialist_latency.labels(model_id=k).observe(v / 1000.0)
        run_records.extend(runs)
    if not preds:
        timeouts = [r for r in run_records if r.get("error_code") == errors.INFERENCE_TIMEOUT]
        reason = errors.INFERENCE_TIMEOUT if timeouts and len(timeouts) == len(run_records) \
            else errors.MODEL_INFERENCE_FAILED
        metrics_mod.disease_model_inference_failed_total.inc()
        _log.warning("disease request_id=%s reason=%s runs=%s",
                     request_id, reason, run_records)
        return _base("error",
                     "A verified disease model was available, but the analysis could not be "
                     "completed. Please try again with another photo.",
                     reason, reason,
                     routing_mode=routing.routing_mode,
                     eligible=routing.eligible_specialists,
                     excluded=routing.excluded_specialists)

    ev_of = {}
    for m in registry_mod.all_models():
        ev_of[m.model_id] = m.evidence_level
    fused = fusion_mod.fuse(preds, evidence_level_of=ev_of)
    metrics_mod.disease_fusion_latency.observe(fused.latency_ms / 1000.0)

    status, reason, action, review = uncertainty_mod.decide(
        fused, quality.status, crop_supported=True)
    if status == "uncertain":
        metrics_mod.disease_uncertain_total.inc()

    # --- optional VLM (uncertain only) ---
    vlm_used, vlm_ms = False, 0.0
    if review and status in {"uncertain", "probable"} and cfg["vlm"] and vlm_mod.is_configured():
        try:
            t0 = time.perf_counter()
            summary = "; ".join(f"{f.disease_id}={f.raw_score:.2f}" for f in fused.findings[:3])
            await vlm_mod.analyze(decoded.image, [f.disease_id for f in fused.findings[:3]],
                                  summary, "", quality_note=",".join(quality.reasons))
            vlm_ms = (time.perf_counter() - t0) * 1000.0
            vlm_used = True
            metrics_mod.disease_vlm_fallback_total.inc()
            metrics_mod.disease_vlm_latency.observe(vlm_ms / 1000.0)
        except Exception:
            vlm_ms = (time.perf_counter() - t0) * 1000.0

    # --- knowledge (separated from evidence) ---
    dids = [f.disease_id for f in fused.findings[:3]]
    k_entries, rag_used = await knowledge_mod.retrieve(dids, language=language)

    reg_v = registry_mod.registry_version()
    findings = [
        Finding(disease_id=f.disease_id, display_name=f.display_name,
                region=Region(kind=f.region_kind,  # type: ignore[arg-type]
                              x1=f.region_box[0], y1=f.region_box[1],
                              x2=f.region_box[2], y2=f.region_box[3],
                              source="detector" if f.region_kind == "detector" else "deterministic"),
                raw_score=f.raw_score, calibrated_score=None, score_type=f.score_type,  # type: ignore[arg-type]
                confidence_band=f.confidence_band,  # type: ignore[arg-type]
                evidence_level=f.evidence_level, model_ids=f.model_ids,
                agreement_count=f.agreement_count, notes=((f.notes + " " if f.notes else "") + f"registry={reg_v}"))
        for f in fused.findings[:1]
    ]
    alternatives = [
        Finding(disease_id=f.disease_id, display_name=f.display_name, region=Region(),
                raw_score=f.raw_score, score_type=f.score_type,  # type: ignore[arg-type]
                confidence_band=f.confidence_band,  # type: ignore[arg-type]
                evidence_level=f.evidence_level, model_ids=f.model_ids,
                agreement_count=f.agreement_count, notes=f.notes)
        for f in fused.findings[1:4]
    ]
    evidence = [
        EvidenceItem(model_id=r["model_id"],
                     license_status=(registry_mod.get_model(r["model_id"]).license_status
                                     if registry_mod.get_model(r["model_id"]) else "unknown"),
                     evidence_level=ev_of.get(r["model_id"], "unknown"),
                     metric_context=(registry_mod.get_model(r["model_id"]).metric_context
                                     if registry_mod.get_model(r["model_id"]) else None),
                     research_only=bool(registry_mod.get_model(r["model_id"]).research_only)
                     if registry_mod.get_model(r["model_id"]) else False)
        for r in run_records if r.get("ok")
    ]
    knowledge = [
        KnowledgeItem(disease_id=e.get("disease_id", ""), title=e.get("title", ""),
                      symptoms=e.get("symptoms", []), similar_conditions=e.get("similar_conditions", []),
                      management=e.get("management", []), prevention=e.get("prevention", []),
                      source=e.get("source", ""), language=e.get("language", language))
        for e in k_entries
    ]
    if (status in {"diagnosed", "probable"}) and findings and not knowledge:
        action += " CropPilot does not yet have verified guidance for this diagnosis."
    total = (time.perf_counter() - t_start) * 1000.0
    res = DiseaseAnalysisResult(
        request_id=request_id, status=status,  # type: ignore[arg-type]
        crop=CropInfo(name=crop, source=crop_source, status=cstat),  # type: ignore[arg-type]
        image_quality=quality,
        findings=findings, alternatives=alternatives,
        routing=RoutingInfo(routing_mode=routing.routing_mode,  # type: ignore[arg-type]
                            specialists_considered=considered,
                            specialists_run=[r["model_id"] for r in run_records if r.get("ok")],
                            crop_hint=crop, crop_status=cstat,  # type: ignore[arg-type]
                            eligible_specialists=routing.eligible_specialists,
                            excluded_specialists=routing.excluded_specialists),
        evidence=evidence, knowledge=knowledge,
        citations=[k.source for k in knowledge if k.source],
        next_action=action, reason_code=reason,
        pipeline=PipelineTimings(routing_mode=routing.routing_mode,
                                 specialists_considered=considered,
                                 specialists_run=[r["model_id"] for r in run_records if r.get("ok")],
                                 specialist_latencies_ms=latencies,
                                 quality_latency_ms=q_ms, router_latency_ms=routing.latency_ms,
                                 fusion_latency_ms=fused.latency_ms, vlm_latency_ms=vlm_ms,
                                 total_latency_ms=total, vlm_used=vlm_used, rag_used=rag_used),
    )
    metrics_mod.disease_requests_total.labels(status=status).inc()
    metrics_mod.disease_request_latency.observe(total / 1000.0)
    if quality.status == "poor":
        metrics_mod.disease_quality_rejected_total.inc()
    _log.info("disease request_id=%s status=%s reason=%s crop=%s crop_source=%s "
              "routing=%s eligible=%s run=%s",
              request_id, status, reason, crop, crop_source, routing.routing_mode,
              routing.eligible_specialists,
              [r["model_id"] for r in run_records if r.get("ok")])
    return res
