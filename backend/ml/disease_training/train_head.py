"""Training heads: frozen DINOv2 encoder + linear probe / specialist heads.

Interfaces only -- real training runs explicitly on licensed manifests,
never at app startup. Export writes torchscript/onnx + label json.
"""

from __future__ import annotations


def train_head(manifest_path: str, out_dir: str, backbone: str = "facebook/dinov2-base") -> dict:
    from ml.disease_training.datasets import load_manifest

    manifest = load_manifest(manifest_path)
    return {"status": "not_run",
            "reason": "training runs explicitly on operator hardware; manifest validated.",
            "images": len(manifest["images"]), "backbone": backbone, "out_dir": out_dir}


def train_specialist(manifest_path: str, out_dir: str, crop: str) -> dict:
    from ml.disease_training.datasets import load_manifest

    manifest = load_manifest(manifest_path)
    return {"status": "not_run", "crop": crop,
            "images": len(manifest["images"]), "out_dir": out_dir}


def calibrate(manifest_path: str, model_id: str) -> dict:
    return {"status": "not_run", "model_id": model_id,
            "note": "calibrate on held-out field data; see services.disease.calibration"}


def evaluate(manifest_path: str, model_id: str) -> dict:
    return {"status": "not_run", "model_id": model_id}


def export(model_id: str, out_dir: str, fmt: str = "onnx") -> dict:
    if fmt not in {"onnx", "torchscript"}:
        raise ValueError(f"unsupported export format: {fmt}")
    return {"status": "not_run", "model_id": model_id, "format": fmt}
