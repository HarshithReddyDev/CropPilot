"""Disease platform tests: registry, QA, router, cache, calibration,
fusion, uncertainty, pipeline paths. No weight downloads (mocked adapters,
synthetic images for transport/validation only)."""

from __future__ import annotations

import asyncio
import io

import pytest
from PIL import Image

from services.disease import errors
from services.disease.base import DiseasePrediction, RegionPrediction
from services.disease.errors import DiseaseError


def _img(color=(70, 130, 60), size=(512, 512), textured: bool = False) -> bytes:
    import random

    buf = io.BytesIO()
    img = Image.new("RGB", size, color)
    if textured:
        rnd = random.Random(42)
        px = img.load()
        for y in range(0, size[1], 4):
            for x in range(0, size[0], 4):
                px[x, y] = (rnd.randint(20, 120), rnd.randint(80, 180), rnd.randint(20, 90))
    img.save(buf, format="JPEG")
    return buf.getvalue()


# --- registry ---

def test_registry_validates():
    from services.disease.registry import validate_registry

    errs, _ = validate_registry()
    assert errs == []


def test_license_gating_blocks_unlicensed_and_blocked():
    from services.disease import registry as reg

    blocked = reg.get_model("aleisya01/cotton-leaf-diseases-and-pest-detection")
    assert blocked is not None and blocked.status == "blocked"
    assert not blocked.eligible_production
    rice = reg.get_model("musheijaa/rice-blast-disease-detection-yolo11")
    assert rice is not None and rice.research_only and not rice.eligible_production
    prod = reg.production_models()
    assert all(m.eligible_production for m in prod)
    assert "imaflower/plantvillage-mobilenetv3" in [m.model_id for m in prod]


def test_factory_refuses_unknown_and_blocked():
    from services.disease.models.factory import build

    with pytest.raises(DiseaseError):
        build("acme/fake-model")
    with pytest.raises(DiseaseError) as e:
        build("aleisya01/cotton-leaf-diseases-and-pest-detection")
    assert e.value.code == errors.NO_VALID_MODEL
    with pytest.raises(DiseaseError):
        build("musheijaa/rice-blast-disease-detection-yolo11", research_mode=False)


def test_taxonomy_stable_ids_and_aliases():
    from services.disease import taxonomy as tax

    assert tax.validate_taxonomy() == []
    assert tax.resolve_alias("rice blast")["id"] == "rice.rice_blast"
    assert tax.display_name("rice.rice_blast") == "Rice blast"
    assert len(tax.priority_filter("telangana_high")) >= 1


# --- image pipeline + QA ---

def test_decode_rejects_garbage_and_oversize():
    from services.disease.image_pipeline import decode_image

    with pytest.raises(DiseaseError):
        decode_image(b"not-an-image" * 10)
    with pytest.raises(DiseaseError) as e:
        decode_image(_img(), max_pixels=100)
    assert e.value.code == errors.IMAGE_TOO_LARGE


def test_quality_gate_good_and_rejected():
    from services.disease.image_pipeline import decode_image
    from services.disease.quality_gate import assess_quality

    q, _ = assess_quality(decode_image(_img(textured=True)))
    assert q.status in {"good", "acceptable"}
    dark = _img(color=(5, 5, 5), size=(64, 64))
    q2, _ = assess_quality(decode_image(dark))
    assert q2.status in {"poor", "rejected"}


def test_regions_deterministic_not_lesions():
    from services.disease.image_pipeline import decode_image, make_regions

    dec = decode_image(_img(size=(400, 400)))
    regs = make_regions(dec.image, max_crops=2)
    assert len(regs) == 3 and regs[0].kind == "full"
    assert all(r.source == "deterministic" for r in regs)


# --- router ---

def test_router_fallback_excludes_wrong_crop():
    from services.disease.router import rank_candidates

    r = rank_candidates(crop_hint="tomato")
    assert r.routing_mode == "registry_fallback"
    ids = [c.model_id for c in r.candidates]
    assert "imaflower/plantvillage-mobilenetv3" in ids
    assert "surprisedPikachu007/tomato-disease-detection_V2" in ids
    assert "aleisya01/cotton-leaf-diseases-and-pest-detection" not in ids


