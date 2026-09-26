# CropPilot Disease Detection — Architecture

Research authority: `docs/disease-model-registry.md` (forensic findings).
Runtime registry: `backend/data/disease_model_registry.json` (machine-readable,
production gates). Taxonomy: `backend/data/disease_taxonomy.json`.
General guidance: `backend/data/disease_knowledge.json` (IPM only, no doses).

## Pipeline

```
upload (multipart) → validation (MIME/size/decode, fail-closed)
  → image QA (deterministic: blur/dark/bright/uniform/tiny) → rejected stops here
  → unknown-crop gate (taxonomy; multicrop models never repurposed)
  → router (registry_fallback | embedding_retrieval | learned_dinov2_router)
  → bounded LRU load (max DISEASE_MAX_LOADED_MODELS) → 2 regions (full + center)
  → bounded parallel specialists (max DISEASE_MAX_PARALLEL_SPECIALISTS, per-model timeout)
  → fusion (agreement grouping; never blind-averages raw scores)
  → uncertainty decision → conditional VLM (uncertain/probable only, opt-in)
  → knowledge retrieval (separated from evidence) → typed result
```

## Router

Pluggable ranking: crop hint → specialist crop compatibility → registry
compatibility → learned head (when artifact exists) → prototype similarity
(when index exists) → BioCLIP similarity (optional, never ranks alone) →
evidence weighting → production eligibility. No trained head ships today, so
`routing_mode="registry_fallback"` is exposed in diagnostics honestly.

## Score honesty

`score_type="raw_model_score"` until a validated calibration artifact exists.
Bands: high (multi-model agreement only) / medium / low / unverified / unknown.
Single-model support is capped at medium. Softmax values are never presented
as calibrated probabilities.

## Regions

Classifier regions are deterministic crops (`full`, `center_crop`), never
lesion locations. Bounding boxes render only for `region.kind="detector"`
(real detector output, currently research-only rice-blast YOLO).

## Uncertainty

Statuses: `diagnosed | probable | uncertain | insufficient_image |
unsupported_crop | error`. Wheat, chilli, cotton-production and other
uncovered crops return `uncertain`/`unsupported_crop` with
`coverage_status=requires_training` — never a repurposed multicrop guess.
VLM never fabricates: unconfigured → skipped, uncertain stands.

## Knowledge vs evidence

Diagnostic evidence (model ids, evidence levels, agreement) and agronomic
guidance (retrieved IPM text with source citations) are separate response
sections. No verified document → "CropPilot does not yet have verified
guidance for this diagnosis." No pesticide names/doses are invented.

## Security / privacy

Only registry-listed model ids load (no client-supplied URLs, no eval/exec/
subprocess). Images are processed in memory/temp and never persisted or
logged; history stores metadata only ("Image not retained").

## Performance (measured, Windows CPU host, 2026-09-26)

- PlantVillage MobileNetV3 ONNX cold load ~790 ms; warm infer p50 ~4 ms.
- DINOv2-base cold load ~21.8 s (transformers, CPU).
- Full tomato pipeline (2 specialists × 2 regions, warm): ~13.7 s.
- VLM is off the normal path; no unused models load at startup.

## Training path

`backend/ml/disease_training/` holds manifest-validated stubs
(datasets/train_head/calibrate/evaluate/export). No training runs at startup;
no datasets auto-download. Prototype index builds only from explicitly
supplied licensed images (`prototypes build`); nothing fabricated is shipped.

## Field validation

Zero models are field- or India-validated today. `field_validation` always
reads "Not verified" until measured. See `docs/disease-model-runtime.md`.
