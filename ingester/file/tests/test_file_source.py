import tempfile
from pathlib import Path

from ingester_file.source import FileSource


def _source(text: str) -> FileSource:
    p = Path(tempfile.mktemp(suffix=".log"))
    p.write_text(text)
    return FileSource(path=str(p))


def test_python_traceback():
    log = ("INFO starting\nTraceback (most recent call last):\n"
           '  File "app.py", line 42, in handle\n'
           "AttributeError: 'NoneType' object has no attribute 'query'\n")
    events = list(_source(log).fetch())
    assert len(events) >= 1
    assert any("Traceback" in e.stack_trace or "AttributeError" in e.stack_trace for e in events)


def test_java_exception():
    log = ("ERROR Payment failed\njava.lang.NullPointerException\n"
           "\tat com.example.PaymentService.process(PaymentService.java:55)\n")
    events = list(_source(log).fetch())
    assert len(events) >= 1
    assert any(e.severity in ("ERROR", "CRITICAL") for e in events)


def test_no_errors_produces_no_events():
    events = list(_source("INFO started\nINFO done\n").fetch())
    assert events == []


def test_severity_critical():
    events = list(_source("CRITICAL database lost\n  at pool.connect(pool.py:1)\n").fetch())
    assert events[0].severity == "CRITICAL"


def test_source_id():
    events = list(_source("ERROR boom\n").fetch())
    assert events[0].source == "file"


def test_multiple_errors():
    log = ("ERROR first\n  at foo(a.py:1)\nINFO ok\nERROR second\n  at bar(b.py:2)\n")
    events = list(_source(log).fetch())
    assert len(events) >= 2
