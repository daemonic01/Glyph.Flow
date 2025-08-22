
from core.node import Node

def table_handler(ctx):
        """Render a table view of all nodes in the tree using Rich Table."""
        from rich.table import Table

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("ID", style="bold", width=12)
        table.add_column("Name", style="white", no_wrap=True)
        table.add_column("Type", style="cyan", width=10)
        table.add_column("Created", style="white", width=12)
        table.add_column("Deadline", style="magenta", width=12)
        table.add_column("Ready", style="green", width=6)
        table.add_column("Short description", style="dim", max_width=30)
        table.add_column("Full description", style="dim", max_width=50)

        for root in ctx.nodes:
            _add_node_to_table(root, table)

        ctx.app.log_widget.write("[bold cyan]Table view:")
        ctx.app.log_widget.write(table)

def _add_node_to_table(node: Node, table):
    """Helper function to add nodes/rows to tables."""
    status = "[X]" if node.completed else "[ ]"
    table.add_row(
        node.id,
        node.name,
        node.type,
        node.created_at,
        node.deadline if node.deadline else "-",
        status,
        node.short_desc or "-",
        node.full_desc or "-"
    )
    for child in node.children:
        _add_node_to_table(child, table)