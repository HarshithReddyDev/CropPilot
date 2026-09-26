"""Disease prototype index: versioned normalized embeddings + metadata.

No fabricated vectors ship. Build only from explicitly supplied,
licensed reference images:
  python -m services.disease.prototypes build --manifest MANIFEST.json ...
"""

from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path

PROTOTYPE_VERSION = "1.0.0"


@dataclass
class Prototype:
    disease_id: str
    crop: str
    vector: list[float]
    source: str
    image_ref: str


def cosine(a: list[float], b: list[float]) -> float:
    n = min(len(a), len(b))
    if n == 0:
        return 0.0
    dot = sum(x * y for x, y in zip(a[:n], b[:n]))
    na = math.sqrt(sum(x * x for x in a[:n])) + 1e-12
    nb = math.sqrt(sum(y * y for y in b[:n])) + 1e-12
    return dot / (na * nb)


def normalize(vec: list[float]) -> list[float]:
    n = math.sqrt(sum(x * x for x in vec)) + 1e-12
    return [x / n for x in vec]


class PrototypeIndex:
    def __init__(self, prototypes: list[Prototype] | None = None, version: str = PROTOTYPE_VERSION):
        self.prototypes = prototypes or []
        self.version = version

    @classmethod
    def load(cls, path: str | Path) -> "PrototypeIndex":
        with open(path, "r", encoding="utf-8") as f:
            doc = json.load(f)
        protos = [Prototype(**p) for p in doc.get("prototypes", [])]
        return cls(protos, version=str(doc.get("version", PROTOTYPE_VERSION)))

    def save(self, path: str | Path) -> None:
        doc = {
            "version": self.version,
            "count": len(self.prototypes),
            "prototypes": [p.__dict__ for p in self.prototypes],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f)

    def query(self, vector: list[float], crop: str | None = None, top_k: int = 5) -> list[tuple[Prototype, float]]:
        scored: list[tuple[Prototype, float]] = []
        for p in self.prototypes:
            if crop and p.crop.lower() != crop.lower():
                continue
            scored.append((p, cosine(vector, p.vector)))
        scored.sort(key=lambda t: t[1], reverse=True)
        return scored[:top_k]


def default_index_path(cache_dir: str | None) -> Path | None:
    if not cache_dir:
        return None
    return Path(cache_dir) / "disease_prototypes_v1.json"


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] != "build":
        print("usage: python -m services.disease.prototypes build --manifest MANIFEST.json --out OUT.json [--cache-dir DIR]")
        print("MANIFEST.json: {\"images\": [{\"path\": ..., \"disease_id\": ..., \"crop\": ..., \"source\": ...}]}")
        return 2
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cache-dir", default=None)
    args = ap.parse_args(argv[2:])
    with open(args.manifest, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    images = manifest.get("images", [])
    if not images:
        print("manifest contains no images; refusing to fabricate prototypes.")
        return 1
    from PIL import Image

    from services.disease.embeddings import DinoV2EmbeddingModel

    embedder = DinoV2EmbeddingModel(cache_dir=args.cache_dir)
    protos: list[Prototype] = []
    for item in images:
        for key in ("path", "disease_id", "crop"):
            if not item.get(key):
                print(f"manifest entry missing {key}: {item}")
                return 1
        img = Image.open(item["path"]).convert("RGB")
        res = embedder.embed(img)
        protos.append(
            Prototype(
                disease_id=item["disease_id"], crop=item["crop"],
                vector=normalize(res.vector),
                source=item.get("source", "farmer-supplied"),
                image_ref=item["path"],
            )
        )
    PrototypeIndex(protos).save(args.out)
    print(f"wrote {len(protos)} prototypes to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
