"""Provider-neutral embedding client interface.

Author: Sarala Biswal
"""

from typing import Protocol


class EmbeddingClient(Protocol):
    """Interface for text embedding providers."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate one embedding vector for each supplied text."""