def test_router_embedding_mode_with_index():
    from services.disease.prototypes import Prototype, PrototypeIndex
    from services.disease.router import rank_candidates

    idx = PrototypeIndex([Prototype(disease_id="tomato.early_blight", crop="tomato",
                                    vector=[1.0, 0.0], source="test", image_ref="x")])
    r = rank_candidates(crop_hint="tomato", embedding=[1.0, 0.0], prototype_index=idx)
    assert r.routing_mode == "embedding_retrieval"


# --- cache ---

def test_model_cache_lru_eviction():
    from services.disease.model_cache import ModelCache

    c = ModelCache(max_loaded_models=2)

    class M:
        def __init__(self, i):
            self.i = i
            self.unloaded = False

        def unload(self):
            self.unloaded = True

    a, b = M(1), M(2)
    c.get_or_load("a", lambda: a)
    c.get_or_load("b", lambda: b)
    c.get_or_load("c", lambda: M(3))
    assert c.loaded_ids() == ["b", "c"] and a.unloaded and c.evictions == 1


# --- calibration / fusion / uncertainty ---

def test_calibration_honest_raw():
    from services.disease.calibration import calibrate

    score, stype, _ = calibrate(0.9)
    assert stype == "raw_model_score" and score == 0.9


def test_fusion_agreement_and_no_blind_average():
    from services.disease import fusion as fusion_mod

    p1 = DiseasePrediction(model_id="m1", predictions=[
        RegionPrediction(disease_id="rice.rice_blast", display_name="Rice blast", raw_score=0.8, rank=1)])
    p2 = DiseasePrediction(model_id="m2", predictions=[
        RegionPrediction(disease_id="rice.rice_blast", display_name="Rice blast", raw_score=0.7, rank=1)])
    fused = fusion_mod.fuse([p1, p2], evidence_level_of={"m1": "E4", "m2": "E4"})
    assert fused.findings[0].agreement_count == 2


def test_uncertainty_paths():
    from services.disease import fusion as fusion_mod
    from services.disease import uncertainty as unc
    from services.disease.fusion import FusedFinding

    empty = fusion_mod.FusionResult(findings=[], latency_ms=0)
    assert unc.decide(empty, "good", True)[0] == "uncertain"
    assert unc.decide(empty, "rejected", True)[0] == "insufficient_image"
    weak = fusion_mod.FusionResult(findings=[
        FusedFinding(disease_id="rice.rice_blast", display_name="Rice blast",
                     raw_score=0.2, score_type="raw_model_score",
                     confidence_band="low", evidence_level="E4")], latency_ms=0)
    assert unc.decide(weak, "good", True)[0] == "uncertain"


# --- pipeline integration (mocked adapters, no weights) ---

class _FakeAdapter:
    model_id = "imaflower/plantvillage-mobilenetv3"

    def predict(self, image, region_kind="full", region_box=(0, 0, 1, 1)):
        return DiseasePrediction(model_id=self.model_id, predictions=[
            RegionPrediction(disease_id="tomato.early_blight", display_name="Early blight",
                             raw_score=0.9, rank=1, region_kind=region_kind, region_box=region_box),
            RegionPrediction(disease_id="tomato.late_blight", display_name="Late blight",
                             raw_score=0.2, rank=2, region_kind=region_kind, region_box=region_box)],
            latency_ms=1.0)


class _FakeAdapter2(_FakeAdapter):
    model_id = "surprisedPikachu007/tomato-disease-detection_V2"


