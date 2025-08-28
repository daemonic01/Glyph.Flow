from typing import Any, Dict, List
from rich.table import Table

def render_search_results(ctx, matches: List[Dict[str, Any]]) -> None:
    """
    Render search results in a formatted Rich table and write to output widget.

    Columns:
        - ID (bold, width 12)
        - Name (white)
        - Type (cyan, width 10)
        - Ready (green, width 6; "[X]" if completed else "[ ]")
        - Deadline (white, width 12)

    Args:
        ctx: Application context (must provide ctx.app.output_widget).
        matches (list[dict[str, Any]]): List of match dicts, usually from
            search_handler._summarize(), containing:
              - id (str)
              - name (str)
              - type (str)
              - completed (bool)
              - deadline (str | None)

    Behavior:
        - Prints a header with the number of results.
        - Renders results as a Rich table.
        - Writes the output to ctx.app.output_widget.
    """
    table = Table(show_header=True, header_style="bold #9c1717", border_style="bold #9c1717")
    table.add_column("ID", style="bold white", width=12)
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
    ctx.app.output_widget.write(f"[bold white]\nSearch results ({len(matches)}):")
    ctx.app.output_widget.write(table)
