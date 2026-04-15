from analyzer.nodes.extract import extract_node, _detect_language, _build_initial_queries


def _base_state(**kwargs):
    return {
        "event_id": "abc123",
        "source": "file",
        "message": "NullPointerException",
        "stack_trace": "",
        "service": "api",
        "language_hint": "",
        "search_queries": [],
        "retrieved_chunks": [],
        "hypothesis": "",
        "explanation": "",
        "confidence": "",
        "relevant_files": [],
        "chunks_used": [],
        "iterations": 0,
        "max_iterations": 3,
        **kwargs,
    }


def test_detect_python():
    trace = 'File "app.py", line 42, in handle\nAttributeError: ...'
    assert _detect_language(trace) == "python"


def test_detect_java():
    trace = "\tat com.example.PaymentService.process(PaymentService.java:55)"
    assert _detect_language(trace) == "java"


def test_detect_go():
    trace = "goroutine 1 [running]:\nmain.handler()\n\t/app/main.go:42"
    assert _detect_language(trace) == "go"


def test_detect_unknown():
    assert _detect_language("something went wrong") == ""


def test_extract_sets_language_hint():
    state = _base_state(
        stack_trace='File "app.py", line 10, in run\nValueError: bad input'
    )
    result = extract_node(state)
    assert result["language_hint"] == "python"


def test_extract_builds_queries():
    state = _base_state(message="ValueError: bad input")
    result = extract_node(state)
    assert len(result["search_queries"]) >= 1
    assert result["search_queries"][0] == "ValueError: bad input"


def test_extract_resets_iterations():
    state = _base_state()
    result = extract_node(state)
    assert result["iterations"] == 0


def test_build_queries_max_three():
    queries = _build_initial_queries("error msg", "some stack trace", "python")
    assert len(queries) <= 3
