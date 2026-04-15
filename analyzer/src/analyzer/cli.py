from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from langchain_core.language_models import BaseChatModel
from rich.console import Console

console = Console()


@click.group()
def cli() -> None:
    """Analyze failure events using LangGraph + LLM reasoning over a vectorized codebase."""


@cli.command()
@click.option("--events", required=True, type=click.Path(exists=True, path_type=Path),
              help="JSONL file of FailureEvents from an ingester.")
@click.option("--db", "db_path", required=True, type=click.Path(exists=True, path_type=Path),
              help="ChromaDB directory from the vectorizer.")
@click.option("--collection", default="code", show_default=True,
              help="ChromaDB collection name.")
# LLM options
@click.option("--llm-provider", default="claude", show_default=True,
              type=click.Choice(["claude", "openai", "ollama"]),
              help="LLM provider for reasoning.")
@click.option("--llm-model", default=None,
              help="Model override (default: claude-sonnet-4-6 / gpt-4o / llama3).")
@click.option("--llm-api-key", default=None, envvar="LLM_API_KEY",
              help="API key. Falls back to ANTHROPIC_API_KEY or OPENAI_API_KEY env vars.")
@click.option("--ollama-url", default="http://localhost:11434", show_default=True)
# Embedding options (must match what was used to build the vector store)
@click.option("--embed-provider", default="openai", show_default=True,
              type=click.Choice(["openai", "ollama"]),
              help="Embedding provider (must match the vectorizer run).")
@click.option("--embed-model", default=None)
@click.option("--embed-api-key", default=None, envvar="OPENAI_API_KEY")
# Analysis options
@click.option("--top-k", default=5, show_default=True,
              help="Chunks to retrieve per query.")
@click.option("--max-iterations", default=3, show_default=True,
              help="Max retrieve→reason cycles per event.")
@click.option("--output", default="analysis.jsonl", show_default=True,
              type=click.Path(path_type=Path),
              help="Output JSONL file for analysis reports.")
def analyze(events, db_path, collection, llm_provider, llm_model, llm_api_key, ollama_url,
            embed_provider, embed_model, embed_api_key, top_k, max_iterations, output):
    """Analyze failure events and write root cause reports to JSONL."""
    from analyzer.graph import build_graph
    from analyzer.llm import get_llm
    from analyzer.output import print_report, write_jsonl

    # Import vectorizer components — they live in a sibling package
    try:
        from vectorizer.embedders import get_embedder
        from vectorizer.store import VectorStore
    except ImportError:
        console.print("[red]Error:[/red] vectorizer package not found. "
                      "Install it: uv pip install -e ../vectorizer")
        sys.exit(1)

    # Build LLM
    llm_kwargs = {}
    if llm_api_key:
        llm_kwargs["api_key"] = llm_api_key
    if llm_provider == "ollama":
        llm_kwargs["base_url"] = ollama_url
    try:
        llm: BaseChatModel = get_llm(llm_provider, llm_model, **llm_kwargs)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    # Build embedder
    embed_kwargs = {}
    if embed_api_key:
        embed_kwargs["api_key"] = embed_api_key
    if embed_provider == "ollama":
        embed_kwargs["base_url"] = ollama_url
    embedder = get_embedder(embed_provider, embed_model, **embed_kwargs)

    # Vector store
    store = VectorStore(collection_name=collection, persist_dir=db_path)

    # Build LangGraph
    graph = build_graph(llm=llm, embedder=embedder, store=store, top_k=top_k)

    # Read and process events
    with events.open(encoding="utf-8") as f:
        raw_events = [json.loads(line) for line in f if line.strip()]

    console.print(f"[bold]Analyzing {len(raw_events)} event(s)[/bold] "
                  f"using [cyan]{llm_provider}[/cyan] + [cyan]{embed_provider}[/cyan] embeddings\n")

    for i, event in enumerate(raw_events, 1):
        console.print(f"[bold]─── Event {i}/{len(raw_events)}[/bold] "
                      f"[dim]{event.get('event_id', '?')}[/dim]")

        initial_state: dict = {
            "event_id": event.get("event_id", ""),
            "source": event.get("source", ""),
            "message": event.get("message", ""),
            "stack_trace": event.get("stack_trace", ""),
            "service": event.get("service", ""),
            "language_hint": "",
            "search_queries": [],
            "retrieved_chunks": [],
            "hypothesis": "",
            "explanation": "",
            "confidence": "",
            "relevant_files": [],
            "chunks_used": [],
            "iterations": 0,
            "max_iterations": max_iterations,
            "_needs_more_context": False,
            "_refined_queries": [],
        }

        final_state = graph.invoke(initial_state)
        print_report(final_state)
        write_jsonl(final_state, output)

    console.print(f"\n[green]Done.[/green] Reports written to [bold]{output}[/bold]")
