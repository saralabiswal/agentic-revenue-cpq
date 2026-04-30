import logging
from pathlib import Path
from typing import Any

import chromadb


logger = logging.getLogger(__name__)


class VectorStoreError(ValueError):
    """Raised when vector store inputs are invalid."""


class VectorStore:
    def __init__(
        self,
        persist_directory: str | Path = "./chroma_db",
        collection_name: str = "knowledge",
        client: Any | None = None,
    ) -> None:
        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name
        self._client = client or chromadb.PersistentClient(path=str(self.persist_directory))
        self._collection = self._client.get_or_create_collection(name=collection_name)

    def add_documents(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
    ) -> None:
        if not (len(ids) == len(documents) == len(embeddings)):
            logger.error(
                "Vector store add rejected: ids=%s documents=%s embeddings=%s",
                len(ids),
                len(documents),
                len(embeddings),
            )
            raise VectorStoreError("ids, documents, and embeddings must have the same length.")

        if not ids:
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
        if not query_embedding:
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
        documents = result.get("documents") or [[]]
        retrieved_documents = list(documents[0])
        logger.info(
            "Vector store query completed: collection=%s result_count=%s",
            self.collection_name,
            len(retrieved_documents),
        )
        return retrieved_documents
