from __future__ import annotations

import time
from pathlib import Path

import click
from rich.console import Console

from ingester_core.output import write_jsonl
from ingester_gcp.source import GCPSource

console = Console()


@click.group()
def cli() -> None:
    """Ingest failure events from GCP Cloud Logging."""


@cli.command()
@click.option("--project", required=True, help="GCP project ID.")
@click.option("--output", default="events.jsonl", show_default=True, type=click.Path(path_type=Path))
@click.option("--lookback", default=60, show_default=True, help="Minutes to look back.")
@click.option("--filter", "filter_extra", default="", help="Extra Cloud Logging filter expression.")
def fetch(project: str, output: Path, lookback: int, filter_extra: str) -> None:
    """Fetch GCP error logs once and write to JSONL."""
    src = GCPSource(project=project, lookback_minutes=lookback, filter_extra=filter_extra)
    console.print(f"[bold]Fetching from GCP project:[/bold] {project}")
    total = write_jsonl(src.fetch(), output)
    console.print(f"[green]Done.[/green] Wrote [bold]{total}[/bold] events → {output}")


@cli.command()
@click.option("--project", required=True)
@click.option("--output", default="events.jsonl", show_default=True, type=click.Path(path_type=Path))
@click.option("--lookback", default=60, show_default=True)
@click.option("--filter", "filter_extra", default="")
@click.option("--interval", default=60, show_default=True, help="Poll interval in seconds.")
def watch(project: str, output: Path, lookback: int, filter_extra: str, interval: int) -> None:
    """Poll GCP Cloud Logging and append new events to JSONL."""
    console.print(f"[bold]Watching GCP project:[/bold] {project}  (interval: {interval}s)")
    try:
        while True:
            src = GCPSource(project=project, lookback_minutes=lookback, filter_extra=filter_extra)
            total = write_jsonl(src.fetch(), output)
            console.print(f"[dim]tick[/dim]  +{total} events")
            time.sleep(interval)
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped.[/yellow]")
