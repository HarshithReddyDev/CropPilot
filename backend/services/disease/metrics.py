"""Prometheus metrics for the disease subsystem (no image content logged)."""

from __future__ import annotations

try:
    from prometheus_client import Counter, Histogram

    disease_requests_total = Counter("disease_requests_total", "Disease analyses by status", ["status"])
    disease_errors_total = Counter("disease_errors_total", "Disease errors by code", ["code"])
    disease_quality_rejected_total = Counter("disease_quality_rejected_total", "Images rejected by QA")
    disease_uncertain_total = Counter("disease_uncertain_total", "Uncertain analyses")
    disease_vlm_fallback_total = Counter("disease_vlm_fallback_total", "VLM fallback invocations")
    disease_model_load_total = Counter("disease_model_load_total", "Model loads", ["model_id"])
    disease_model_load_errors_total = Counter("disease_model_load_errors_total", "Model load failures", ["model_id"])
    disease_no_eligible_specialist_total = Counter(
        "disease_no_eligible_specialist_total", "Analyses with no eligible specialist (coverage gap)")
    disease_model_inference_failed_total = Counter(
        "disease_model_inference_failed_total", "Analyses where all specialist runs failed")
    disease_unsupported_crop_total = Counter(
        "disease_unsupported_crop_total", "Analyses for crops without a verified specialist")
    disease_request_latency = Histogram("disease_request_latency_seconds", "End-to-end analysis latency")
    disease_quality_latency = Histogram("disease_quality_latency_seconds", "QA latency")
    disease_router_latency = Histogram("disease_router_latency_seconds", "Router latency")
    disease_specialist_latency = Histogram("disease_specialist_latency_seconds", "Per-specialist latency", ["model_id"])
    disease_fusion_latency = Histogram("disease_fusion_latency_seconds", "Fusion latency")
    disease_vlm_latency = Histogram("disease_vlm_latency_seconds", "VLM latency")
except Exception:  # pragma: no cover - metrics optional in minimal envs
    class _Noop:
        def labels(self, *a, **k):
            return self

        def observe(self, *a, **k):
            pass

        def inc(self, *a, **k):
            pass

    disease_requests_total = disease_errors_total = disease_quality_rejected_total = _Noop()
    disease_uncertain_total = disease_vlm_fallback_total = disease_model_load_total = _Noop()
    disease_model_load_errors_total = disease_no_eligible_specialist_total = _Noop()
    disease_model_inference_failed_total = disease_unsupported_crop_total = _Noop()
    disease_request_latency = disease_quality_latency = disease_router_latency = _Noop()
    disease_specialist_latency = disease_fusion_latency = disease_vlm_latency = _Noop()
