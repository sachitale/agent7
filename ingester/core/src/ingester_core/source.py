from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator

from ingester_core.models import FailureEvent


class BaseSource(ABC):
    """Common interface for all error sources."""

    @abstractmethod
    def fetch(self) -> Iterator[FailureEvent]:
        """Yield FailureEvents from the source (one-shot)."""
        ...

    @property
    @abstractmethod
    def source_id(self) -> str:
        """Short identifier used in FailureEvent.source."""
        ...
