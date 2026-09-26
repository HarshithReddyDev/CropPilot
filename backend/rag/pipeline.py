import hashlib
import uuid

from core.config import settings

# Namespace for deterministic embedding-row identity. Stable ids make
# re-ingestion idempotent: same chunk + same model -> same row id.
_CHUNK_ID_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "croppilot:rag-chunk")


def chunk_row_id(collection: str, chunk_key: str, model: str) -> str:
    """Deterministic embedding-row id for (collection, chunk, model)."""
    return str(
        uuid.uuid5(
            _CHUNK_ID_NAMESPACE, f"{collection}:{chunk_key}:{model}"
        )
    )


def content_sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _libpq_dsn(url: str | None = None) -> str:
    """Plain libpq DSN from the SQLAlchemy sync URL.

    db_url_sync carries a driver suffix (postgresql+psycopg2://)
    that libpq rejects, so strip it for direct psycopg2 use.
    """
    url = url if url is not None else settings.db_url_sync
    if "://" in url:
        scheme, rest = url.split("://", 1)
        scheme = scheme.split("+", 1)[0]
        return f"{scheme}://{rest}"
    return url


class RAGPipeline:
    def __init__(self):
        self.vector_store = None
        self.embedding_model = None
        self.collection_name = settings.SCHEMES_VECTOR_COLLECTION

    async def initialize(self):
        from langchain_community.embeddings import OllamaEmbeddings
        from langchain_postgres import PGVector

        self.embedding_model = OllamaEmbeddings(
            model=settings.ASSISTANT_EMBEDDING_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
        )

        self.vector_store = PGVector(
            embeddings=self.embedding_model,
            collection_name=self.collection_name,
            connection=settings.db_url_sync,
            use_jsonb=True,
        )
        self._ensure_chunk_identity_index()

    def _ensure_chunk_identity_index(self):
        """Unique (collection, chunk_key, embedding_model) where tagged.

        Enforces one canonical embedding row per logical chunk per
        model at the DB level. Rows without chunk_key (other writers)
        are unaffected, and a future model upgrade simply uses new
        key values instead of colliding.
        """
        import psycopg2

        conn = psycopg2.connect(_libpq_dsn())
        try:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE UNIQUE INDEX IF NOT EXISTS
                    uq_embedding_chunk_identity
                    ON langchain_pg_embedding (
                        collection_id,
                        (cmetadata->>'chunk_key'),
                        (cmetadata->>'embedding_model')
                    ) WHERE cmetadata ? 'chunk_key'
                    """
                )
        finally:
            conn.close()

    def _find_chunk_row(self, row_id: str) -> dict | None:
        import psycopg2.extras

        import psycopg2

        conn = psycopg2.connect(_libpq_dsn())
        try:
            with conn.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cur:
                cur.execute(
                    "SELECT document, cmetadata FROM "
                    "langchain_pg_embedding WHERE id = %s",
                    (row_id,),
                )
                row = cur.fetchone()
                return dict(row) if row else None
        finally:
            conn.close()

    async def ingest_scheme(self, scheme_data: dict):
        if not self.vector_store:
            await self.initialize()

        model = settings.ASSISTANT_EMBEDDING_MODEL
        chunk_key = str(scheme_data["id"])
        row_id = chunk_row_id(self.collection_name, chunk_key, model)
        text = f"{scheme_data['scheme_name']}: {scheme_data['description']} {scheme_data.get('benefits', '')}"
        sha = content_sha(text)

        # Idempotent: same chunk + same model + unchanged text -> skip.
        # Changed text -> delete + re-insert under the stable id, so
        # row count never grows on re-ingestion.
        existing = self._find_chunk_row(row_id)
        if existing and (existing["cmetadata"] or {}).get("content_sha") == sha:
            return {"status": "skipped", "id": row_id}
        if existing:
            self.vector_store.delete(ids=[row_id])

        metadata = {
            "scheme_name": scheme_data["scheme_name"],
            "state_jurisdiction": scheme_data.get("state_jurisdiction", "All India"),
            "category": scheme_data.get("category", ""),
            "ministry": scheme_data.get("ministry", ""),
            "scheme_id": chunk_key,
            "chunk_key": chunk_key,
            "embedding_model": model,
            "content_sha": sha,
        }
        self.vector_store.add_texts([text], metadatas=[metadata], ids=[row_id])
        return {"status": "ingested", "id": row_id}

    async def hybrid_search(
        self, query: str, h3_index: str | None = None, top_k: int = 5
    ) -> list[dict]:
        if not self.vector_store:
            await self.initialize()

        results = []
        try:
            docs = self.vector_store.similarity_search_with_score(
                query, k=top_k
            )
            for doc, score in docs:
                results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score),
                })
        except Exception as e:
            pass

        return results

    async def hybrid_search_schemes(
        self, query: str, state_jurisdiction: str = "Telangana", top_k: int = 5
    ) -> list[dict]:
        if not self.vector_store:
            await self.initialize()

        results = []
        try:
            docs = self.vector_store.similarity_search_with_score(
                query, 
                k=top_k, 
                filter={"state_jurisdiction": {"$eq": state_jurisdiction}}
            )
            for doc, score in docs:
                results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score),
                })
        except Exception as e:
            from schemas.scheme import GovernmentSchemeResponse
            from repositories.scheme import scheme_repository
            from db.session import async_session_factory

            async with async_session_factory() as session:
                schemes = await scheme_repository.get_by_state(session, state_jurisdiction)
                results = [
                    {
                        "content": f"{s.scheme_name}: {s.description}",
                        "metadata": {"scheme_name": s.scheme_name},
                        "score": 1.0,
                    }
                    for s in schemes[:top_k]
                ]

        return results


rag_pipeline = RAGPipeline()
