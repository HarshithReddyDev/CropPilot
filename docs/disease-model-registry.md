# CropPilot Master Disease/Model Forensic Registry
Research date: 2026-09-26. Method: HF Hub API + dataset API inspected live;
prior reports used as discovery leads only. `UNVERIFIED` means not
confirmed from a primary source in this pass — never read as available.

Conventions: evidence E0–E6 and statuses per the research brief.
`foss_compatible` requires an OSI-approved/permissive license on CODE,
WEIGHTS, and DATASET separately. Downloadable ≠ FOSS.

## A. Verified model registry (weights inspected via Hub API)

| # | model_id | cat | arch / task | weights (verified siblings) | size | labels | license | training data | metrics | evidence | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M1 | musheijaa/rice-blast-disease-detection-yolo11 | G exact-specialist (rice blast) | YOLO11 / detection | model.onnx + rice_blast_best.pt, 16 MB, ungated, 2026-04 | 16 MB | UNVERIFIED (no labels file) | NONE DECLARED | UNVERIFIED | none reported | E3 | REQUIRES_CALIBRATION (no metrics, no license) |
| M2 | imaflower/plantvillage-mobilenetv3 | C multi-crop | MobileNetV3 / image-cls | model.onnx + .data + model_scripted.pt + pytorch_model.bin + class_names.json + training_config.json, 19 MB, MIT, 2026-07 | 19 MB | class_names.json present (content not opened) | MIT (code+weights per card) | emmarex/plantdisease (HF) | UNVERIFIED (card claims accuracy, no value shown) | E4 | READY_TO_TEST |
| M3 | innocent11105/plantvillage-mobilenetv3 | C (MIRROR of M2 pattern, same tags/dataset, 2026-09) | MobileNetV3 | UNVERIFIED (siblings not opened) | unknown | UNVERIFIED | MIT (tag) | emmarex/plantdisease (tag) | none | E0–E2 | UNKNOWN (probable mirror; deduplicate to M2) |
| M4 | surprisedPikachu007/tomato-disease-detection_V2 | B crop (tomato) | ViT-base/86M / image-cls | model.safetensors + pytorch_model.bin + config, Apache-2.0, 2023-03 | ~350 MB | UNVERIFIED (config not opened) | Apache-2.0 | imagefolder (unspecified) | 98.87% TRAIN accuracy, self-reported, `verified:false`, NO test metric | E4 | REQUIRES_FIELD_VALIDATION (train-only metric = overfit signal) |
| M5 | aquib1011/maize-leaf-disease-convnext | B crop (maize) | ConvNeXt / image-cls, 72 downloads | UNVERIFIED (siblings not opened) | unknown | UNVERIFIED | UNVERIFIED (no license tag) | UNVERIFIED | none reported | E2 | REQUIRES_CALIBRATION |
| M6 | eligapris/maize-diseases-detection | B crop (maize) | tf-keras / image-cls | UNVERIFIED (siblings not opened) | unknown | UNVERIFIED | MIT (tag) | smaranjitghose/corn-or-maize-leaf-disease-dataset (HF tag) | none reported | E2 | REQUIRES_FIELD_VALIDATION |
| M7 | muAtarist/maize_disease_model | B crop (maize) | ConvNeXt/safetensors | UNVERIFIED | unknown | UNVERIFIED | UNVERIFIED | UNVERIFIED | none | E2 | UNKNOWN |
| M8 | aleisya01/cotton-leaf-diseases-and-pest-detection | B crop (cotton) | .h5 (Keras), 155 MB | model_cotton_leaf.h5 ONLY file, no license/metrics | 155 MB | UNVERIFIED | NONE DECLARED | UNVERIFIED | none | E3 | LICENSE_BLOCKED (no license; do not ship) |
| M9 | dwililiya/sugarcane-plant-diseases-classification | B crop (sugarcane) | EfficientNet (tag only) | UNVERIFIED (siblings not opened) | unknown | UNVERIFIED | UNVERIFIED | UNVERIFIED | none | E2 | UNKNOWN |
| M10 | imageomics/bioclip-2 | F embedding/retrieval | CLIP-style biology FM, TreeOfLife-200M | safetensors (standard), MIT, 97k downloads | ~350 MB–1 GB class | taxonomy text, NOT disease labels | MIT | TreeOfLife-200M/GBIF/BIOSCAN (species, not disease) | zero-shot species benchmarks only | E4 (as species model) | REQUIRES_FIELD_VALIDATION for disease-router use (species≠disease; unproven) |
| M11 | imageomics/bioclip / bioclip-2.5-vith14 | F (variants of M10) | same family | standard, MIT | varies | same caveat | MIT | same | same | E4 | same as M10 |
| M12 | facebook/dinov2-base | F router backbone | ViT-B/86M self-supervised, Apache-2.0, 2.8M downloads | model.safetensors + pytorch_model.bin, config verified | 330 MB (86M F32) | none (embeddings) | Apache-2.0 | LVD-142M (general images, NOT agriculture) | linear-probe benchmarks (general) | E4 | READY_TO_INTEGRATE as embedding router (needs disease reference index) |
| M13 | ashikaasriarun/MobileNet-V2-PlantVillage | C | Keras MobileNetV2, MIT, 2026-06 | UNVERIFIED (siblings not opened) | unknown | UNVERIFIED | MIT (tag) | PlantVillage (implied) | none | E2 | UNKNOWN |

