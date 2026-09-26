"""Tomato ViT adapter (Apache-2.0, E4).

Reported 98.87% is self-reported TRAIN-split accuracy and is preserved
as metric_context in the registry; it is never quoted as field accuracy
and never upgrades the evidence level. Labels come from the model config
at runtime; adapter refuses to predict when labels are unavailable.
"""

from __future__ import annotations

import threading
import time

from services.disease.base import DiseasePrediction, RegionPrediction
from services.disease.errors import DiseaseError, MODEL_LOAD_FAILED

MODEL_ID = "surprisedPikachu007/tomato-disease-detection_V2"


class TomatoViT:
    model_id = MODEL_ID
    version = "1.0.0"
    crop = "tomato"
    license = "Apache-2.0"
    evidence_level = "E4"
    production_allowed = True

    def __init__(self, cache_dir: str | None = None, device: str = "cpu"):
        self.cache_dir = cache_dir
        self.device = device if device in {"cpu", "cuda"} else "cpu"
        self._lock = threading.Lock()
        self._processor = None
        self._model = None
        self._labels: list[str] = []
        self.diseases: list[str] = []
        self.load_error: str | None = None

    def is_loaded(self) -> bool:
        return self._model is not None and bool(self._labels)

    def load(self) -> None:
        with self._lock:
            if self.is_loaded():
                return
            try:
                import torch
                from transformers import AutoImageProcessor, AutoModelForImageClassification

                kw: dict = {"trust_remote_code": False}
                if self.cache_dir:
                    kw["cache_dir"] = self.cache_dir
                self._processor = AutoImageProcessor.from_pretrained(self.model_id, **kw)
                self._model = AutoModelForImageClassification.from_pretrained(self.model_id, **kw)
                cfg_labels = getattr(getattr(self._model, "config", None), "id2label", None) or {}
                labels = [cfg_labels[k] for k in sorted(cfg_labels)] if cfg_labels else []
                if not labels:
                    raise RuntimeError("model config has no id2label mapping to verify")
                self._labels = [str(x) for x in labels]
                self.diseases = list(self._labels)
                if self.device == "cuda" and torch.cuda.is_available():
                    self._model.to("cuda")
                self._model.eval()
            except Exception as e:
                self.load_error = f"{type(e).__name__}: {e}"
                self._processor = None
                self._model = None
                raise DiseaseError(MODEL_LOAD_FAILED, f"{MODEL_ID} failed to load: {e}") from e

    def unload(self) -> None:
        with self._lock:
            self._model = None
            self._processor = None

    def predict(self, image, region_kind: str = "full",
                region_box: tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0)) -> DiseasePrediction:
        t0 = time.perf_counter()
        if not self.is_loaded():
            self.load()
        assert self._model is not None and self._processor is not None
        import torch

        inputs = self._processor(images=image, return_tensors="pt")
        device = next(self._model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.inference_mode():
            logits = self._model(**inputs).logits.squeeze(0).float().cpu()
        import numpy as np

        arr = logits.numpy()
        m = arr - arr.max()
        exp = np.exp(m)
        probs = exp / exp.sum()
        order = np.argsort(-probs)[:5]
        from services.disease import taxonomy as taxonomy_mod

        preds = []
        for r, i in enumerate(order.tolist()):
            label = str(self._labels[i])
            hit = taxonomy_mod.resolve_alias(label)
            did = str(hit["id"]) if hit else "tomato." + "".join(
                c.lower() if c.isalnum() else "_" for c in label).strip("_")
            preds.append(RegionPrediction(
                disease_id=did, display_name=label, raw_score=float(probs[i]),
                rank=r + 1, region_kind=region_kind, region_box=region_box))
        return DiseasePrediction(model_id=self.model_id, predictions=preds,
                                 latency_ms=(time.perf_counter() - t0) * 1000.0)
