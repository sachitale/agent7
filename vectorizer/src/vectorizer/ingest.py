from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Generator

from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn, TimeElapsedColumn

from vectorizer.embedders.base import BaseEmbedder
from vectorizer.store import VectorStore

console = Console()

# Fields stored as ChromaDB metadata (everything except content which goes to document)
_META_FIELDS = ("repo", "file_path", "language", "start_line", "end_line", "chunk_type", "name")


def _read_chunks(jsonl_path: Path) -> Generator[dict[str, Any], None, None]:
    with jsonl_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def ingest(
    jsonl_path: Path,
    embedder: BaseEmbedder,
    store: VectorStore,
    batch_size: int = 64,
) -> int:
    """
    Read chunks from a JSONL file, embed them in batches, and upsert into the store.
    Returns the total number of chunks ingested.
    """
    chunks = list(_read_chunks(jsonl_path))
    if not chunks:
        console.print("[yellow]No chunks found in input file.[/yellow]")
        return 0

    total = 0

    with Progress(
        TextColumn("[bold green]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Embedding & storing", total=len(chunks))

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            texts = [c["content"] for c in batch]
            embeddings = embedder.embed(texts)

            ids = [c["chunk_id"] for c in batch]
            documents = texts
            metadatas = [
                {k: (c.get(k) or "") for k in _META_FIELDS}
                for c in batch
            ]

            store.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
            total += len(batch)
            progress.advance(task, len(batch))

    return total
