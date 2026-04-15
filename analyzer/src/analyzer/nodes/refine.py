from __future__ import annotations

from analyzer.state import AnalysisState


def refine_node(state: AnalysisState) -> AnalysisState:
    """
    Node 4 — Update search queries with the refined ones suggested by the LLM,
    then loop back to retrieve.
    """
    refined = state.get("_refined_queries", [])
    return {
        **state,
        "search_queries": refined if refined else state["search_queries"],
    }
