from __future__ import annotations

import time
from collections.abc import Iterator

import requests

from ingester_core.models import FailureEvent, utcnow
from ingester_core.source import BaseSource

_SEVERITY_KEYWORDS = {
    "CRITICAL": ["critical", "fatal", "panic"],
    "ERROR": ["error", "exception", "traceback", "fail"],
    "WARNING": ["warn", "warning"],
}


def _infer_severity(text: str) -> str:
    lower = text.lower()
    for severity, keywords in _SEVERITY_KEYWORDS.items():
        if any(k in lower for k in keywords):
            return severity
    return "UNKNOWN"


class SplunkSource(BaseSource):
    def __init__(
        self,
        host: str,
        query: str,
        token: str | None = None,
        username: str | None = None,
        password: str | None = None,
        port: int = 8089,
        earliest: str = "-1h",
        latest: str = "now",
        max_results: int = 100,
        verify_ssl: bool = True,
    ) -> None:
        self._base_url = f"https://{host}:{port}"
        self._query = query if query.strip().startswith("search") else f"search {query}"
        self._earliest = earliest
        self._latest = latest
        self._max_results = max_results
        self._verify_ssl = verify_ssl

        if token:
            self._auth = None
            self._headers = {"Authorization": f"Bearer {token}"}
        elif username and password:
            self._auth = (username, password)
            self._headers = {}
        else:
            raise ValueError("Splunk source requires either a token or username+password")

    @property
    def source_id(self) -> str:
        return "splunk"

    def fetch(self) -> Iterator[FailureEvent]:
        resp = requests.post(
            f"{self._base_url}/services/search/jobs",
            data={"search": self._query, "earliest_time": self._earliest,
                  "latest_time": self._latest, "output_mode": "json"},
            auth=self._auth, headers=self._headers,
            verify=self._verify_ssl, timeout=30,
        )
        resp.raise_for_status()
        sid = resp.json()["sid"]

        status_url = f"{self._base_url}/services/search/jobs/{sid}"
        while True:
            status = requests.get(status_url, params={"output_mode": "json"},
                                  auth=self._auth, headers=self._headers,
                                  verify=self._verify_ssl, timeout=15)
            status.raise_for_status()
            state = status.json()["entry"][0]["content"]["dispatchState"]
            if state == "DONE":
                break
            if state in ("FAILED", "KILLED"):
                raise RuntimeError(f"Splunk search job failed with state: {state}")
            time.sleep(1)

        results = requests.get(
            f"{self._base_url}/services/search/jobs/{sid}/results",
            params={"output_mode": "json", "count": self._max_results},
            auth=self._auth, headers=self._headers,
            verify=self._verify_ssl, timeout=30,
        )
        results.raise_for_status()
        for result in results.json().get("results", []):
            yield self._to_event(result)

    def _to_event(self, result: dict) -> FailureEvent:
        raw_text = result.get("_raw", "")
        message = raw_text.splitlines()[0] if raw_text else str(result)
        return FailureEvent(
            source=self.source_id,
            timestamp=result.get("_time") or utcnow(),
            severity=_infer_severity(raw_text),
            message=message,
            stack_trace=raw_text,
            service=result.get("source") or result.get("host") or "",
            raw=result,
        )
