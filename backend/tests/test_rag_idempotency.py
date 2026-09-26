"""RAG embedding idempotency regression tests (no DB, no Ollama).

Verifies the deterministic chunk-identity contract in rag/pipeline.py:
same chunk + same model -> same row id; unchanged text -> skip;
changed text -> re-insert under the stable id (count never grows).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag.pipeline import _libpq_dsn, chunk_row_id, content_sha  # noqa: E402


def test_chunk_row_id_deterministic():
    a = chunk_row_id("government_schemes", "s1", "bge-m3")
    b = chunk_row_id("government_schemes", "s1", "bge-m3")
    assert a == b


def test_chunk_row_id_model_upgrade_gets_new_id():
    old = chunk_row_id("government_schemes", "s1", "bge-m3")
    new = chunk_row_id("government_schemes", "s1", "bge-m4")
    assert old != new  # upgrades must not collide with existing rows


def test_chunk_row_id_chunk_scoped():
    assert chunk_row_id("government_schemes", "s1", "bge-m3") != chunk_row_id(
        "government_schemes", "s2", "bge-m3"
    )


def test_content_sha_stable_and_sensitive():
    assert content_sha("abc") == content_sha("abc")
    assert content_sha("abc") != content_sha("abd")


def test_libpq_dsn_strips_driver():
    assert (
        _libpq_dsn("postgresql+psycopg2://u:p@host:5432/db")
        == "postgresql://u:p@host:5432/db"
    )
    assert (
        _libpq_dsn("postgresql://u:p@host:5432/db")
        == "postgresql://u:p@host:5432/db"
    )


class _StubStore:
    def __init__(self):
        self.added = []
        self.deleted = []

    def delete(self, ids):
        self.deleted.extend(ids)

    def add_texts(self, texts, metadatas=None, ids=None):
        self.added.append((texts, metadatas, ids))


def _scheme(**over):
    d = {
        "id": "s1",
        "scheme_name": "Test Scheme",
        "description": "Desc",
        "benefits": "Ben",
        "state_jurisdiction": "Telangana",
        "category": "C",
        "ministry": "M",
    }
    d.update(over)
    return d


def test_ingest_skips_unchanged_chunk(monkeypatch):
    import asyncio

    from rag.pipeline import RAGPipeline

    p = RAGPipeline.__new__(RAGPipeline)
    p.collection_name = "government_schemes"
    p.vector_store = _StubStore()
    p._find_chunk_row = lambda row_id: {
        "document": "x",
        "cmetadata": {"content_sha": "MATCH"},
    }
    import rag.pipeline as mod

    monkeypatch.setattr(mod, "content_sha", lambda t: "MATCH")
    out = asyncio.run(p.ingest_scheme(_scheme()))
    assert out["status"] == "skipped"
    assert p.vector_store.added == []
    assert p.vector_store.deleted == []


def test_ingest_reinserts_changed_chunk_under_stable_id(monkeypatch):
    import asyncio

    from rag.pipeline import RAGPipeline

    p = RAGPipeline.__new__(RAGPipeline)
    p.collection_name = "government_schemes"
    p.vector_store = _StubStore()
    p._find_chunk_row = lambda row_id: {
        "document": "old",
        "cmetadata": {"content_sha": "OLD"},
    }
    import rag.pipeline as mod

    monkeypatch.setattr(mod, "content_sha", lambda t: "NEW")
    out = asyncio.run(p.ingest_scheme(_scheme()))
    assert out["status"] == "ingested"
    rid = out["id"]
    assert p.vector_store.deleted == [rid]
    assert p.vector_store.added[0][2] == [rid]
    meta = p.vector_store.added[0][1][0]
    assert meta["chunk_key"] == "s1"
    assert meta["content_sha"] == "NEW"
    assert "embedding_model" in meta
