
from core.node import Node

def tree_handler(ctx):
    ctx.app.log_widget.write("[bold cyan]Tree view:")
    for n in ctx.app.nodes:
        print_node_recursive(ctx=ctx, node=n)


def print_node_recursive(ctx, node: Node, indent: int = 0):
        """Print the tree view recursively in indented format with optional delay."""
        status = "[X]" if node.completed else "[ ]"

        if indent == 0:
            color = "#2B9995"
        elif indent == 1:
            color = "#2AA7A2"
        elif indent == 2:
            color = "#71DDD9"
        else:
            color = "#C9F0EF"
        
        line = f"[{color}]{status} {node.name} ({node.type}, ID = {node.id})[/{color}]"
        ctx.app.log_widget.write("  " * indent + line)
        for child in node.children:
            print_node_recursive(ctx, node = child, indent = indent + 1)