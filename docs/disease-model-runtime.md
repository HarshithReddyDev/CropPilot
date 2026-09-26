# CropPilot Disease Model Runtime

Source authority: `docs/disease-model-registry.md`. Registry version: `1.1.0`
(`backend/data/disease_model_registry.json`).

## Production enabled

| model | license | evidence | labels | status |
|---|---|---|---|---|
| `imaflower/plantvillage-mobilenetv3` | MIT | E4, PlantVillage-derived (lab, not field) | runtime `class_names.json`, 15 classes verified 2026-09-26; covered crops pepper/potato/tomato | production |
| `surprisedPikachu007/tomato-disease-detection_V2` | Apache-2.0 | E4; reported 98.87% is self-reported train-split, never field accuracy | runtime config `id2label`, verified 2026-09-26 | production |
| `facebook/dinov2-base` | Apache-2.0 | shared embedding/router backbone, not a diagnostic | n/a | production (representation only; never in specialist runners) |

Load verified live 2026-09-26 (Windows CPU): M2 ONNX loads, 15 labels,
predicts; tomato ViT loads, predicts; DINOv2 loads (~21.8 s cold).

## Research-only (never production unless `DISEASE_ENABLE_RESEARCH_MODELS=true`, visibly badged)

| model | reason |
|---|---|
| `musheijaa/rice-blast-disease-detection-yolo11` | no declared license, labels unverified, no metrics |

## Blocked / not production

| model | reason |
|---|---|
| `aleisya01/cotton-leaf-diseases-and-pest-detection` | no license declared; registered, never downloaded |
| `imageomics/bioclip-2` | similarity aid only; must not rank or diagnose alone |

## Coverage (honest)

105 taxonomy rows; 6 production-enabled rows (5.7%); 1 research-only;
98 `requires_training`. India-high covered 4/45; Telangana-high 3/25.
Crops with a verified production specialist: potato, tomato (M2 label set
also includes pepper, which has no taxonomy rows yet). All other
taxonomy crops (wheat, maize, chilli, cotton, …) return
`unsupported_crop` + `NO_VERIFIED_MODEL_FOR_CROP` without running any
model — never a repurposed guess.

## Status semantics (backend reason codes)

`status` + `reason_code` on every analysis (HTTP 200; no-model states are
normal product states, not server errors):

| situation | status | reason_code |
|---|---|---|
| routing found no runnable model | `uncertain` | `NO_ELIGIBLE_SPECIALIST` |
| known crop, no verified specialist | `unsupported_crop` | `NO_VERIFIED_MODEL_FOR_CROP` |
| eligible models exist but all loads failed | `error` | `MODEL_LOAD_FAILED` |
| loads ok, all runs failed/timed out | `error` | `MODEL_INFERENCE_FAILED` / `INFERENCE_TIMEOUT` |
| weak/conflicting specialist evidence | `uncertain` | `LOW_CONFIDENCE` / `SPECIALIST_DISAGREEMENT` |
| QA rejected | `insufficient_image` | `POOR_IMAGE_QUALITY` |

`NO_ELIGIBLE_SPECIALIST` is never stored as `MODEL_LOAD_FAILED`. Crop is
`unknown` unless the farmer selects it (`source: user`); nothing infers
crop from filenames, EXIF, or model outputs. Metrics:
`disease_no_eligible_specialist_total`,
`disease_model_inference_failed_total`, `disease_unsupported_crop_total`
(+ existing load/error/latency metrics). Logs carry
`request_id … reason=…`, never image data.

## Downloads & cache

HF Hub only, lazy, once, reused, bounded LRU (`DISEASE_MAX_LOADED_MODELS=3`).
`DISEASE_MODEL_CACHE_DIR` (default `/models/disease`; Docker volume for
persistence). Partial snapshots are detected (labels file required) and
healed by re-download. No weights in Git. Research models never auto-download
in production.

## Env

`DISEASE_ENABLED, DISEASE_MODEL_CACHE_DIR, DISEASE_MAX_LOADED_MODELS=3,
DISEASE_MAX_PARALLEL_SPECIALISTS=3, DISEASE_ENABLE_RESEARCH_MODELS=false,
DISEASE_ENABLE_VLM_FALLBACK=true, DISEASE_MAX_IMAGE_MB=10,
DISEASE_MAX_PIXELS=25000000, DISEASE_INFERENCE_TIMEOUT_SECONDS=20,
DISEASE_ROUTER_MODE=auto, DISEASE_VLM_PROVIDER, DISEASE_VLM_MODEL`
(no keys in frontend; VLM unconfigured → skipped).

## Commands

- `python -m services.disease validate` — production gates (license/artifact/labels).
- `python -m services.disease coverage` — taxonomy vs runnable-model coverage.
- `python -m services.disease.healthcheck [--cache-dir DIR]` — registry, taxonomy, onnx/transformers, synthetic QA+router pass.
- `python -m services.disease.inspect_model --model ID` — artifacts, labels, license, live load check.
- `python -m services.disease.evaluate --model ID --dataset ...` — refuses synthetic mirrors as field evidence.
- `python -m services.disease.benchmark` — cold/warm/latency numbers.
