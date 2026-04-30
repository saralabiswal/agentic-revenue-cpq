import logging

from services.rag.embeddings import EmbeddingClient
from services.rag.vector_store import VectorStore


logger = logging.getLogger(__name__)


class Retriever:
    def __init__(
        self,
        embedding_client: EmbeddingClient | None = None,
        vector_store: VectorStore | None = None,
    ) -> None:
        self._embedding_client = embedding_client or EmbeddingClient()
        self._vector_store = vector_store or VectorStore()

    def retrieve(self, query: str, k: int = 3) -> list[str]:
        logger.info("Retriever started: query_length=%s k=%s", len(query), k)
        query_embedding = self._embedding_client.embed([query])[0]
        results = self._vector_store.query(query_embedding, n_results=k)
        logger.info("Retriever completed: result_count=%s", len(results))
        return results
