"""CropPilot disease diagnosis package.

Evidence-aware, CPU-first, extensible crop-disease diagnosis platform.
No mock results: every production finding originates from real model
inference, deterministic image QA, registry metadata, retrieved
knowledge, or an explicit uncertainty/error state.
"""

from __future__ import annotations


def __getattr__(name: str):
    if name in {"analyze_image", "get_pipeline"}:
        from services.disease.pipeline import analyze_image as _a, get_pipeline as _g

        return _a if name == "analyze_image" else _g
    raise AttributeError(name)


__all__ = ["analyze_image", "get_pipeline"]