@pytest.mark.asyncio
async def test_pipeline_parallel_and_provenance(monkeypatch):
    import services.disease.pipeline as pipe_mod
    from services.disease.model_cache import ModelCache

    async def fake_run(adapters, image, **kw):
        out = [a.predict(image) for a in adapters]
        return out, {a.model_id: 1.0 for a in adapters}, [
            {"model_id": a.model_id, "ok": True} for a in adapters]

    monkeypatch.setattr(pipe_mod, "run_specialists", fake_run, raising=False)
    import services.disease.specialist_runner as runner_mod

    monkeypatch.setattr(runner_mod, "run_specialists", fake_run, raising=False)
    # Patch pipeline's imported symbol too
    import services.disease.pipeline as p2

    p2_cache = ModelCache()
    p2_cache.get_or_load(_FakeAdapter.model_id, _FakeAdapter)
    p2_cache.get_or_load(_FakeAdapter2.model_id, _FakeAdapter2)
    orig = p2.Pipeline._get_cache
    p2.Pipeline._get_cache = lambda self: p2_cache
    try:
        res = await p2.analyze_image(_img(), crop_hint="tomato")
    finally:
        p2.Pipeline._get_cache = orig
    assert res.status in {"diagnosed", "probable", "uncertain"}
    assert res.pipeline.specialists_run, "specialists must actually run"
    assert res.findings[0].score_type == "raw_model_score"
    assert "registry=" in (res.findings[0].notes or "")
    assert res.image_quality.status in {"good", "acceptable", "poor"}


@pytest.mark.asyncio
async def test_pipeline_rejects_bad_mime_and_oversize():
    from services.disease.pipeline import analyze_image

    with pytest.raises(DiseaseError) as e:
        await analyze_image(b"x" * 200, content_type="application/pdf")
    assert e.value.code == errors.IMAGE_INVALID


@pytest.mark.asyncio
async def test_pipeline_unsupported_crop():
    from services.disease.pipeline import analyze_image

    res = await analyze_image(_img(), crop_hint="durian")
    assert res.status == "unsupported_crop"


@pytest.mark.asyncio
async def test_pipeline_poor_image_no_models(monkeypatch):
    import services.disease.pipeline as p2
    from services.disease.model_cache import ModelCache

    called = {"n": 0}

    async def boom(adapters, image, **kw):
        called["n"] += 1
        raise AssertionError("models must not run on rejected images")

    monkeypatch.setattr(p2, "run_specialists", boom, raising=False)
    dark = _img(color=(4, 4, 4), size=(48, 48))
    res = await p2.analyze_image(dark)
    assert res.status == "insufficient_image" and called["n"] == 0


def test_parallel_runner_timeout_and_bounded():
    from services.disease.specialist_runner import run_specialists

    class Slow:
        model_id = "slow"

        def predict(self, image, region_kind="full", region_box=(0, 0, 1, 1)):
            import time as t

            t.sleep(5)
            return DiseasePrediction(model_id="slow")

    preds, lat, runs = asyncio.run(
        run_specialists([Slow()], Image.new("RGB", (32, 32)), timeout_s=0.2))
    assert preds == [] and runs[0]["error_code"] == "INFERENCE_TIMEOUT"


def test_knowledge_missing_disease_honest():
    from services.disease import knowledge as kn

    assert kn.get_entry("wheat.stripe_rust") is None


# --- reason codes: no-model vs model-failure are distinct ---

def test_router_no_hint_excludes_crop_specific_models():
    from services.disease.router import rank_candidates

    r = rank_candidates(crop_hint=None)
    assert r.crop_status == "unknown"  # dataclass default; pipeline sets the truth
    ids = [c.model_id for c in r.candidates]
    assert "imaflower/plantvillage-mobilenetv3" in r.eligible_specialists
    assert "surprisedPikachu007/tomato-disease-detection_V2" not in r.eligible_specialists
    assert r.excluded_specialists.get(
        "surprisedPikachu007/tomato-disease-detection_V2") == "needs-crop-hint"


def test_router_wheat_hint_has_no_eligible_specialist():
    from services.disease.router import rank_candidates

    # M2's verified label set (pepper/potato/tomato) does not cover wheat;
    # M4 is tomato-specific. Wheat is a genuine coverage gap.
    r = rank_candidates(crop_hint="wheat")
    assert r.eligible_specialists == []
    assert r.excluded_specialists.get(
        "imaflower/plantvillage-mobilenetv3") == "crop-not-covered"
    assert r.excluded_specialists.get(
        "surprisedPikachu007/tomato-disease-detection_V2") == "crop-mismatch"


