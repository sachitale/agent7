from __future__ import annotations

from abc import ABC, abstractmethod


class BaseEmbedder(ABC):
    """Common interface for all embedding backends."""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text."""
        ...

    @abstractmethod
    def dimensions(self) -> int:
        """Return the dimensionality of the embedding vectors."""
        ...

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Canonical model identifier used to tag stored vectors."""
        ...
