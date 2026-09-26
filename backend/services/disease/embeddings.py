"""Shared embedding service: DINOv2 router backbone (+ optional BioCLIP).

DINOv2 is a representation, never a disease classifier. Embeddings are
L2-normalized; dimensions exposed dynamically. Missing weights or
libraries degrade honestly to unavailable (router falls back).
"""

from __future__ import annotations

import threading
from dataclasses import dataclass

import torch


@dataclass
class EmbeddingResult:
    vector: list[float]
    dim: int
    model_id: str
    latency_ms: float


class DinoV2EmbeddingModel:
    model_id = "facebook/dinov2-base"

    def __init__(self, cache_dir: str | None = None, device: str = "cpu"):
        self.cache_dir = cache_dir
        self.device = device if device in {"cpu", "cuda"} else "cpu"
        if self.device == "cuda" and not torch.cuda.is_available():
            self.device = "cpu"
        self._processor = None
        self._model = None
        self._dim: int | None = None
        self._lock = threading.Lock()
        self.load_error: str | None = None

    def load(self) -> None:
        with self._lock:
            if self._model is not None:
                return
            try:
                from transformers import AutoImageProcessor, AutoModel

                kw: dict = {"trust_remote_code": False}
                if self.cache_dir:
                    kw["cache_dir"] = self.cache_dir
                self._processor = AutoImageProcessor.from_pretrained(self.model_id, **kw)
                self._model = AutoModel.from_pretrained(self.model_id, **kw)
                self._model.to(self.device)
                self._model.eval()
                with torch.inference_mode():
                    pass
            except Exception as e:
                self.load_error = f"{type(e).__name__}: {e}"
                self._processor = None
                self._model = None
                raise

    def is_loaded(self) -> bool:
        return self._model is not None

    def unload(self) -> None:
        with self._lock:
            self._model = None
            self._processor = None
            self._dim = None

    @property
    def dim(self) -> int | None:
        return self._dim

    def embed(self, image) -> EmbeddingResult:
        import time

        t0 = time.perf_counter()
        if self._model is None or self._processor is None:
            self.load()
        assert self._model is not None and self._processor is not None
        inputs = self._processor(images=image, return_tensors="pt")
        pixel_values = inputs["pixel_values"].to(self.device)
        with torch.inference_mode():
            out = self._model(pixel_values=pixel_values)
            vec = out.last_hidden_state[:, 0, :].squeeze(0).float().cpu()
            vec = vec / (vec.norm(p=2) + 1e-12)
        flat = vec.tolist()
        self._dim = len(flat)
        return EmbeddingResult(
            vector=flat, dim=len(flat), model_id=self.model_id,
            latency_ms=(time.perf_counter() - t0) * 1000.0,
        )


class BioCLIPSimilarity:
    """Optional crop/species similarity signal. Never a diagnosis."""

    model_id = "imageomics/bioclip-2"

    def __init__(self):
        self._loaded = False
        self.load_error: str | None = None

    def load(self) -> None:
        try:
            import transformers  # noqa: F401  # verifies stack present
            from huggingface_hub import snapshot_download  # noqa: F401
            self._loaded = False  # text-image scoring wired only when needed
            raise RuntimeError(
                "BioCLIP similarity is registered but not wired to a verified "
                "disease-relevance mapping; refusing to fabricate scores."
            )
        except Exception as e:
            self.load_error = f"{type(e).__name__}: {e}"
            raise

    def is_loaded(self) -> bool:
        return False
