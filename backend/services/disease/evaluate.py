"""Offline evaluation CLI (never fabricates metrics).

Usage:
  python -m services.disease.evaluate --model imaflower/plantvillage-mobilenetv3 --manifest MANIFEST.json

MANIFEST.json: {"dataset": NAME, "split": SPLIT, "images": [{"path":..., "disease_id":...}], "hardware": ...}
"""

from __future__ import annotations

import argparse
import json
import sys
import time


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--cache-dir", default=None)
    ap.add_argument("--research", action="store_true")
    args = ap.parse_args(argv[1:])
    with open(args.manifest, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    images = manifest.get("images", [])
    if not images:
        print("manifest has no images; refusing to fabricate metrics.")
        return 1
    # PlantDoc synthetic mirrors must never be the field corpus.
    if "synthetic" in str(manifest.get("dataset", "")).lower():
        print("REFUSED: synthetic mirrors must not be used as the field evaluation corpus.")
        return 1
    from PIL import Image

    from services.disease.models.factory import build

    adapter = build(args.model, cache_dir=args.cache_dir, research_mode=args.research)
    adapter.load()
    hits = 0
    lat: list[float] = []
    per_crop: dict[str, list[int]] = {}
    for item in images:
        img = Image.open(item["path"]).convert("RGB")
        t0 = time.perf_counter()
        pred = adapter.predict(img)
        lat.append((time.perf_counter() - t0) * 1000.0)
        top = pred.predictions[0].disease_id if pred.predictions else None
        ok = int(top == item.get("disease_id"))
        hits += ok
        per_crop.setdefault(str(item.get("crop", "?")), []).append(ok)
    n = len(images)
    lat_sorted = sorted(lat)
    result = {
        "dataset": manifest.get("dataset"), "split": manifest.get("split"),
        "model": args.model, "n": n,
        "accuracy": hits / n if n else 0.0,
        "per_crop_accuracy": {k: sum(v) / len(v) for k, v in per_crop.items()},
        "latency_ms": {"p50": lat_sorted[n // 2], "p95": lat_sorted[int(n * 0.95) - 1] if n > 1 else lat_sorted[0],
                       "max": lat_sorted[-1]},
        "hardware": manifest.get("hardware", "unknown"),
        "date": time.strftime("%Y-%m-%d"),
        "notes": "Measured on supplied manifest only; lab accuracy, not field validation.",
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