DISAGREEMENTS RESOLVED: (1) Prior reports cited
`linkanjarad/mobilenet_v2_1.0_224` — does NOT appear in Hub search;
UNVERIFIED, do not depend on it. Use M2 instead. (2) innocent11105 vs
imaflower identical tags/dataset 2 months apart → mirror, count once.
(3) "BioCLIP for disease diagnosis" — BioCLIP is species-level;
disease zero-shot use is UNVERIFIED; do not treat M10/M11 as disease
classifiers. (4) Tomato 98.87% is TRAIN-split, self-reported,
unverified — must not be quoted as field accuracy.

## B. Verified datasets

| dataset | access (verified) | size/classes | field? | license | notes |
|---|---|---|---|---|---|
| PlantDoc (original, ACM 2020, Singh et al.) | mirrors: agyaatcoder/PlantDoc (CC-BY-4.0, 1–10K, object-detection, 352 dl) + LamTNguyen variants (incl `plantdoc-synthetic`) | ~2.6K images, 27 classes, 13 crops | YES field | CC-BY-4.0 (mirror tag; original paper ©ACM) | ONLY verified field dataset; LamTNguyen `*-synthetic` variant = leakage risk, exclude from eval |
| PlantVillage (Hughes/Salathé) | Kaggle (well-known, not API-checked) + HF mirrors dpdl-benchmark/plant_village, emmarex/plantdisease | ~54K, 38 classes, 14 crops | NO (lab) | UNVERIFIED (commonly cited CC; confirm before commercial use) | dominant training source of M2/M4/M13; field gap applies to all of them |
| smaranjitghose/corn-or-maize-leaf-disease-dataset | HF tag on M6 (repo not opened) | UNVERIFIED | UNVERIFIED | UNVERIFIED | verify before use |
| IP102 (pest) | NOT verified this pass | ~75K (literature) | mixed | UNVERIFIED | pest branch, lower priority |
| FieldPlant | NO HF match; location UNVERIFIED | UNVERIFIED | field (literature) | UNVERIFIED | do not cite a URL |
| ICAR/PJTSAU/ICRISAT field sets | none found public | — | — | — | GAP: no verified Indian field dataset |

## C. Disease registry (India-first; Telangana flagged)

Format: crop | disease | pathogen | type | India | Telangana.
Types: F fungal, O oomycete, B bacterial, V viral, PH phytoplasma,
N nematode, P pest, A abiotic. Sources: IRRI/CABI/APS/ICAR knowledge
base (org-level attribution; no fabricated URLs).

