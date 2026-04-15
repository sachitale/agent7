from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class FailureEvent:
    source: str           # "gcp" | "splunk" | "file"
    timestamp: str        # ISO 8601
    severity: str         # "ERROR" | "CRITICAL" | "WARNING" | "UNKNOWN"
    message: str          # short error message / first line
    stack_trace: str      # full stack trace or log block (may be empty)
    service: str          # service / app name (may be empty)
    raw: dict[str, Any]   # original payload from the source
    event_id: str = field(init=False)

    def __post_init__(self) -> None:
        raw = f"{self.source}:{self.timestamp}:{self.message}:{self.stack_trace}"
        self.event_id = hashlib.sha256(raw.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "source": self.source,
            "timestamp": self.timestamp,
            "severity": self.severity,
            "service": self.service,
            "message": self.message,
            "stack_trace": self.stack_trace,
            "raw": self.raw,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()
