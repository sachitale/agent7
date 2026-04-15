from __future__ import annotations

import re

from analyzer.state import AnalysisState

# Map stack trace patterns to language hints
_LANGUAGE_SIGNALS = [
    (re.compile(r'File ".*\.py", line \d+'), "python"),
    (re.compile(r'\tat [\w$.]+\([\w]+\.java:\d+\)'), "java"),
    (re.compile(r'\tat [\w$.]+\([\w]+\.kt:\d+\)'), "kotlin"),
    (re.compile(r'goroutine \d+|\.go:\d+'), "go"),
    (re.compile(r'at Object\.<anonymous>|\.js:\d+|\tat .*\.ts:\d+'), "typescript"),
    (re.compile(r'\.rb:\d+|in `'), "ruby"),
    (re.compile(r'\.rs:\d+|thread .* panicked'), "rust"),
]


def _detect_language(stack_trace: str) -> str:
    for pattern, lang in _LANGUAGE_SIGNALS:
        if pattern.search(stack_trace):
            return lang
    return ""


def _build_initial_queries(message: str, stack_trace: str, language: str) -> list[str]:
    """
    Build 1-3 search queries from the failure.
    - Query 1: the raw error message (most specific)
    - Query 2: key symbols extracted from the stack trace
    - Query 3: language-qualified generic query
    """
    queries = [message]

    # Extract class/function names from the stack trace
    symbols: list[str] = []
    if language == "python":
        symbols = re.findall(r'in (\w+)\n', stack_trace)
    elif language in ("java", "kotlin"):
        symbols = re.findall(r'at ([\w.$]+)\(', stack_trace)
        symbols = [s.split(".")[-2] for s in symbols if "." in s]  # class names
    elif language == "go":
        symbols = re.findall(r'(\w+)\(', stack_trace)
    elif language in ("javascript", "typescript"):
        symbols = re.findall(r'at (\w+)', stack_trace)

    if symbols:
        queries.append(" ".join(dict.fromkeys(symbols[:5])))  # unique, preserve order

    if language:
        queries.append(f"{language} {message}")

    return queries[:3]


def extract_node(state: AnalysisState) -> AnalysisState:
    """
    Node 1 — Extract language hint and build initial search queries from the failure event.
    """
    stack_trace = state["stack_trace"]
    message = state["message"]

    language = _detect_language(stack_trace)
    queries = _build_initial_queries(message, stack_trace, language)

    return {
        **state,
        "language_hint": language,
        "search_queries": queries,
        "iterations": 0,
        "retrieved_chunks": [],
        "hypothesis": "",
        "explanation": "",
        "confidence": "",
        "relevant_files": [],
        "chunks_used": [],
        "_needs_more_context": False,
        "_refined_queries": [],
    }
