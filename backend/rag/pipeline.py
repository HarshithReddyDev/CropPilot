from core.config import settings


class RAGPipeline:
    def __init__(self):
        self.vector_store = None
        self.embedding_model = None
        self.collection_name = settings.SCHEMES_VECTOR_COLLECTION

    async def initialize(self):
        from langchain_community.embeddings import OllamaEmbeddings
        from langchain_postgres import PGVector

        self.embedding_model = OllamaEmbeddings(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
        )

        self.vector_store = PGVector(
            embeddings=self.embedding_model,
            collection_name=self.collection_name,
            connection=settings.db_url_sync,
            use_jsonb=True,
        )

    async def ingest_scheme(self, scheme_data: dict):
        if not self.vector_store:
            await self.initialize()

        text = f"{scheme_data['scheme_name']}: {scheme_data['description']} {scheme_data.get('benefits', '')}"
        metadata = {
            "scheme_name": scheme_data["scheme_name"],
            "state_jurisdiction": scheme_data.get("state_jurisdiction", "All India"),
            "category": scheme_data.get("category", ""),
            "ministry": scheme_data.get("ministry", ""),
            "scheme_id": str(scheme_data["id"]),
        }
        self.vector_store.add_texts([text], metadatas=[metadata])

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
