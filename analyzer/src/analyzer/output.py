from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from analyzer.state import AnalysisState

console = Console()

_CONFIDENCE_COLORS = {"high": "green", "medium": "yellow", "low": "red"}


def write_jsonl(state: AnalysisState, output_path: Path) -> None:
    record = {
        "event_id": state["event_id"],
        "source": state["source"],
        "service": state["service"],
        "root_cause": state["hypothesis"],
        "confidence": state["confidence"],
        "explanation": state["explanation"],
        "relevant_files": state["relevant_files"],
        "chunks_used": state["chunks_used"],
        "iterations": state["iterations"],
    }
    with output_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def print_report(state: AnalysisState) -> None:
    confidence = state["confidence"]
    color = _CONFIDENCE_COLORS.get(confidence, "white")

    title = Text()
    title.append("Root Cause Analysis  ", style="bold")
    title.append(f"[{confidence.upper()}]", style=f"bold {color}")

    console.print()
    console.print(Panel(title, expand=False))

    console.print(f"[bold]Event:[/bold]   {state['event_id']}")
    console.print(f"[bold]Service:[/bold] {state['service'] or '—'}")
    console.print(f"[bold]Source:[/bold]  {state['source']}")
    console.print()

    console.print(Panel(
        f"[bold]{state['hypothesis']}[/bold]",
        title="Hypothesis",
        border_style=color,
    ))
    console.print()
    console.print(Panel(state["explanation"], title="Explanation", border_style="dim"))

    if state["relevant_files"]:
        console.print()
        table = Table(title="Relevant Files")
        table.add_column("File", style="cyan")
        for f in state["relevant_files"]:
            table.add_row(f)
        console.print(table)

    console.print(f"\n[dim]Iterations: {state['iterations']} | "
                  f"Chunks used: {len(state['chunks_used'])}[/dim]")
