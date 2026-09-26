"""Disease knowledge: JSON-file guidance + optional RAG namespace.

Diagnostic evidence (model outputs) is always separated from agronomic
guidance (retrieved text). No pesticide names/doses are invented: if a
disease has no verified entry, callers must say so explicitly.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
KNOWLEDGE_PATH = DATA_DIR / "disease_knowledge.json"


@lru_cache(maxsize=1)
def _doc() -> dict:
    with open(KNOWLEDGE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_entry(disease_id: str, language: str = "en") -> dict | None:
    for e in _doc().get("entries", []):
        if e.get("disease_id") == disease_id and e.get("language", "en") == language:
            return e
    for e in _doc().get("entries", []):
        if e.get("disease_id") == disease_id:
            return e
    return None


async def retrieve(disease_ids: list[str], language: str = "en", top_k: int = 3) -> tuple[list[dict], bool]:
    """Return (items, rag_used). File guidance first; optional RAG second."""
    items: list[dict] = []
    for did in disease_ids[:top_k]:
        e = get_entry(did, language)
        if e:
            items.append(e)
    rag_used = False
    try:
        from rag.pipeline import RAGPipeline  # optional namespace

        pipe = RAGPipeline()
        for did in disease_ids[:top_k]:
            if get_entry(did, language):
                continue
            hits = await pipe.hybrid_search(f"crop disease {did} symptoms management", top_k=2)
            for h in hits:
                md = h.get("metadata", {}) or {}
                if "disease" not in str(md).lower() and "crop" not in str(md).lower():
                    continue
                items.append({
                    "disease_id": did,
                    "title": str(md.get("title", did)),
                    "symptoms": [],
                    "similar_conditions": [],
                    "management": [str(h.get("content", ""))[:800]],
                    "prevention": [],
                    "source": str(md.get("source", "CropPilot RAG")),
                    "language": language,
                })
                rag_used = True
    except Exception:
        pass
    return items, rag_used
