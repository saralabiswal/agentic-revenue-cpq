"""Retriever facade that embeds queries and reads matching knowledge from the vector store.

Author: Sarala Biswal
"""

import logging

from services.rag.embeddings import EmbeddingClient
from services.rag.vector_store import VectorStore


logger = logging.getLogger(__name__)

# Retriever flow:
# - Embed the user's query with the same embedding model used for ingestion.
# - Search the vector store with that query vector.
# - Return raw knowledge snippets to the MCP tool/agent.


class Retriever:
    """Coordinates query embedding and vector search for RAG context retrieval."""

    def __init__(
        self,
        embedding_client: EmbeddingClient | None = None,
        vector_store: VectorStore | None = None,
    ) -> None:
        """Create a retriever with injectable embedding and vector-store clients."""
        self._embedding_client = embedding_client or EmbeddingClient()
        self._vector_store = vector_store or VectorStore()

    def retrieve(self, query: str, k: int = 3) -> list[str]:
        """Embed a query and return the top matching knowledge snippets."""
        logger.info("Retriever started: query_length=%s k=%s", len(query), k)
        # The embedding client returns a batch, so take the first vector for one query.
        query_embedding = self._embedding_client.embed([query])[0]
        results = self._vector_store.query(query_embedding, n_results=k)
        logger.info("Retriever completed: result_count=%s", len(results))
        return results
