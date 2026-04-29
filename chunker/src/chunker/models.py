from __future__ import annotations

import hashlib
from dataclasses import dataclass, field


@dataclass
class Chunk:
    repo: str
    file_path: str
    language: str
    start_line: int
    end_line: int
    content: str
    chunk_type: str  # "function", "class", "method", "module", "window"
    name: str | None = field(default=None)
    version: str | None = field(default=None)
    chunk_id: str = field(init=False)

    def __post_init__(self) -> None:
        raw = f"{self.repo}:{self.file_path}:{self.start_line}:{self.content}"
        self.chunk_id = hashlib.sha256(raw.encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "repo": self.repo,
            "file_path": self.file_path,
            "language": self.language,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "chunk_type": self.chunk_type,
            "name": self.name,
            "version": self.version,
            "content": self.content,
        }
