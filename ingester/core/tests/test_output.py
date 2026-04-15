import json
import tempfile
from pathlib import Path

from ingester_core.models import FailureEvent
from ingester_core.output import write_jsonl


def _event(msg: str) -> FailureEvent:
    return FailureEvent(source="file", timestamp="2026-04-14T10:00:00+00:00",
                        severity="ERROR", message=msg, stack_trace=msg, service="svc", raw={})


def test_creates_file():
    out = Path(tempfile.mktemp(suffix=".jsonl"))
    assert write_jsonl(iter([_event("e1"), _event("e2")]), out) == 2
    assert out.exists()


def test_valid_json():
    out = Path(tempfile.mktemp(suffix=".jsonl"))
    write_jsonl(iter([_event("boom")]), out)
    obj = json.loads(out.read_text().strip())
    assert obj["message"] == "boom"
    assert "event_id" in obj


def test_appends():
    out = Path(tempfile.mktemp(suffix=".jsonl"))
    write_jsonl(iter([_event("first")]), out)
    write_jsonl(iter([_event("second")]), out)
    assert len(out.read_text().strip().splitlines()) == 2
