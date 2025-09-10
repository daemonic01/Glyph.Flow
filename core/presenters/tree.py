
from core.node import Node

def tree_handler(ctx):
    """
    Handler for the 'tree' command.

    Renders the current node tree in a simple indented view, with
    checkboxes for completion state and color-coded levels.
    Example:

        [ ] Project A (Project, ID = 01)
          [X] Phase 1 (Phase, ID = 01.01)
            [ ] Task A (Task, ID = 01.01.01)

    Args:
        ctx: Application context (must provide ctx.app.output_widget and ctx.nodes).
    """
    ctx.app.output_widget.write("[bold white]\nTree view:")
    for n in ctx.app.nodes:
        print_node_recursive(ctx=ctx, node=n)

    if ctx.config.get("test_mode") == True:
        from core.controllers.command_result import CommandResult
        return CommandResult(code="success", outcome=True)


def print_node_recursive(ctx, node: Node, indent: int = 0):
    """
    Recursive helper to print a node and its children in an indented tree view.

    Args:
        ctx: Application context (must provide ctx.app.output_widget).
        node (Node): Current node to print.
        indent (int): Indentation level (0 for root).
    """
    status = "[X]" if node.completed else "[ ]"

    if indent == 0:
        color = "#92530A"
    elif indent == 1:
        color = "#DB9B51"
    elif indent == 2:
        color = "#FDC483"
    else:
        color = "#FFE1BF"
    
    line = f"[{color}]{status} {node.name} ({node.type}, ID = {node.id})[/{color}]"
    ctx.app.output_widget.write("  " * indent + line)
    for child in node.children:
        print_node_recursive(ctx, node = child, indent = indent + 1)