from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from ingester_core.models import FailureEvent


def write_jsonl(events: Iterator[FailureEvent], output_path: Path) -> int:
    """Write FailureEvents to a JSONL file (appended). Returns total events written."""
    total = 0
    with output_path.open("a", encoding="utf-8") as f:
        for event in events:
            f.write(event.to_json() + "\n")
            total += 1
    return total
