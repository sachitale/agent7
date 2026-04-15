from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from vectorizer.embedders import get_embedder
from vectorizer.ingest import ingest
from vectorizer.store import VectorStore

console = Console()


@click.group()
def cli() -> None:
    """Embed code chunks and store them in ChromaDB."""


@cli.command()
@click.option("--input", "input_path", required=True, type=click.Path(exists=True, path_type=Path), help="JSONL file from the chunker.")
@click.option("--collection", default="code", show_default=True, help="ChromaDB collection name.")
@click.option("--db", "db_path", default="./chroma", show_default=True, type=click.Path(path_type=Path), help="ChromaDB persistence directory.")
@click.option("--provider", default="openai", show_default=True, type=click.Choice(["openai", "ollama"]), help="Embedding provider.")
@click.option("--model", default=None, help="Model name override (default: provider's default model).")
@click.option("--api-key", default=None, envvar="OPENAI_API_KEY", help="API key (openai provider). Falls back to OPENAI_API_KEY env var.")
@click.option("--ollama-url", default="http://localhost:11434", show_default=True, help="Ollama server base URL.")
@click.option("--batch-size", default=64, show_default=True, help="Chunks per embedding API call.")
def embed(
    input_path: Path,
    collection: str,
    db_path: Path,
    provider: str,
    model: str | None,
    api_key: str | None,
    ollama_url: str,
    batch_size: int,
) -> None:
    """Embed a chunks JSONL file and upsert into ChromaDB."""
    console.print(f"[bold]Provider:[/bold] {provider}  [bold]Model:[/bold] {model or '(default)'}")
    console.print(f"[bold]Input:[/bold] {input_path}  [bold]Collection:[/bold] {collection}  [bold]DB:[/bold] {db_path}\n")

    kwargs: dict = {"batch_size": batch_size}
    if provider == "openai" and api_key:
        kwargs["api_key"] = api_key
    if provider == "ollama":
        kwargs["base_url"] = ollama_url

    try:
        embedder = get_embedder(provider, model, **kwargs)
    except (ValueError, RuntimeError) as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    db_path.mkdir(parents=True, exist_ok=True)
    store = VectorStore(collection_name=collection, persist_dir=db_path)

    total = ingest(jsonl_path=input_path, embedder=embedder, store=store, batch_size=batch_size)

    console.print(f"\n[green]Done.[/green] Stored [bold]{total}[/bold] chunks in collection '[bold]{collection}[/bold]' → {db_path}")
    console.print(f"Total vectors in collection: [bold]{store.count()}[/bold]")


@cli.command()
@click.option("--query", required=True, help="Text to search for.")
@click.option("--collection", default="code", show_default=True, help="ChromaDB collection name.")
@click.option("--db", "db_path", default="./chroma", show_default=True, type=click.Path(exists=True, path_type=Path), help="ChromaDB persistence directory.")
@click.option("--provider", default="openai", show_default=True, type=click.Choice(["openai", "ollama"]))
@click.option("--model", default=None)
@click.option("--api-key", default=None, envvar="OPENAI_API_KEY")
@click.option("--ollama-url", default="http://localhost:11434", show_default=True)
@click.option("--top-k", default=5, show_default=True, help="Number of results to return.")
@click.option("--language", default=None, help="Filter results by language.")
def search(
    query: str,
    collection: str,
    db_path: Path,
    provider: str,
    model: str | None,
    api_key: str | None,
    ollama_url: str,
    top_k: int,
    language: str | None,
) -> None:
    """Search the vector store with a natural language or code query."""
    kwargs: dict = {}
    if provider == "openai" and api_key:
        kwargs["api_key"] = api_key
    if provider == "ollama":
        kwargs["base_url"] = ollama_url

    try:
        embedder = get_embedder(provider, model, **kwargs)
    except (ValueError, RuntimeError) as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    store = VectorStore(collection_name=collection, persist_dir=db_path)
    [query_vec] = embedder.embed([query])

    where = {"language": language} if language else None
    hits = store.query(query_vec, n_results=top_k, where=where)

    if not hits:
        console.print("[yellow]No results found.[/yellow]")
        return

    for i, hit in enumerate(hits, 1):
        meta = hit["metadata"]
        console.print(f"\n[bold cyan]#{i}[/bold cyan]  [bold]{meta.get('file_path')}[/bold]  "
                      f"lines {meta.get('start_line')}–{meta.get('end_line')}  "
                      f"[dim]{meta.get('language')} · {meta.get('chunk_type')} · {meta.get('name') or '—'}[/dim]  "
                      f"distance=[yellow]{hit['distance']:.4f}[/yellow]")
        console.print(hit["document"][:300] + ("…" if len(hit["document"]) > 300 else ""))
