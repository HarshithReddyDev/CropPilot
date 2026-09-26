"""Dataset manifests: explicit, licensed, never auto-downloaded.

A manifest names the dataset type (plantvillage|plantdoc|india_field),
split, license, and image list. Training entry points accept only these
manifests. PlantDoc synthetic mirrors are rejected as field corpora.
"""

from __future__ import annotations

import json

ALLOWED_TYPES = {"plantvillage", "plantdoc", "india_field", "telangana_field"}


def load_manifest(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        m = json.load(f)
    if m.get("dataset_type") not in ALLOWED_TYPES:
        raise ValueError(f"unknown dataset_type: {m.get('dataset_type')}")
    if not m.get("license"):
        raise ValueError("manifest must declare a dataset license")
    if not m.get("images"):
        raise ValueError("manifest contains no images")
    if "synthetic" in str(m.get("dataset", "")).lower() and m.get("use_as") == "field_eval":
        raise ValueError("synthetic mirrors must not be used as the field evaluation corpus")
    return m
