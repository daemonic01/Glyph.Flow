
from core.node import Node

def ascii_handler(ctx):
    ctx.app.log_widget.write("[bold cyan]ASCII Tree View:")
    for i, root in enumerate(ctx.nodes):
        ctx.app.log_widget.write(f"[#2B9995]{root.name} ({root.type}, ID = {root.id})")
        for j, child in enumerate(root.children):
            is_last = (j == len(root.children) - 1)
            print_ascii_tree(ctx, child, "", is_last)


def print_ascii_tree(ctx, node: Node, prefix: str = "", is_last: bool = True, level: int = 1):
        """Render an ASCII branch view of the tree recursively."""
        connector = "└── " if is_last else "├── "

        if level == 0:
            color = "#2B9995"
        elif level == 1:
            color = "#2AA7A2"
        elif level == 2:
            color = "#71DDD9"
        else:
            color = "#C9F0EF"

        line = f"{prefix}{connector}[{color}]{node.name} ({node.type}, ID = {node.id})[/{color}]"
        ctx.app.log_widget.write(line)

        new_prefix = prefix + ("    " if is_last else "│   ")
        for i, child in enumerate(node.children):
            is_last_child = (i == len(node.children) - 1)
            print_ascii_tree(ctx, child, new_prefix, is_last_child, level + 1)