"""Rice-blast YOLO11 adapter — RESEARCH ONLY (no license declared).

Gated behind DISEASE_ENABLE_RESEARCH_MODELS. Never production. Only real
detector output becomes a bounding box; each detection carries its box.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path

from services.disease.base import DiseasePrediction, RegionPrediction
from services.disease.errors import DiseaseError, MODEL_LOAD_FAILED

MODEL_ID = "musheijaa/rice-blast-disease-detection-yolo11"


class RiceBlastYOLO:
    model_id = MODEL_ID
    version = "1.0.0"
    crop = "rice"
    license = "NONE DECLARED"
    evidence_level = "E3"
    production_allowed = False

    def __init__(self, cache_dir: str | None = None, device: str = "cpu", enabled: bool = False):
        self.cache_dir = cache_dir
        self._enabled = enabled
        self._lock = threading.Lock()
        self._model = None
        self.diseases = ["rice.rice_blast"]
        self.load_error: str | None = None

    def is_loaded(self) -> bool:
        return self._model is not None

    def load(self) -> None:
        with self._lock:
            if self.is_loaded():
                return
            if not self._enabled:
                raise DiseaseError(MODEL_LOAD_FAILED, f"{MODEL_ID} is research-only and research mode is disabled")
            try:
                snap = self._snapshot()
                weights = snap / "rice_blast_best.pt"
                if not weights.exists():
                    weights = snap / "model.onnx"
                if not weights.exists():
                    raise RuntimeError(f"no weight file in {snap}")
                from ultralytics import YOLO

                self._model = YOLO(str(weights))
            except Exception as e:
                self.load_error = f"{type(e).__name__}: {e}"
                raise DiseaseError(MODEL_LOAD_FAILED, f"{MODEL_ID} failed to load: {e}") from e

    def _snapshot(self) -> Path:
        from huggingface_hub import snapshot_download

        kw: dict = {"allow_patterns": ["model.onnx", "rice_blast_best.pt"]}
        if self.cache_dir:
            kw["cache_dir"] = self.cache_dir
        return Path(snapshot_download(repo_id=MODEL_ID, **kw))

    def unload(self) -> None:
        with self._lock:
            self._model = None

    def predict(self, image, region_kind: str = "full",
                region_box: tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0)) -> DiseasePrediction:
        t0 = time.perf_counter()
        if not self.is_loaded():
            self.load()
        assert self._model is not None
        import numpy as np

        res = self._model(np.asarray(image), verbose=False)[0]
        preds: list[RegionPrediction] = []
        names = getattr(res, "names", {}) or {}
        boxes = getattr(res, "boxes", None)
        if boxes is not None:
            for i, box in enumerate(boxes):
                x1, y1, x2, y2 = [float(v) for v in box.xyxy[0].tolist()]
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                label = str(names.get(cls, "rice blast"))
                w, h = image.size
                preds.append(RegionPrediction(
                    disease_id="rice.rice_blast", display_name=label,
                    raw_score=conf, rank=i + 1, region_kind="detector",
                    region_box=(x1 / w, y1 / h, x2 / w, y2 / h)))
        preds.sort(key=lambda p: p.raw_score, reverse=True)
        for i, p in enumerate(preds):
            p.rank = i + 1
        return DiseasePrediction(model_id=self.model_id, predictions=preds,
                                 latency_ms=(time.perf_counter() - t0) * 1000.0)
