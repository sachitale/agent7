from __future__ import annotations

from pathlib import Path

from chunker.chunkers.base import BaseChunker
from chunker.models import Chunk


class SlidingWindowChunker(BaseChunker):
    def __init__(self, window_size: int = 60, overlap: int = 15) -> None:
        self.window_size = window_size
        self.overlap = overlap

    def chunk(self, path: Path, repo: str, file_path: str, language: str, version: str | None) -> list[Chunk]:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []

        lines = text.splitlines()
        if not lines:
            return []

        chunks: list[Chunk] = []
        step = max(1, self.window_size - self.overlap)
        i = 0
        while i < len(lines):
            end = min(i + self.window_size, len(lines))
            content = "\n".join(lines[i:end])
            chunks.append(Chunk(
                repo=repo,
                file_path=file_path,
                language=language,
                start_line=i + 1,
                end_line=end,
                content=content,
                chunk_type="window",
                name=None,
                version=version,
            ))
            if end == len(lines):
                break
            i += step

        return chunks
