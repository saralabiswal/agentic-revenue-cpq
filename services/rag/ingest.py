"""Sample knowledge ingestion workflow for product, pricing, and playbook documents.

Author: Sarala Biswal
"""

import logging
from dataclasses import dataclass

from services.rag.embeddings import EmbeddingClient
from services.rag.vector_store import VectorStore


logger = logging.getLogger(__name__)

# RAG ingestion flow:
# - SAMPLE_DOCUMENTS are the demo knowledge base.
# - ingest_sample_documents() sends text to the embedding client.
# - Embeddings and original text are stored together in ChromaDB.
# - The search_knowledge MCP tool later retrieves these documents by meaning.


@dataclass(frozen=True)
class KnowledgeDocument:
    """Knowledge base document with a stable identifier and searchable content."""
    id: str
    text: str


SAMPLE_DOCUMENTS: tuple[KnowledgeDocument, ...] = (
    KnowledgeDocument(
        id="product-catalog-aff-a-series",
        text=(
            "Product catalog: NTAP-AFF-A-SERIES is the AFF A-Series Performance "
            "Storage package. Recommend it for telecom 5G edge, low-latency, "
            "mission-critical, and high-performance ONTAP workloads."
        ),
    ),
    KnowledgeDocument(
        id="product-catalog-asa-a-series",
        text=(
            "Product catalog: NTAP-ASA-A-SERIES is the ASA A-Series Block Storage "
            "package. Recommend it for billing databases, subscriber systems, "
            "VMware, SAN, and block-storage workloads."
        ),
    ),
    KnowledgeDocument(
        id="product-catalog-storagegrid",
        text=(
            "Product catalog: NTAP-STORAGEGRID is the StorageGRID Object Storage "
            "package. Recommend it for telemetry, logs, CDR retention, archive, "
            "object storage, and analytics data lake requirements."
        ),
    ),
    KnowledgeDocument(
        id="product-catalog-hybrid-cloud",
        text=(
            "Product catalog: NTAP-CVO is the Cloud Volumes ONTAP package. "
            "Recommend it for hybrid cloud disaster recovery, cloud migration, "
            "and ONTAP workload mobility."
        ),
    ),
    KnowledgeDocument(
        id="pricing-rules-telecom",
        text=(
            "Pricing rules: telecom modernization quotes receive a 10 percent "
            "discount for 36-month terms and a 5 percent bundle discount when "
            "three or more infrastructure platforms are selected."
        ),
    ),
    KnowledgeDocument(
        id="sales-playbook-telecom-review",
        text=(
            "Sales playbook: for telecom data infrastructure opportunities, prepare "
            "a recommendation first, show evidence and pricing to the sales rep, "
            "let the rep select products, and create a draft quote only after approval."
        ),
    ),
)


def ingest_sample_documents(
    embedding_client: EmbeddingClient | None = None,
    vector_store: VectorStore | None = None,
) -> int:
    """Embed and store sample product, pricing, and playbook documents."""
    # Dependency injection keeps tests fast and avoids requiring live Ollama/Chroma.
    client = embedding_client or EmbeddingClient()
    store = vector_store or VectorStore()
    # IDs must stay stable so repeated ingestion upserts the same logical documents.
    ids = [document.id for document in SAMPLE_DOCUMENTS]
    documents = [document.text for document in SAMPLE_DOCUMENTS]
    logger.info("Knowledge ingestion started: document_count=%s", len(documents))
    embeddings = client.embed(documents)
    store.add_documents(ids=ids, documents=documents, embeddings=embeddings)
    logger.info("Knowledge ingestion completed: document_count=%s", len(documents))
    return len(documents)


if __name__ == "__main__":
    # Manual local setup path: `uv run python -m services.rag.ingest`.
    count = ingest_sample_documents()
    print(f"Ingested {count} knowledge documents.")
