from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from analyzer.nodes.extract import extract_node
from analyzer.nodes.reason import make_reason_node
from analyzer.nodes.refine import refine_node
from analyzer.nodes.retrieve import make_retrieve_node
from analyzer.state import AnalysisState


def _should_continue(state: AnalysisState) -> str:
    """
    Conditional edge after the reason node:
    - Loop back to refine → retrieve if the LLM asked for more context
      AND we haven't hit the iteration limit
    - Otherwise finish
    """
    needs_more = state.get("_needs_more_context", False)
    iterations = state.get("iterations", 0)
    max_iterations = state.get("max_iterations", 3)

    if needs_more and iterations < max_iterations:
        return "refine"
    return "end"


def build_graph(llm, embedder, store, top_k: int = 5) -> StateGraph:
    """
    Build and compile the analysis graph.

    Nodes:
        extract  → derive language hint + initial queries
        retrieve → embed queries, fetch chunks from ChromaDB
        reason   → LLM analyses failure + chunks, produces hypothesis
        refine   → update queries if LLM needs more context

    Edges:
        START → extract → retrieve → reason
        reason → (conditional) → refine → retrieve  (loop)
                               → END
    """
    retrieve_node = make_retrieve_node(embedder=embedder, store=store, top_k=top_k)
    reason_node = make_reason_node(llm=llm)

    graph = StateGraph(AnalysisState)

    graph.add_node("extract", extract_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("reason", reason_node)
    graph.add_node("refine", refine_node)

    graph.add_edge(START, "extract")
    graph.add_edge("extract", "retrieve")
    graph.add_edge("retrieve", "reason")
    graph.add_conditional_edges("reason", _should_continue, {"refine": "refine", "end": END})
    graph.add_edge("refine", "retrieve")

    return graph.compile()
