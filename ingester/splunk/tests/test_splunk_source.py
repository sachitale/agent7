import pytest
from unittest.mock import MagicMock, patch

from ingester_splunk.source import SplunkSource, _infer_severity


def test_infer_severity_error():
    assert _infer_severity("ERROR: something failed") == "ERROR"


def test_infer_severity_critical():
    assert _infer_severity("FATAL: system panic") == "CRITICAL"


def test_infer_severity_warning():
    assert _infer_severity("WARNING: disk almost full") == "WARNING"


def test_infer_severity_unknown():
    assert _infer_severity("INFO: all good") == "UNKNOWN"


def test_requires_auth():
    with pytest.raises(ValueError, match="token or username"):
        SplunkSource(host="splunk.example.com", query="index=prod")


def _mock_responses(results=None):
    if results is None:
        results = [{"_raw": "ERROR something broke", "_time": "2026-04-14T10:00:00", "host": "web-01"}]
    create = MagicMock()
    create.raise_for_status = MagicMock()
    create.json.return_value = {"sid": "job123"}
    status = MagicMock()
    status.raise_for_status = MagicMock()
    status.json.return_value = {"entry": [{"content": {"dispatchState": "DONE"}}]}
    result = MagicMock()
    result.raise_for_status = MagicMock()
    result.json.return_value = {"results": results}
    return create, status, result


def test_fetch_returns_events():
    create, status, result = _mock_responses()
    with patch("requests.post", return_value=create), patch("requests.get", side_effect=[status, result]):
        events = list(SplunkSource(host="splunk.example.com", query="index=prod", token="tok").fetch())
    assert len(events) == 1
    assert events[0].source == "splunk"
    assert events[0].severity == "ERROR"


def test_fetch_empty_results():
    create, status, result = _mock_responses(results=[])
    with patch("requests.post", return_value=create), patch("requests.get", side_effect=[status, result]):
        assert list(SplunkSource(host="h", query="q", token="t").fetch()) == []


def test_adds_search_prefix():
    create, status, result = _mock_responses()
    with patch("requests.post", return_value=create) as mock_post, \
         patch("requests.get", side_effect=[status, result]):
        list(SplunkSource(host="h", query="index=prod", token="t").fetch())
    assert mock_post.call_args.kwargs["data"]["search"].startswith("search ")
