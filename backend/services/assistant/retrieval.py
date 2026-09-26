"""Assistant RAG retrieval: hybrid search + rerank + citations over schemes.

Wraps the existing ``rag.pipeline`` vector store behind one function so the
tool layer keeps a stable name. Hybrid = vector search first, keyword
prefilter boost second, deterministic rerank third. Failures fall back to
the relational scheme catalog (never an exception to the agent).
"""

from __future__ import annotations

import logging
import re

from core.config import settings
from .types import Citation

logger = logging.getLogger(__name__)

_TOKEN_RE = re.compile(r"[a-z0-9]{3,}")


def _keywords(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def _keyword_overlap(query: str, content: str) -> int:
    return len(_keywords(query) & _keywords(content))


async def retrieve_schemes(
    query: str,
    state: str | None = None,
    top_k: int | None = None,
) -> tuple[str, list[Citation]]:
    """Hybrid scheme retrieval returning (compact_json_text, citations).

    Rerank: vector score adjusted by keyword overlap so exact-name queries
    surface the right scheme even when embeddings rank loosely.
    """
    from rag.pipeline import rag_pipeline
    from repositories.scheme import scheme_repository
    from db.session import async_session_factory

    state = state or "Telangana"
    top_k = top_k or settings.ASSISTANT_RAG_TOP_K
    rerank_k = settings.ASSISTANT_RAG_RERANK_K

    candidates: list[dict] = []
    try:
        candidates = await rag_pipeline.hybrid_search_schemes(
            query, state_jurisdiction=state, top_k=top_k
        )
    except Exception as exc:  # vector store down: relational fallback below
        from telemetry.assistant_metrics import RAG_FALLBACK

        RAG_FALLBACK.labels(reason="vector_error").inc()
        logger.warning("assistant_rag_vector_failed: %s", exc)

    scope = state
    if not candidates:
        from telemetry.assistant_metrics import RAG_FALLBACK

        RAG_FALLBACK.labels(reason="empty").inc()
        async with async_session_factory() as session:
            schemes = await scheme_repository.get_by_state(session, state)
            if not schemes:
                # National fallback: the KB may simply not cover the
                # requested state (e.g. a scheme name asked with an
                # invented state scope). Broaden once, and MARK the scope
                # so the answer qualifies applicability instead of
                # presenting another state's schemes as local.
                schemes = await scheme_repository.list_active(session, limit=top_k)
                scope = "national-fallback"
                if schemes:
                    RAG_FALLBACK.labels(reason="national").inc()
        candidates = [
            {
                "content": f"{s.scheme_name}: {s.description}",
                "metadata": {"scheme_name": s.scheme_name},
                "score": 1.0,
            }
            for s in schemes[:top_k]
        ]

    # Rerank: vector rank weight + keyword overlap bonus, stable order.
    ranked = sorted(
        candidates,
        key=lambda c: (
            -_keyword_overlap(query, str(c.get("content", ""))),
            float(c.get("score") or 0.0),
        ),
    )[:rerank_k]

    import json

    citations = [
        Citation(
            source=f"scheme:{c.get('metadata', {}).get('scheme_name', 'catalog')}",
            title=str(c.get("metadata", {}).get("scheme_name", "Scheme")),
            snippet=str(c.get("content", ""))[:500],
        )
        for c in ranked
    ]
    payload = [
        {
            "scheme": c.get("metadata", {}).get("scheme_name"),
            "snippet": str(c.get("content", ""))[:500],
        }
        for c in ranked
    ]
    return json.dumps({"state": state, "scope": scope, "results": payload}), citations
