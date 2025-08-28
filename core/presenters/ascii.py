
from core.node import Node

def ascii_handler(ctx):
    """
    Handler for the 'ascii' command.

    Renders the current node tree as an ASCII diagram into the app's
    output widget. Each node is shown with its name, type, and ID.
    Root nodes are printed first, then children recursively.

    Args:
        ctx: Application context (must provide ctx.app.output_widget and ctx.nodes).
    """
    ctx.app.output_widget.write("[bold white]\nASCII Tree View:")
    for i, root in enumerate(ctx.nodes):
        ctx.app.output_widget.write(f"[#AE6D24]{root.name} ({root.type}, ID = {root.id})")

        # Recursively render children with ASCII branches
        for j, child in enumerate(root.children):
            is_last = (j == len(root.children) - 1)
            print_ascii_tree(ctx, child, "", is_last)


def print_ascii_tree(ctx, node: Node, prefix: str = "", is_last: bool = True, level: int = 1):
        """
    Render an ASCII branch view of the tree recursively.

    Example output:
        Root
        ├── Child A
        │   └── Subchild
        └── Child B

    Args:
        ctx: Application context (must provide ctx.app.output_widget).
        node (Node): The current node to render.
        prefix (str): Current indentation prefix (used for branches).
        is_last (bool): Whether this node is the last sibling in its level.
        level (int): Depth level in the tree (used for coloring).
    """
        connector = "└── " if is_last else "├── "

        if level == 0:
            color = "#92530A"
        elif level == 1:
            color = "#DB9B51"
        elif level == 2:
            color = "#FDC483"
        else:
            color = "#FFE1BF"

        # Render the current node line
        line = f"{prefix}{connector}[{color}]{node.name} ({node.type}, ID = {node.id})[/{color}]"
        ctx.app.output_widget.write(line)

        new_prefix = prefix + ("    " if is_last else "│   ")

        # Recurse into children
        for i, child in enumerate(node.children):
            is_last_child = (i == len(node.children) - 1)
            print_ascii_tree(ctx, child, new_prefix, is_last_child, level + 1)