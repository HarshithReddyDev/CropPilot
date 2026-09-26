"""Subsystem healthcheck CLI: registry, labels, ONNX, DINOv2, cache.

Usage: python -m services.disease.healthcheck [--cache-dir DIR]
Exit 1 on any production-gate failure. Heavy weights are NOT downloaded:
checks verify metadata + runtime import support + a synthetic-image pass
through QA/router/fusion without network weights.
"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache-dir", default=None)
    args = ap.parse_args(argv[1:])
    ok = True
    from services.disease import registry as registry_mod
    from services.disease import taxonomy as taxonomy_mod

    errs, warns = registry_mod.validate_registry()
    print(f"registry: {len(errs)} errors, {len(warns)} warnings (v{registry_mod.registry_version()})")
    for e in errs:
        print(f"  ERROR {e}")
        ok = False
    tax_errs = taxonomy_mod.validate_taxonomy()
    print(f"taxonomy: {len(tax_errs)} errors")
    for e in tax_errs[:10]:
        print(f"  ERROR {e}")
        ok = False
    try:
        import onnxruntime  # noqa: F401

        print(f"onnxruntime: available")
    except Exception as e:
        print(f"onnxruntime: MISSING ({e}) -- PlantVillage ONNX path falls back to torch")
    try:
        import transformers  # noqa: F401

        print("transformers: available (DINOv2/tomato path importable)")
    except Exception as e:
        print(f"transformers: MISSING ({e})")
        ok = False
    # Synthetic-image offline pass (transport/validation only, no weights).
    try:
        from io import BytesIO

        from PIL import Image

        from services.disease.image_pipeline import decode_image, make_regions
        from services.disease.quality_gate import assess_quality
        from services.disease.router import rank_candidates

        img = Image.new("RGB", (512, 512), (60, 140, 70))
        buf = BytesIO()
        img.save(buf, format="JPEG")
        dec = decode_image(buf.getvalue())
        q, _ = assess_quality(dec)
        r = rank_candidates(crop_hint="tomato")
        print(f"qa+router synthetic pass: quality={q.status} candidates={len(r.candidates)} mode={r.routing_mode}")
        _ = make_regions(dec.image)
    except Exception as e:
        print(f"offline pass FAILED: {e}")
        ok = False
    if args.cache_dir:
        from pathlib import Path

        try:
            Path(args.cache_dir).mkdir(parents=True, exist_ok=True)
            print(f"cache {args.cache_dir}: writable")
        except Exception as e:
            print(f"cache {args.cache_dir}: NOT writable ({e})")
            ok = False
    print("HEALTHY" if ok else "UNHEALTHY")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
