from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from chunker.chunkers.ast_chunker import ASTChunker
from chunker.chunkers.sliding import SlidingWindowChunker
from chunker.output import write_jsonl
from chunker.repo import resolve_repo
from chunker.walker import EXTENSION_TO_LANGUAGE, walk

console = Console()


@click.group()
def cli() -> None:
    """Chunk a codebase into semantically meaningful pieces."""


@cli.command()
@click.option("--repo", required=True, help="Git repo URL or local directory path.")
@click.option("--output", default="chunks.jsonl", show_default=True, help="Output JSONL file.")
@click.option("--ref", default=None, help="Git tag, branch, or commit to index (remote repos). Auto-detected if omitted.")
@click.option("--language", "languages", multiple=True, help="Filter to specific language(s). Repeatable.")
@click.option("--window-size", default=60, show_default=True, help="Lines per sliding window chunk (generic files).")
@click.option("--overlap", default=15, show_default=True, help="Overlap lines for sliding window chunks.")
def chunk(repo: str, output: str, ref: str | None, languages: tuple[str, ...], window_size: int, overlap: int) -> None:
    """Walk a repo, chunk source files, and write to a JSONL file."""
    lang_filter = set(languages) if languages else None

    output_path = Path(output)

    console.print(f"[bold]Resolving repo:[/bold] {repo}")
    try:
        rd = resolve_repo(repo, ref)
    except (ValueError, RuntimeError) as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    if rd.version:
        console.print(f"[bold]Version:[/bold] {rd.version}")

    ast_chunker = ASTChunker(window_size=window_size, overlap=overlap)
    fallback_chunker = SlidingWindowChunker(window_size=window_size, overlap=overlap)

    supported_languages = set(EXTENSION_TO_LANGUAGE.values())

    files_seen = 0
    all_chunks = []

    try:
        with console.status("[bold green]Chunking files…"):
            for file_path, language in walk(rd.path, language_filter=lang_filter):
                relative = str(file_path.relative_to(rd.path))
                if language in supported_languages:
                    file_chunks = ast_chunker.chunk(file_path, rd.url, relative, language, rd.version)
                else:
                    file_chunks = fallback_chunker.chunk(file_path, rd.url, relative, language, rd.version)
                all_chunks.extend(file_chunks)
                files_seen += 1

        total, lang_counts = write_jsonl(all_chunks, output_path)
    finally:
        if rd.cleanup_fn:
            rd.cleanup_fn()

    console.print(f"\n[green]Done.[/green] Wrote [bold]{total}[/bold] chunks from [bold]{files_seen}[/bold] files → [bold]{output_path}[/bold]\n")

    table = Table(title="Chunks by language")
    table.add_column("Language", style="cyan")
    table.add_column("Chunks", justify="right")
    for lang, count in sorted(lang_counts.items(), key=lambda x: -x[1]):
        table.add_row(lang, str(count))
    console.print(table)
