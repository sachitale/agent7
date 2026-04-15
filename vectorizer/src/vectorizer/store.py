from __future__ import annotations

from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings


def _client(persist_dir: Path) -> chromadb.ClientAPI:
    return chromadb.PersistentClient(
        path=str(persist_dir),
        settings=Settings(anonymized_telemetry=False),
    )


class VectorStore:
    """Thin wrapper around a ChromaDB collection."""

    def __init__(self, collection_name: str, persist_dir: Path) -> None:
        self._client = _client(persist_dir)
        # get_or_create so re-runs are idempotent
        self._col = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        self._col.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def count(self) -> int:
        return self._col.count()

    def query(
        self,
        embedding: list[float],
        n_results: int = 10,
        where: dict | None = None,
    ) -> list[dict[str, Any]]:
        kwargs: dict[str, Any] = {"query_embeddings": [embedding], "n_results": n_results, "include": ["documents", "metadatas", "distances"]}
        if where:
            kwargs["where"] = where
        result = self._col.query(**kwargs)
        hits = []
        for i in range(len(result["ids"][0])):
            hits.append({
                "chunk_id": result["ids"][0][i],
                "document": result["documents"][0][i],
                "metadata": result["metadatas"][0][i],
                "distance": result["distances"][0][i],
            })
        return hits
