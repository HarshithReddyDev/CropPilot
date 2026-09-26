"""Latency benchmark CLI (measured only, never claimed).

Usage: python -m services.disease.benchmark [--cache-dir DIR] [--model MODEL_ID]
Prints p50/p95/max for QA, router, and each runnable stage. Stages whose
weights are absent are reported as skipped (not zero).
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from io import BytesIO


def _pct(lat: list[float], q: float) -> float:
    if not lat:
        return 0.0
    s = sorted(lat)
    return s[min(len(s) - 1, int(len(s) * q))]


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache-dir", default=None)
    ap.add_argument("--model", default="imaflower/plantvillage-mobilenetv3")
    ap.add_argument("--repeats", type=int, default=5)
    args = ap.parse_args(argv[1:])
    from PIL import Image

    from services.disease.image_pipeline import decode_image
    from services.disease.quality_gate import assess_quality
    from services.disease.router import rank_candidates

    img = Image.new("RGB", (640, 640), (70, 130, 60))
    buf = BytesIO()
    img.save(buf, format="JPEG")
    payload = buf.getvalue()
    q_lat, r_lat = [], []
    for _ in range(args.repeats):
        dec = decode_image(payload)
        t0 = time.perf_counter()
        assess_quality(dec)
        q_lat.append((time.perf_counter() - t0) * 1000.0)
        t0 = time.perf_counter()
        rank_candidates(crop_hint="tomato")
        r_lat.append((time.perf_counter() - t0) * 1000.0)
    print(f"quality_gate ms: p50={_pct(q_lat,.5):.1f} p95={_pct(q_lat,.95):.1f} max={max(q_lat):.1f}")
    print(f"router ms: p50={_pct(r_lat,.5):.1f} p95={_pct(r_lat,.95):.1f} max={max(r_lat):.1f}")
    try:
        from services.disease.models.factory import build

        a = build(args.model, cache_dir=args.cache_dir)
        t0 = time.perf_counter()
        a.load()
        print(f"{args.model} cold load ms: {(time.perf_counter()-t0)*1000.0:.0f}")
        dec = decode_image(payload)
        inf = []
        for _ in range(args.repeats):
            t0 = time.perf_counter()
            a.predict(dec.image)
            inf.append((time.perf_counter() - t0) * 1000.0)
        print(f"{args.model} warm infer ms: p50={statistics.median(inf):.0f} p95={_pct(inf,.95):.0f} max={max(inf):.0f}")
    except Exception as e:
        print(f"{args.model}: SKIPPED ({type(e).__name__}: {e})")
    try:
        from services.disease.embeddings import DinoV2EmbeddingModel

        em = DinoV2EmbeddingModel(cache_dir=args.cache_dir)
        t0 = time.perf_counter()
        em.load()
        print(f"dinov2 cold load ms: {(time.perf_counter()-t0)*1000.0:.0f}")
    except Exception as e:
        print(f"dinov2: SKIPPED ({type(e).__name__}: {e})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
