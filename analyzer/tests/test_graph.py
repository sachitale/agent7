import json
from unittest.mock import MagicMock


def _make_llm_response(hypothesis="null pointer in PaymentService", confidence="high",
                       needs_more=False, refined_queries=None):
    payload = {
        "hypothesis": hypothesis,
        "explanation": "The charge object is null when card is declined.",
        "confidence": confidence,
        "relevant_files": ["src/PaymentService.java"],
        "chunks_used": ["chunk001"],
        "needs_more_context": needs_more,
        "refined_queries": refined_queries or [],
    }
    msg = MagicMock()
    msg.content = json.dumps(payload)
    return msg


def _make_embedder():
    embedder = MagicMock()
    embedder.embed.return_value = [[0.1] * 4]
    return embedder


def _make_store(hits=None):
    store = MagicMock()
    store.query.return_value = hits or [
        {"chunk_id": "chunk001", "document": "def process(charge): ...",
         "metadata": {"file_path": "src/PaymentService.java", "start_line": 10,
                      "end_line": 20, "language": "java", "chunk_type": "method", "name": "process"},
         "distance": 0.1}
    ]
    return store


def _base_state():
    return {
        "event_id": "evt001",
        "source": "gcp",
        "message": "NullPointerException in PaymentService",
        "stack_trace": "\tat com.example.PaymentService.process(PaymentService.java:55)",
        "service": "payment-api",
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
    }


def test_graph_produces_hypothesis():
    from analyzer.graph import build_graph

    llm = MagicMock()
    llm.invoke.return_value = _make_llm_response()

    graph = build_graph(llm=llm, embedder=_make_embedder(), store=_make_store())
    result = graph.invoke(_base_state())

    assert result["hypothesis"] == "null pointer in PaymentService"
    assert result["confidence"] == "high"
    assert result["iterations"] == 1


def test_graph_loops_when_needs_more_context():
    from analyzer.graph import build_graph

    llm = MagicMock()
    # First call: needs more context; second call: confident
    llm.invoke.side_effect = [
        _make_llm_response(confidence="low", needs_more=True, refined_queries=["PaymentService charge null"]),
        _make_llm_response(confidence="high"),
    ]

    graph = build_graph(llm=llm, embedder=_make_embedder(), store=_make_store())
    result = graph.invoke(_base_state())

    assert result["iterations"] == 2
    assert llm.invoke.call_count == 2


def test_graph_respects_max_iterations():
    from analyzer.graph import build_graph

    llm = MagicMock()
    # Always asks for more context
    llm.invoke.return_value = _make_llm_response(
        confidence="low", needs_more=True, refined_queries=["more context needed"]
    )

    state = {**_base_state(), "max_iterations": 2}
    graph = build_graph(llm=llm, embedder=_make_embedder(), store=_make_store())
    result = graph.invoke(state)

    assert result["iterations"] <= 2


def test_graph_detects_java_language():
    from analyzer.graph import build_graph

    llm = MagicMock()
    llm.invoke.return_value = _make_llm_response()

    graph = build_graph(llm=llm, embedder=_make_embedder(), store=_make_store())
    result = graph.invoke(_base_state())

    assert result["language_hint"] == "java"
