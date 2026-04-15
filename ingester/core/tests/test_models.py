import json

from ingester_core.models import FailureEvent


def _make_event(**kwargs) -> FailureEvent:
    defaults = dict(
        source="file",
        timestamp="2026-04-14T10:00:00+00:00",
        severity="ERROR",
        message="NullPointerException",
        stack_trace="NullPointerException\n  at Foo.bar(Foo.java:10)",
        service="payment-api",
        raw={},
    )
    defaults.update(kwargs)
    return FailureEvent(**defaults)


def test_event_id_is_generated():
    e = _make_event()
    assert e.event_id and len(e.event_id) == 16


def test_event_id_is_deterministic():
    assert _make_event().event_id == _make_event().event_id


def test_event_id_differs_on_different_content():
    assert _make_event(message="Error A").event_id != _make_event(message="Error B").event_id


def test_to_dict_has_all_fields():
    d = _make_event().to_dict()
    for f in ("event_id", "source", "timestamp", "severity", "service", "message", "stack_trace", "raw"):
        assert f in d


def test_to_json_is_valid():
    obj = json.loads(_make_event().to_json())
    assert obj["message"] == "NullPointerException"
