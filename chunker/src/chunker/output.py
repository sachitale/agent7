from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from chunker.models import Chunk


def write_jsonl(chunks: Iterable[Chunk], output_path: Path) -> tuple[int, dict[str, int]]:
    """
    Write chunks to a JSONL file.
    Returns (total_chunks, {language: count}).
    """
    total = 0
    lang_counts: dict[str, int] = defaultdict(int)

    with output_path.open("w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk.to_dict(), ensure_ascii=False) + "\n")
            total += 1
            lang_counts[chunk.language] += 1

    return total, dict(lang_counts)
