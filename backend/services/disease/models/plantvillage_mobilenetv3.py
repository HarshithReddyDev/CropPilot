"""Real PlantVillage MobileNetV3 adapter (MIT, E4, PlantVillage-derived).

Artifact resolution order: local ONNX (preferred CPU path) -> torchscript
-> pytorch_model.bin. Labels come from the downloaded class_names.json at
runtime; adapter refuses to predict when labels are missing. HF Hub is the
only download source; model_id allow-listed by the registry (no arbitrary
URLs). torch.inference_mode, CPU-first, batch-capable.
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path

from services.disease.base import DiseasePrediction, RegionPrediction
from services.disease.errors import DiseaseError, MODEL_LOAD_FAILED

MODEL_ID = "imaflower/plantvillage-mobilenetv3"
LABELS_FILE = "class_names.json"
EVIDENCE = "PlantVillage-derived (lab images, not field validation)"


def _snapshot_dir(cache_dir: str | None) -> Path | None:
    if not cache_dir:
        return None
    base = Path(cache_dir) / ("models--" + MODEL_ID.replace("/", "--"))
    snap = base / "snapshots"
    if not snap.exists():
        return None
    revs = sorted([p for p in snap.iterdir() if p.is_dir()])
    # Only trust a snapshot that actually contains the labels file; a
    # partial/interrupted download must heal via ensure_snapshot, never
    # fail the whole pipeline with a confusing "missing" error.
    complete = [p for p in revs if (p / LABELS_FILE).exists()]
    return complete[-1] if complete else None


def ensure_snapshot(cache_dir: str | None) -> Path:
    from huggingface_hub import snapshot_download

    allow = {"model.onnx", "model.onnx.data", "model_scripted.pt",
             "pytorch_model.bin", "class_names.json", "training_config.json", "config.json"}
    kw: dict = {"allow_patterns": sorted(allow)}
    if cache_dir:
        kw["cache_dir"] = cache_dir
    path = snapshot_download(repo_id=MODEL_ID, **kw)
    return Path(path)


class PlantVillageMobileNetV3:
    model_id = MODEL_ID
    version = "1.0.0"
    crop = None
    license = "MIT"
    evidence_level = "E4"
    production_allowed = True

    def __init__(self, cache_dir: str | None = None, device: str = "cpu"):
        self.cache_dir = cache_dir
        self.device = device if device in {"cpu", "cuda"} else "cpu"
        self._lock = threading.Lock()
        self._session = None
        self._torch_model = None
        self._labels: list[str] = []
        self.diseases: list[str] = []
        self.load_error: str | None = None

    def is_loaded(self) -> bool:
        return bool(self._labels) and (self._session is not None or self._torch_model is not None)

    def load(self) -> None:
        with self._lock:
            if self.is_loaded():
                return
            try:
                snap = _snapshot_dir(self.cache_dir) or ensure_snapshot(self.cache_dir)
                labels_path = snap / LABELS_FILE
                if not labels_path.exists():
                    raise RuntimeError(f"{LABELS_FILE} missing in {snap}")
                with open(labels_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                labels = raw if isinstance(raw, list) else raw.get("classes") or raw.get("labels") or raw.get("class_names")
                if not labels or not isinstance(labels, list):
                    raise RuntimeError(f"{LABELS_FILE} has no verifiable label list")
                self._labels = [str(x) for x in labels]
                self.diseases = list(self._labels)
                onnx_path = snap / "model.onnx"
                if onnx_path.exists():
                    try:
                        import onnxruntime as ort

                        opts = ort.SessionOptions()
                        opts.intra_op_num_threads = 1
                        opts.inter_op_num_threads = 1
                        self._session = ort.InferenceSession(str(onnx_path), sess_options=opts, providers=["CPUExecutionProvider"])
                        return
                    except Exception:
                        self._session = None  # fall through to torch
                scripted = snap / "model_scripted.pt"
                weights = snap / "pytorch_model.bin"
                import torch

                if scripted.exists():
                    self._torch_model = torch.jit.load(str(scripted), map_location="cpu")
                elif weights.exists():
                    # Architecture unknown from registry alone; refuse to guess weights-only load.
                    raise RuntimeError("pytorch_model.bin present but no architecture/config to load it safely; ONNX/scripted unavailable")
                else:
                    raise RuntimeError("no loadable artifact (model.onnx/model_scripted.pt) in snapshot")
                self._torch_model.eval()
            except Exception as e:
                self.load_error = f"{type(e).__name__}: {e}"
                self._session = None
                self._torch_model = None
                raise DiseaseError(MODEL_LOAD_FAILED, f"{MODEL_ID} failed to load: {e}") from e

    def unload(self) -> None:
        with self._lock:
            self._session = None
            self._torch_model = None

    def _preprocess(self, image, size: tuple[int, int] = (224, 224)):
        from PIL import Image as PILImage

        import torch

        img = image.resize(size, PILImage.BILINEAR).convert("RGB")
        import numpy as np

        arr = (np.asarray(img).astype("float32") / 255.0 - 0.5) / 0.5
        arr = arr.transpose(2, 0, 1)[None]
        return torch.from_numpy(arr), arr

    def predict(self, image, region_kind: str = "full",
                region_box: tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0)) -> DiseasePrediction:
        t0 = time.perf_counter()
        if not self.is_loaded():
            self.load()
        import numpy as np

        if self._session is not None:
            _, arr = self._preprocess(image)
            import torch

            with torch.inference_mode():
                out = self._session.run(None, {self._session.get_inputs()[0].name: arr})[0]
            logits = np.asarray(out).reshape(-1)
        else:
            tensor, _ = self._preprocess(image)
            import torch

            with torch.inference_mode():
                out = self._torch_model(tensor)
            logits = np.asarray(out.detach().cpu()).reshape(-1)
        # Softmax (raw model score, NOT calibrated probability).
        m = logits - logits.max()
        exp = np.exp(m)
        probs = exp / exp.sum()
        order = np.argsort(-probs)[:5]
        preds = [
            RegionPrediction(
                disease_id=self._canonical(i),
                display_name=str(self._labels[i]),
                raw_score=float(probs[i]),
                rank=r + 1,
                region_kind=region_kind,
                region_box=region_box,
            )
            for r, i in enumerate(order.tolist())
        ]
        return DiseasePrediction(model_id=self.model_id, predictions=preds, latency_ms=(time.perf_counter() - t0) * 1000.0)

    def _canonical(self, idx: int) -> str:
        from services.disease import taxonomy as taxonomy_mod

        label = str(self._labels[idx])
        hit = taxonomy_mod.resolve_alias(label)
        if hit:
            return str(hit["id"])
        # PlantVillage label with no taxonomy row: namespace honestly, never merge.
        slug = "".join(c.lower() if c.isalnum() else "_" for c in label).strip("_")
        return f"plantvillage.{slug}"
