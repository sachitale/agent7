from __future__ import annotations

from typing import Any, TypedDict


class AnalysisState(TypedDict):
    # Input
    event_id: str
    source: str
    message: str
    stack_trace: str
    service: str
    language_hint: str          # detected language from stack trace (e.g. "python", "java")

    # Retrieval
    search_queries: list[str]   # queries sent to vector store
    retrieved_chunks: list[dict[str, Any]]  # raw chunk dicts from ChromaDB

    # Reasoning
    hypothesis: str             # current root cause hypothesis
    explanation: str            # detailed explanation
    confidence: str             # "high" | "medium" | "low"
    relevant_files: list[str]   # file paths implicated

    # Control
    iterations: int             # number of retrieve→reason cycles completed
    max_iterations: int         # limit to prevent infinite loops
    chunks_used: list[str]      # chunk_ids that contributed to final answer

    # Internal — set by reason node, consumed by conditional edge + refine node
    _needs_more_context: bool
    _refined_queries: list[str]
