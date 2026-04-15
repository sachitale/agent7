from __future__ import annotations

import re
import sys
from collections.abc import Iterator
from pathlib import Path

from ingester_core.models import FailureEvent, utcnow
from ingester_core.source import BaseSource

_ERROR_PATTERNS = [
    re.compile(r"(ERROR|CRITICAL|FATAL|Exception|Traceback|Error:|FAILED|panic:)", re.IGNORECASE),
]

_FRAME_PATTERNS = [
    re.compile(r'^\s+at '),
    re.compile(r'^\s+File ".*", line \d+'),
    re.compile(r'^\s+goroutine \d+'),
    re.compile(r'^\s+\d+:'),
]

_SEVERITY_WORDS = {
    "CRITICAL": ["critical", "fatal", "panic"],
    "ERROR": ["error", "exception", "traceback", "failed"],
    "WARNING": ["warn", "warning"],
}


def _infer_severity(text: str) -> str:
    lower = text.lower()
    for severity, words in _SEVERITY_WORDS.items():
        if any(w in lower for w in words):
            return severity
    return "UNKNOWN"


def _is_frame_line(line: str) -> bool:
    return any(p.match(line) for p in _FRAME_PATTERNS)


def _is_error_line(line: str) -> bool:
    return any(p.search(line) for p in _ERROR_PATTERNS)


def _parse_blocks(lines: list[str]) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if _is_error_line(line):
            if current:
                blocks.append(current)
            current = [line]
        elif current and (_is_frame_line(line) or line.strip()):
            current.append(line)
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    return blocks


class FileSource(BaseSource):
    def __init__(self, path: str | None = None) -> None:
        self._path = path

    @property
    def source_id(self) -> str:
        return "file"

    def fetch(self) -> Iterator[FailureEvent]:
        text = Path(self._path).read_text(encoding="utf-8", errors="replace") if self._path else sys.stdin.read()
        for block in _parse_blocks(text.splitlines()):
            full_text = "\n".join(block)
            yield FailureEvent(
                source=self.source_id,
                timestamp=utcnow(),
                severity=_infer_severity(full_text),
                message=block[0].strip(),
                stack_trace=full_text,
                service="",
                raw={"path": self._path or "stdin"},
            )
