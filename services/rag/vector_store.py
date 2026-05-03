"""ChromaDB-backed vector store adapter for RAG documents.

Author: Sarala Biswal
"""

import logging
from pathlib import Path
from typing import Any

import chromadb


logger = logging.getLogger(__name__)

# Vector-store flow:
# - Ingestion upserts document ids, text, and embeddings.
# - Retrieval submits one query embedding.
# - ChromaDB returns the nearest document texts for the agent prompt.


class VectorStoreError(ValueError):
    """Raised when vector store inputs are invalid."""


class VectorStore:
    """ChromaDB adapter for storing and querying embedded knowledge documents."""

    def __init__(
        self,
        persist_directory: str | Path = "./chroma_db",
        collection_name: str = "knowledge",
        client: Any | None = None,
    ) -> None:
        """Open or create the configured persistent Chroma collection."""
        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name
        # Default path is ./chroma_db, which is ignored by git as runtime data.
        self._client = client or chromadb.PersistentClient(path=str(self.persist_directory))
        self._collection = self._client.get_or_create_collection(name=collection_name)

    def add_documents(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
    ) -> None:
        """Upsert documents and embeddings into the configured collection."""
        if not (len(ids) == len(documents) == len(embeddings)):
            # All three lists are parallel arrays; mismatched lengths would corrupt
            # the relationship between id, text, and embedding vector.
            logger.error(
                "Vector store add rejected: ids=%s documents=%s embeddings=%s",
                len(ids),
                len(documents),
                len(embeddings),
            )
            raise VectorStoreError("ids, documents, and embeddings must have the same length.")

        if not ids:
            # Empty ingestion is a no-op, which keeps setup scripts idempotent.
            logger.info("Vector store add skipped: document_count=0")
            return

        logger.info(
            "Vector store adding documents: collection=%s document_count=%s",
            self.collection_name,
            len(documents),
        )
        self._collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
        )

    def query(self, query_embedding: list[float], n_results: int = 3) -> list[str]:
        """Return the nearest stored documents for a query embedding."""
        if not query_embedding:
            # Chroma requires a vector; catching this early gives clearer errors.
            logger.error("Vector store query rejected: empty_embedding=true")
            raise VectorStoreError("query_embedding is required.")

        logger.info(
            "Vector store query started: collection=%s n_results=%s",
            self.collection_name,
            n_results,
        )
        result = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
        )
        # Chroma returns a nested list because it supports batches of query vectors.
        documents = result.get("documents") or [[]]
        retrieved_documents = list(documents[0])
        logger.info(
            "Vector store query completed: collection=%s result_count=%s",
            self.collection_name,
            len(retrieved_documents),
        )
        return retrieved_documents
