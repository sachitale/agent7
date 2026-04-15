from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timedelta, timezone

from ingester_core.models import FailureEvent, utcnow
from ingester_core.source import BaseSource

_FAILURE_SEVERITIES = {"ERROR", "CRITICAL", "ALERT", "EMERGENCY"}

_SEVERITY_MAP = {
    "ERROR": "ERROR",
    "CRITICAL": "CRITICAL",
    "ALERT": "CRITICAL",
    "EMERGENCY": "CRITICAL",
    "WARNING": "WARNING",
}


class GCPSource(BaseSource):
    def __init__(
        self,
        project: str,
        lookback_minutes: int = 60,
        filter_extra: str = "",
        page_size: int = 100,
    ) -> None:
        self._project = project
        self._lookback_minutes = lookback_minutes
        self._filter_extra = filter_extra
        self._page_size = page_size

    @property
    def source_id(self) -> str:
        return "gcp"

    def fetch(self) -> Iterator[FailureEvent]:
        from google.cloud import logging as gcp_logging

        client = gcp_logging.Client(project=self._project)
        since = (datetime.now(timezone.utc) - timedelta(minutes=self._lookback_minutes)).isoformat()
        severity_filter = " OR ".join(f'severity="{s}"' for s in _FAILURE_SEVERITIES)
        log_filter = f"({severity_filter}) AND timestamp >= \"{since}\""
        if self._filter_extra:
            log_filter += f" AND ({self._filter_extra})"

        for entry in client.list_entries(
            projects=[self._project],
            filter_=log_filter,
            page_size=self._page_size,
            order_by=gcp_logging.DESCENDING,
        ):
            yield self._to_event(entry)

    def _to_event(self, entry) -> FailureEvent:
        payload = entry.payload
        if isinstance(payload, dict):
            message = payload.get("message") or payload.get("textPayload") or str(payload)
            stack_trace = payload.get("stack_trace") or payload.get("stackTrace") or ""
        else:
            message = str(payload)
            stack_trace = ""

        message_first_line = message.splitlines()[0] if message else ""
        severity = _SEVERITY_MAP.get(str(entry.severity).upper(), "UNKNOWN")
        timestamp = entry.timestamp.isoformat() if entry.timestamp else utcnow()
        service = ""
        if entry.resource and entry.resource.labels:
            service = entry.resource.labels.get("service_name") or entry.resource.labels.get("module_id", "")

        return FailureEvent(
            source=self.source_id,
            timestamp=timestamp,
            severity=severity,
            message=message_first_line,
            stack_trace=stack_trace or message,
            service=service,
            raw={"log_name": entry.log_name, "payload": str(payload)},
        )