RICE: blast (Magnaporthe oryzae, F, high/high); brown spot (Bipolaris
oryzae, F, high/high); bacterial leaf blight (Xanthomonas oryzae pv.
oryzae, B, high/high); sheath blight (Rhizoctonia solani, F,
high/high); tungro (RTSV+RTSV complex, V, med/med); false smut
(Ustilaginoidea virens, F, med/med); sheath rot (Sarocladium oryzae,
F, low/low); stem rot (Sclerotium oryzae, F, low/low).
WHEAT: stripe rust (Puccinia striiformis, F, high/low); leaf rust (P.
triticina, F, high/low); stem rust (P. graminis, F, med/low); powdery
mildew (Blumeria graminis, F, med/low); spot blotch (Bipolaris
sorokiniana, F, high/low); loose smut (Ustilago tritici, F, low/low);
Karnal bunt (Tilletia indica, F, med/low); head scab (Fusarium
graminearum, F, low/low).
MAIZE: turcicum leaf blight (Exserohilum turcicum, F, high/high); gray
leaf spot (Cercospora zeae-maydis, F, med/med); common rust (Puccinia
sorghi, F, med/med); banded leaf & sheath blight (R. solani f.sp.
sasakii, F, med/med); maize streak virus (V, low/low).
SORGHUM: anthracnose (Colletotrichum sublineola, F, high/high); grain
mold (Fusarium/Alternaria complex, F, high/high); downy mildew
(Peronosclerospora sorghi, F, med/med); ergot (Claviceps sorghi, F,
low/low).
PEARL MILLET: downy mildew (Sclerospora graminicola, F, high/med);
blast (Pyricularia grisea, F, med/low); smut (Moesziomyces
penicillariae, F, low/low).
FINGER MILLET: blast (Pyricularia oryzae, F, med/low); brown spot (low).
PIGEON PEA: fusarium wilt (Fusarium udum, F, high/high); sterility
mosaic virus (V, high/high); phytophthora blight (O, med/med).
CHICKPEA: ascochyta blight (Ascochyta rabiei, F, high/low); fusarium
wilt (F. oxysporum f.sp. ciceris, F, high/low); gray mold (Botrytis, F,
med/low).
BLACK/GREEN GRAM: yellow mosaic virus (V, high/high); powdery mildew
(Erysiphe polygoni, F, med/med); cercospora leaf spot (F, med/med).
LENTIL: rust (Uromyces viciae-fabae, F, med/low); ascochyta (F, low).
GROUNDNUT: early leaf spot (Cercospora arachidicola, F, high/high);
late leaf spot (Nothopassalora personata, F, high/high); rust
(Puccinia arachidis, F, high/high); stem rot (Sclerotium rolfsii, F,
med/med); bud necrosis virus (V, med/med).
MUSTARD: white rust (Albugo candida, O, high/low); alternaria blight
(Alternaria brassicae, F, high/low); sclerotinia stem rot (F, med/low).
SOYBEAN: yellow mosaic virus (V, high/high); rust (Phakopsora
pachyrhizi, F, high/med); charcoal rot (Macrophomina phaseolina, F,
med/med).
SUNFLOWER: alternaria leaf spot (F, med/low); downy mildew
(Plasmopara halstedii, O, low/low); head rot (Rhizopus/Botrytis, F,
low/low).
SESAME: phyllody (PH, med/low); alternaria (F, low/low).
CASTOR: fusarium wilt (F, med/low); gray mold (F, low/low).
COTTON: bacterial blight (X. citri pv. malvacearum, B, high/high);
grey mildew (Ramularia areola, F, high/high); alternaria spot (F,
med/med); fusarium wilt (F, med/med); bollworm/whitefly/jassids/
thrips (P, high/high — pests, not diseases).
SUGARCANE: red rot (Colletotrichum falcatum, F, high/low); smut
(Sporisorium scitamineum, F, high/low); wilt (Fusarium sacchari, F,
med/low); grassy shoot (PH, med/low); pokkah boeng (Fusarium, F,
low/low).
TOMATO: early blight (Alternaria solani, F, high/high); late blight
(Phytophthora infestans, O, high/med); leaf curl virus (ToLCV, V,
high/high); bacterial wilt (Ralstonia solanacearum, B, high/high);
septoria spot (F, med/low); powdery mildew (Leveillula, F, med/med).
POTATO: late blight (P. infestans, O, high/low); early blight (F,
high/low); bacterial wilt (B, med/low); black scurf (R. solani, F,
low/low); common scab (Streptomyces scabies, B, low/low).
ONION: purple blotch (Alternaria porri, F, high/high); stemphylium
blight (F, med/med); basal rot (Fusarium, F, low/low).
CHILLI: leaf curl virus (ChiLCV, V, high/high); anthracnose/die-back
(Colletotrichum capsici, F, high/high); bacterial wilt (B, med/med);
phytophthora fruit rot (O, med/med).
BRINJAL: bacterial wilt (B, med/med); little leaf (PH, med/low);
phomopsis blight (F, low/low); shoot & fruit borer (P, high/high).
OKRA: yellow vein mosaic virus (V, high/med); cercospora (F, low/low).
CABBAGE/CAULIFLOWER: black rot (X. campestris, B, med/low);
alternaria (F, med/low); clubroot (Plasmodiophora brassicae, O,
low/low).
CUCURBITS: downy mildew (Pseudoperonospora cubensis, O, med/med);
powdery mildew (Podosphaera xanthii, F, med/med); CMV mosaic (V,
med/med).
MANGO: anthracnose (Colletotrichum gloeosporioides, F, high/med);
powdery mildew (Oidium mangiferae, F, med/med); bacterial black spot
(B, low/low).
BANANA: sigatoka (Mycosphaerella spp., F, high/low); Panama TR4
(Fusarium oxysporum f.sp. cubense, F, high/low); bunchy top virus (V,
med/low).
CITRUS: canker (Xanthomonas citri, B, high/med); greening/HLB
(Candidatus Liberibacter, B, high/med); gummosis (Phytophthora, O,
med/med).
GRAPE: downy mildew (Plasmopara viticola, F, med/low); powdery mildew
(Erysiphe necator, F, med/low).
GUAVA: wilt (Fusarium oxysporum f.sp. psidii, F, med/med).
POMEGRANATE: bacterial blight (X. axonopodis pv. punicae, B,
high/low); anthracnose (F, low/low).
PAPAYA: ringspot virus (PRSV, V, med/low).
COCONUT: bud rot (Phytophthora palmivora, O, med/low); root wilt (PH,
med/low).
TURMERIC: leaf spot (Colletotrichum capsici, F, high/high); rhizome
rot (Pythium/Phytophthora, O, high/high).
TEA: blister blight (Exobasidium vexans, F, med/low). COFFEE: rust
(Hemileia vastatrix, F, med/low). TOBACCO: mosaic TMV (V, low/low).
(≈100 rows; Telangana-high ≈ 30.)

