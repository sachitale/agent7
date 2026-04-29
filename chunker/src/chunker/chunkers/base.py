from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from chunker.models import Chunk


class BaseChunker(ABC):
    @abstractmethod
    def chunk(self, path: Path, repo: str, file_path: str, language: str, version: str | None) -> list[Chunk]:
        """Parse a file and return a list of Chunk objects."""
        ...