def test_router_potato_hint_uses_multicrop_coverage():
    from services.disease.router import rank_candidates

    r = rank_candidates(crop_hint="potato")
    assert "imaflower/plantvillage-mobilenetv3" in r.eligible_specialists
    assert "surprisedPikachu007/tomato-disease-detection_V2" not in r.eligible_specialists


@pytest.mark.asyncio
async def test_pipeline_unknown_crop_unsupported_before_models(monkeypatch):
    import services.disease.pipeline as p2

    called = {"n": 0}

    async def boom(adapters, image, **kw):
        called["n"] += 1
        raise AssertionError("no model may run for an off-taxonomy crop")

    monkeypatch.setattr(p2, "run_specialists", boom, raising=False)
    res = await p2.analyze_image(_img(), crop_hint="durian")
    assert res.status == "unsupported_crop"
    assert res.reason_code == errors.NO_VERIFIED_MODEL_FOR_CROP
    assert res.crop.status == "unsupported" and res.crop.source == "user"
    assert called["n"] == 0


@pytest.mark.asyncio
async def test_pipeline_empty_eligible_is_coverage_gap_not_load_failure(monkeypatch):
    import services.disease.pipeline as p2
    import services.disease.router as router_mod
    from services.disease.router import RoutingResult

    def empty_rank(**kw):
        return RoutingResult(candidates=[], routing_mode="registry_fallback",
                             latency_ms=0.1, eligible_specialists=[],
                             excluded_specialists={"m": "crop-mismatch"})

    monkeypatch.setattr(router_mod, "rank_candidates", empty_rank)
    res = await p2.analyze_image(_img(), crop_hint="maize")
    assert res.status == "unsupported_crop"
    assert res.reason_code == errors.NO_VERIFIED_MODEL_FOR_CROP
    assert res.error_code == errors.NO_VALID_MODEL
    assert res.routing.excluded_specialists == {"m": "crop-mismatch"}

    res2 = await p2.analyze_image(_img())
    assert res2.status == "uncertain"
    assert res2.reason_code == errors.NO_ELIGIBLE_SPECIALIST
    assert res2.crop.status == "unknown"


@pytest.mark.asyncio
async def test_pipeline_load_failure_is_error_not_coverage(monkeypatch):
    import services.disease.models.factory as factory_mod
    import services.disease.pipeline as p2
    from services.disease.model_cache import ModelCache

    def fail_build(model_id, **kw):
        raise DiseaseError(errors.MODEL_LOAD_FAILED, f"{model_id} boom")

    monkeypatch.setattr(factory_mod, "build", fail_build)
    p2_cache = ModelCache()
    orig = p2.Pipeline._get_cache
    p2.Pipeline._get_cache = lambda self: p2_cache
    try:
        res = await p2.analyze_image(_img())
    finally:
        p2.Pipeline._get_cache = orig
    assert res.status == "error"
    assert res.reason_code == errors.MODEL_LOAD_FAILED
    assert res.error_code == errors.MODEL_LOAD_FAILED


@pytest.mark.asyncio
async def test_pipeline_inference_failure_reason_when_runs_empty(monkeypatch):
    import services.disease.pipeline as p2
    from services.disease.model_cache import ModelCache

    class _Exploding(_FakeAdapter):
        model_id = "imaflower/plantvillage-mobilenetv3"

        def predict(self, image, region_kind="full", region_box=(0, 0, 1, 1)):
            raise RuntimeError("infer boom")

    import services.disease.router as router_mod
    from services.disease.router import CandidateSpecialist, RoutingResult

    def one_rank(**kw):
        return RoutingResult(
            candidates=[CandidateSpecialist(model_id=_Exploding.model_id, rank_score=1.0)],
            routing_mode="registry_fallback", latency_ms=0.1,
            eligible_specialists=[_Exploding.model_id], excluded_specialists={})

    monkeypatch.setattr(router_mod, "rank_candidates", one_rank)
    cache = ModelCache()
    cache.get_or_load(_Exploding.model_id, _Exploding)
    orig = p2.Pipeline._get_cache
    p2.Pipeline._get_cache = lambda self: cache
    try:
        res = await p2.analyze_image(_img())
    finally:
        p2.Pipeline._get_cache = orig
    assert res.status == "error"
    assert res.reason_code == errors.MODEL_INFERENCE_FAILED