## D. Disease → model mapping (priority subset; full matrix follows same pattern)

| disease | exact specialist | crop model | multi-crop | embedding/VLM | usable today | action |
|---|---|---|---|---|---|---|
| rice blast | M1 (E3, no license/metrics) | none verified | M2 (E4) | M12 router | M2 | CALIBRATE M1; FINE-TUNE M2 head on field data |
| rice BLB/brown spot/sheath blight | none found | none verified | M2 | M12 | M2 | FINE-TUNE (no rice multi-disease weights found) |
| tomato EB/LB/leaf curl/bact. wilt | none verified | M4 (E4, Apache-2.0) | M2 | M12 | M4+M2 | REUSE M4 + field-validate; leaf-curl-VLM fallback UNVERIFIED |
| maize TLB/GLS/rust | none verified | M5/M6/M7 (E2) | M2 | M12 | M2 | VERIFY M5–M7 files, then REUSE best + field-validate |
| cotton bact. blight/grey mildew | none verified | M8 (E3, NO LICENSE) | M2 | M12 | M2 | DO NOT SHIP M8; FINE-TUNE from M2/M12 features |
| sugarcane red rot/smut | none verified | M9 (E2, UNVERIFIED) | M2 | M12 | M2 | VERIFY M9, else FINE-TUNE |
| wheat rusts/mildew/spot blotch | none found (HF: zero) | none verified | M2 | M12 | M2 | TRAIN/FINE-TUNE (backbone M12 or M2) |
| chilli leaf curl/anthracnose | none found (HF: zero) | none verified | M2 | M12 | M2 | TRAIN/FINE-TUNE |
| groundnut leaf spots/rust | none verified | none verified | M2 | M12 | M2 | FINE-TUNE |
| soybean YMV/rust | none verified | none verified | M2 | M12 | M2 | FINE-TUNE |
| pigeon pea wilt/SMD, chickpea blight/wilt, urad/mung YMV | none verified | none verified | M2 | M12 | M2 | FINE-TUNE (pulse gap is wide) |
| potato/onion/brinjal/okra/cabbage/cucurbits | none verified (this pass) | none verified | M2/M4(tomato-adjacent) | M12 | M2 | FINE-TUNE |
| mango/banana/citrus/grape/guava/pomegranate/papaya/coconut | none verified | none verified | M2 | M12 | M2 | FINE-TUNE (perennial gap) |
| turmeric leaf spot/rhizome rot | none verified | none verified | M2 | M12 | M2 | FINE-TUNE (Telangana priority) |
| millets/sorghum/oilseeds minor | none verified | none verified | M2 | M12 | M2 | FINE-TUNE or defer by importance |

## E. Verified counts

India registry: ~15 crops groups, ~100 disease rows. Exact
specialists VERIFIED: 1 (M1 rice-blast YOLO). Crop models VERIFIED
(weights): M4 tomato, M8 cotton(h5), M2-class multi-crop (M2, M13
unverified-files), M5–M7/M9 file-unverified. Multi-crop verified: M2.
General verified: M12 (+M10/M11 species-only). Field-validated: 0.
India-validated: 0. Telangana-validated: 0. No-public-model diseases:
majority (~85+ rows). These are LOWER BOUNDS from one pass, not
exhaustive totals — report as verified-minimums.

## F. Latency/cost (ESTIMATES by architecture class, NOT measurements)

