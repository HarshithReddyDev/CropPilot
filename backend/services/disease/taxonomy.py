"""Disease taxonomy: stable IDs, display names, priorities. Canonical IDs
are never silently renamed; farmer aliases map to canonical IDs."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
TAXONOMY_PATH = DATA_DIR / "disease_taxonomy.json"


def _load() -> dict:
    with open(TAXONOMY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _doc() -> dict:
    return _load()


def all_diseases() -> list[dict]:
    return list(_doc().get("diseases", []))


def get_disease(disease_id: str) -> dict | None:
    for d in all_diseases():
        if d.get("id") == disease_id:
            return d
    return None


def diseases_for_crop(crop: str) -> list[dict]:
    c = (crop or "").strip().lower()
    return [d for d in all_diseases() if str(d.get("crop", "")).lower() == c]


def all_crops() -> list[str]:
    """Sorted unique crop names in the taxonomy (drives the manual crop
    selector; taxonomy membership is NOT model coverage)."""
    return sorted({str(d.get("crop", "")).lower() for d in all_diseases() if d.get("crop")})


def resolve_alias(name: str) -> dict | None:
    """Map a farmer/common name to a canonical disease row (exact/alias match)."""
    q = (name or "").strip().lower()
    if not q:
        return None
    for d in all_diseases():
        if str(d.get("display_name", "")).lower() == q or str(d.get("id", "")).lower() == q:
            return d
        for a in d.get("aliases", []) or []:
            if str(a).lower() == q:
                return d
    return None


def display_name(disease_id: str) -> str:
    d = get_disease(disease_id)
    if d:
        return str(d.get("display_name", disease_id))
    return disease_id


def priority_filter(level: str) -> list[dict]:
    """level in {'india_high','telangana_high'}; 'high' values only."""
    if level == "india_high":
        return [d for d in all_diseases() if d.get("india") == "high"]
    if level == "telangana_high":
        return [d for d in all_diseases() if d.get("telangana") == "high"]
    raise ValueError(f"unknown priority level: {level}")


def validate_taxonomy() -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for d in all_diseases():
        did = d.get("id", "")
        if not did or "." not in did:
            errors.append(f"malformed disease id: {did!r}")
        if did in seen:
            errors.append(f"duplicate disease id: {did}")
        seen.add(did)
        if not d.get("display_name"):
            errors.append(f"{did}: missing display_name")
        if not d.get("crop"):
            errors.append(f"{did}: missing crop")
    return errors
