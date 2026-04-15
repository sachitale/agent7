from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from ingester_core.output import write_jsonl
from ingester_file.source import FileSource

console = Console()


@click.group()
def cli() -> None:
    """Ingest failure events from a log file or stdin."""


@cli.command()
@click.option("--path", default=None, help="Log file path. Omit to read from stdin.")
@click.option("--output", default="events.jsonl", show_default=True, type=click.Path(path_type=Path))
def fetch(path: str | None, output: Path) -> None:
    """Parse a log file (or stdin) for errors and write to JSONL."""
    src = FileSource(path=path)
    source_label = path or "stdin"
    console.print(f"[bold]Reading from:[/bold] {source_label}")
    total = write_jsonl(src.fetch(), output)
    console.print(f"[green]Done.[/green] Wrote [bold]{total}[/bold] events → {output}")
