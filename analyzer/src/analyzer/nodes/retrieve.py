from __future__ import annotations

from typing import Any

from analyzer.state import AnalysisState


def make_retrieve_node(embedder, store, top_k: int = 5):
    """
    Factory — returns a retrieve node bound to the given embedder and vector store.

    embedder: any object with .embed(texts: list[str]) -> list[list[float]]
    store:    VectorStore instance from the vectorizer package
    top_k:    number of chunks to retrieve per query
    """

    def retrieve_node(state: AnalysisState) -> AnalysisState:
        """
        Node 2 — Embed each search query, query ChromaDB, deduplicate results.
        """
        queries = state["search_queries"]
        seen_ids: set[str] = {c["chunk_id"] for c in state.get("retrieved_chunks", [])}
        new_chunks: list[dict[str, Any]] = []

        for query in queries:
            [vec] = embedder.embed([query])
            hits = store.query(vec, n_results=top_k)
            for hit in hits:
                if hit["chunk_id"] not in seen_ids:
                    seen_ids.add(hit["chunk_id"])
                    new_chunks.append(hit)

        all_chunks = list(state.get("retrieved_chunks", [])) + new_chunks
        # Keep the top chunks by relevance (lowest distance first)
        all_chunks.sort(key=lambda c: c.get("distance", 1.0))

        return {**state, "retrieved_chunks": all_chunks[:top_k * 2]}

    return retrieve_node