MobileNetV3-38cls ONNX CPU b1: tens of ms. YOLO11n/s ONNX CPU b1:
tens of ms. ViT-B CPU b1: hundreds of ms. ConvNeXt-T CPU b1:
~50–150 ms. DINOv2-B embedding CPU b1: ~100 ms. Cloud T4 warm:
single-digit ms class for small CNNs. End-to-end farmer upload on
4G dominates (seconds) — on-device/edge small models win latency;
cloud wins breadth. Free inference: HF serverless free tier reported
(verify at use); otherwise CPU VPS. VERIFY all numbers before
budgeting; none measured this pass.

## G. Architecture evidence (no winner declared; evidence-mapped)

Available evidence supports: DINOv2-class embedding router (M12
verified integrable, Apache-2.0) → top-k crop/disease specialists
(M2/M4 verified runnable; M1/M5–M9 need verification) in parallel →
per-model calibration (R1: no calibrated confidences found anywhere)
→ VLM fallback for uncertain (UNVERIFIED agri-VLM this pass; general
Qwen-VL-class would need evaluation) → RAG advisory (CropPilot has).
Single-giant-classifier: no verified India-breadth weights exist.
One-model-per-disease: only 1 exact specialist verified; storage/
maintenance scales badly. Shared-encoder+heads: no verified
implementation; would need training (but is the cheapest TRAIN path:
freeze M12/M2 encoder, train heads on PlantDoc+field data).
Recommendation-if-forced-by-evidence: E (router+specialists) now,
D (shared encoder) as the fine-tune target, G (VLM) for
uncertain-only. Minimum simultaneous models for fast path: 1 embedder
+ 2–5 small specialists (all <100 MB class except ViT options).

## H. License registry (verified tags/cards only)

MIT weights: M2, M6(tag), M10/M11, M13(tag). Apache-2.0: M4, M12.
CC-BY-4.0 dataset: PlantDoc mirrors. NO LICENSE: M1, M5, M7, M8, M9
→ foss_compatible=false until clarified; M8 (.h5) must not ship.
UNVERIFIED: PlantVillage dataset license (confirm CC terms), IP102,
Kaggle mirrors. Rule kept: downloadable ≠ FOSS.

## I. Field/domain-gap findings

- 98.87% tomato ViT is TRAIN-split: textbook lab-overfit signal.
- PlantVillage-trained models (M2/M4/M13) inherit lab backgrounds.
- Only verified field corpus: PlantDoc (2.6K, 27 classes) — too small
  alone; pair with farmer-image active-learning loop (no verified
  existing agri active-learning system this pass — standard AL
  literature applies, mark as method not product).
- Multi-disease coexistence: only detectors (M1-class) address it;
  classifiers are single-label — CropPilot MUST support multi-finding
  output (detection/segmentation stage), evidence: classifier label
  spaces are mutually exclusive by construction.
- Nutrient/pest vs disease confusion: no verified model separates
  them; taxonomy PART 1 separation must be enforced in data design.

## J. What to build first (blueprint summary, no code)

1. Registry service (models/diseases/datasets/licenses/evidence as
   versioned records — this file is v0). 2. Embedding index over
   PlantDoc + PlantVillage + incoming farmer images (M12). 3. Router:
   top-k specialist selection by embedding similarity + crop prior.
4. Specialist runner: M2 (multi-crop), M4 (tomato), M1 (rice blast
   after calibration), M5–M9 after file verification; parallel,
   <100 MB residents. 5. Calibration + uncertainty gate (unseen/
   multi-condition → VLM/human). 6. Field-validation loop with
   extension-verified labels → fine-tune heads (LoRA/adapter on frozen
   M12/M2 encoder). 7. Dataset+model versioning, per-decision traces.
8. Cloud: CPU-first (small models), GPU only for VLM fallback;
   ONNX for all deployed specialists.

## K. Source list (primary, accessed 2026-09-26)

HF Hub API: musheijaa/rice-blast-disease-detection-yolo11;
imaflower/plantvillage-mobilenetv3; innocent11105/plantvillage-mobilenetv3;
surprisedPikachu007/tomato-disease-detection_V2; aquib1011/maize-leaf-disease-convnext;
eligapris/maize-diseases-detection; muAtarist/maize_disease_model;
aleisya01/cotton-leaf-diseases-and-pest-detection;
dwililiya/sugarcane-plant-diseases-classification;
ashikaasriarun/MobileNet-V2-PlantVillage;
imageomics/bioclip, bioclip-2, bioclip-2.5-vith14;
facebook/dinov2-base; datasets agyaatcoder/PlantDoc (+LamTNguyen
variants). Taxonomy: IRRI rice knowledge bank, CABI Crop Protection
Compendium, APS compendia, ICAR institute publications (org-level;
no per-row URLs fabricated). Commercial: Plantix, Kindwise
(benchmarks only, no weights claimed).
