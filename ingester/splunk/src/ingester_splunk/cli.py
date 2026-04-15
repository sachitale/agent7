from __future__ import annotations

import time
from pathlib import Path

import click
from rich.console import Console

from ingester_core.output import write_jsonl
from ingester_splunk.source import SplunkSource

console = Console()


@click.group()
def cli() -> None:
    """Ingest failure events from Splunk."""


def _shared_options(f):
    f = click.option("--host", required=True, help="Splunk host.")(f)
    f = click.option("--query", required=True, help="Splunk search query.")(f)
    f = click.option("--token", default=None, envvar="SPLUNK_TOKEN", help="Bearer token.")(f)
    f = click.option("--username", default=None, envvar="SPLUNK_USER")(f)
    f = click.option("--password", default=None, envvar="SPLUNK_PASSWORD")(f)
    f = click.option("--earliest", default="-1h", show_default=True)(f)
    f = click.option("--no-verify-ssl", is_flag=True, default=False)(f)
    f = click.option("--output", default="events.jsonl", show_default=True, type=click.Path(path_type=Path))(f)
    return f


@cli.command()
@_shared_options
def fetch(host, query, token, username, password, earliest, no_verify_ssl, output):
    """Fetch Splunk errors once and write to JSONL."""
    src = SplunkSource(host=host, query=query, token=token, username=username,
                       password=password, earliest=earliest, verify_ssl=not no_verify_ssl)
    console.print(f"[bold]Fetching from Splunk:[/bold] {host}")
    total = write_jsonl(src.fetch(), output)
    console.print(f"[green]Done.[/green] Wrote [bold]{total}[/bold] events → {output}")


@cli.command()
@_shared_options
@click.option("--interval", default=60, show_default=True, help="Poll interval in seconds.")
def watch(host, query, token, username, password, earliest, no_verify_ssl, output, interval):
    """Poll Splunk and append new events to JSONL."""
    console.print(f"[bold]Watching Splunk:[/bold] {host}  (interval: {interval}s)")
    try:
        while True:
            src = SplunkSource(host=host, query=query, token=token, username=username,
                               password=password, earliest=earliest, verify_ssl=not no_verify_ssl)
            total = write_jsonl(src.fetch(), output)
            console.print(f"[dim]tick[/dim]  +{total} events")
            time.sleep(interval)
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped.[/yellow]")