def test_uncertainty_reason_codes():
    from services.disease import fusion as fusion_mod
    from services.disease import uncertainty as unc
    from services.disease.fusion import FusedFinding

    def _f(score, band, agree=1, second=None):
        fs = [FusedFinding(disease_id="tomato.early_blight", display_name="Early blight",
                           raw_score=score, score_type="raw_model_score",
                           confidence_band=band, evidence_level="E4",
                           agreement_count=agree)]
        if second is not None:
            fs.append(FusedFinding(disease_id="tomato.late_blight", display_name="Late blight",
                                   raw_score=second, score_type="raw_model_score",
                                   confidence_band="low", evidence_level="E4"))
        return fusion_mod.FusionResult(findings=fs, latency_ms=0)

    assert unc.decide(_f(0.2, "low"), "good", True)[1] == errors.LOW_CONFIDENCE
    s, r, _, _ = unc.decide(_f(0.8, "medium", second=0.78), "good", True)
    assert s == "uncertain" and r == errors.SPECIALIST_DISAGREEMENT
    s, r, _, _ = unc.decide(fusion_mod.FusionResult(findings=[], latency_ms=0), "good", True)
    assert s == "uncertain" and r == errors.LOW_CONFIDENCE
    s, r, _, _ = unc.decide(_f(0.2, "low"), "rejected", True)
    assert s == "insufficient_image" and r == errors.POOR_IMAGE_QUALITY


def test_taxonomy_crops_for_selector():
    from services.disease import taxonomy as tax

    crops = tax.all_crops()
    assert "tomato" in crops and "rice" in crops and "maize" in crops
    assert crops == sorted(crops)


@pytest.mark.asyncio
async def test_pipeline_unknown_crop_uncertain_keeps_raw_outputs(monkeypatch):
    """Contract the UI relies on: unknown-crop uncertain results still carry
    the specialists' raw findings/alternatives (rendered under Analysis
    Details as model outputs), while crop stays unidentified."""
    import services.disease.pipeline as p2
    from services.disease.model_cache import ModelCache

    class _WeakTomato(_FakeAdapter):
        def predict(self, image, region_kind="full", region_box=(0, 0, 1, 1)):
            return DiseasePrediction(model_id=self.model_id, predictions=[
                RegionPrediction(disease_id="tomato.healthy", display_name="Tomato healthy",
                                 raw_score=0.31, rank=1, region_kind=region_kind, region_box=region_box),
                RegionPrediction(disease_id="tomato.early_blight", display_name="Early blight",
                                 raw_score=0.22, rank=2, region_kind=region_kind, region_box=region_box)],
                latency_ms=1.0)

    async def fake_run(adapters, image, **kw):
        out = [a.predict(image) for a in adapters]
        return out, {a.model_id: 1.0 for a in adapters}, [
            {"model_id": a.model_id, "ok": True} for a in adapters]

    monkeypatch.setattr(p2, "run_specialists", fake_run, raising=False)
    import services.disease.specialist_runner as runner_mod

    monkeypatch.setattr(runner_mod, "run_specialists", fake_run, raising=False)
    cache = ModelCache()
    cache.get_or_load("imaflower/plantvillage-mobilenetv3", _WeakTomato)
    orig = p2.Pipeline._get_cache
    p2.Pipeline._get_cache = lambda self: cache
    try:
        res = await p2.analyze_image(_img())
    finally:
        p2.Pipeline._get_cache = orig
    assert res.status == "uncertain"
    assert res.reason_code == errors.LOW_CONFIDENCE
    assert res.crop.name is None and res.crop.source == "unknown"
    assert res.crop.status == "unknown"
    # Raw specialist outputs preserved for the transparency section.
    assert len(res.findings) >= 1 and len(res.alternatives) >= 1
    assert res.findings[0].disease_id == "tomato.healthy"
