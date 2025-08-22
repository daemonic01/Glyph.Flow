from typing import Any, Dict, List
from rich.table import Table

def render_search_results(ctx, matches: List[Dict[str, Any]]) -> None:
    """Render search results as a Rich table."""
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID", style="bold", width=12)
    table.add_column("Name", style="white")
    table.add_column("Type", style="cyan", width=10)
    table.add_column("Ready", style="green", width=6)
    table.add_column("Deadline", style="white", width=12)

    for m in matches:
        ready = "[X]" if bool(m.get("completed", False)) else "[ ]"
        deadline = m.get("deadline") or "-"
        table.add_row(
            m.get("id", ""),
            m.get("name", ""),
            m.get("type", ""),
            ready,
            str(deadline),
        )

    ctx.app.log_widget.write(table)
