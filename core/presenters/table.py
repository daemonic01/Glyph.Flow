
from core.node import Node

def table_handler(ctx):
        """
        Handler for the 'table' command.

        Renders the entire node tree into a Rich Table and writes it into
        the app's output widget. Each node (root + children) is represented
        as a row with metadata.

        Args:
            ctx: Application context (must provide ctx.nodes and ctx.app.output_widget).
        """
        from rich.table import Table

        table = Table(show_header=True, header_style="bold #9c1717", border_style="bold #9c1717")
        table.add_column("ID", style="white", width=12)
        table.add_column("Name", style="white", no_wrap=True)
        table.add_column("Type", style="cyan", width=10)
        table.add_column("Created", style="white", width=12)
        table.add_column("Deadline", style="magenta", width=12)
        table.add_column("Ready", style="green", width=6)
        table.add_column("Short description", style="dim", max_width=30)
        table.add_column("Full description", style="dim", max_width=50)

        for root in ctx.nodes:
            _add_node_to_table(root, table)

        
        ctx.app.output_widget.write("[bold #9c1717]\nTable view:")
        ctx.app.output_widget.write(table)
        

def _add_node_to_table(node: Node, table):
    """
    Helper: Add a node (and all its descendants) as rows into the table.

    Args:
        node (Node): The node to add.
        table (rich.table.Table): The Rich table to populate.
    """
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