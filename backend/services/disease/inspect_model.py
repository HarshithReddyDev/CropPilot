"""Model inspector CLI: reports artifact/labels/license/runtime support.

Usage: python -m services.disease.inspect_model --model MODEL_ID [--cache-dir DIR]
"""

from __future__ import annotations

import argparse
import json
import sys


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--cache-dir", default=None)
    args = ap.parse_args(argv[1:])
    from services.disease.registry import get_model

    rec = get_model(args.model)
    if rec is None:
        print(f"unknown model id (not in registry): {args.model}")
        return 1
    info = {
        "model_id": rec.model_id, "task": rec.task, "architecture": rec.architecture,
        "artifact_files": rec.raw.get("artifact_files"), "labels_file": rec.raw.get("labels_file"),
        "labels_verified": rec.labels_verified, "weights_verified": rec.weights_verified,
        "license": rec.license, "license_status": rec.license_status,
        "evidence_level": rec.evidence_level, "field_validated": rec.field_validated,
        "production_allowed": rec.production_allowed, "status": rec.status,
        "metric_context": rec.metric_context, "input_size": rec.input_size,
        "estimated_memory_mb": rec.estimated_memory_mb,
        "runtime": {},
    }
    try:
        from services.disease.models.factory import build

        a = build(args.model, cache_dir=args.cache_dir, research_mode=True)
        a.load()
        info["runtime"] = {"loads": True, "labels": len(getattr(a, "_labels", []) or getattr(a, "diseases", [])),
                           "diseases": getattr(a, "diseases", [])[:10]}
        a.unload()
    except Exception as e:
        info["runtime"] = {"loads": False, "error": f"{type(e).__name__}: {e}"}
    print(json.dumps(info, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
