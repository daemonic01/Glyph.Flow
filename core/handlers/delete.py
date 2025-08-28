from typing import Optional, Tuple
from core.controllers.command_result import CommandResult
from core.node import Node

def delete_handler(ctx, *, id: Optional[str] = None) -> CommandResult:
    """
    Handler for the 'delete' command.

    Deletes a node by ID from the tree. Confirmation is assumed to be handled
    centrally by the Command system when `destructive=True`.

    Behavior:
        - If node not found → returns CommandResult(code="not_found").
        - If node is a root → removes from ctx.app.nodes and relabels roots.
        - If node is a child → removes from parent's children and relabels.

    Args:
        ctx: Application context (must provide ctx.app.nodes).
        id (str | None): ID of the node to delete.

    Returns:
        CommandResult:
            - code="not_found" with {"id"} params
            - code="deleted_root" with {"target_id", "target_name"}
            - code="deleted_child" with {"target_id", "target_name", "target_parent_id"}
    """

    target, parent = _find_node_and_parent(ctx, id)
    if not target:
        return CommandResult(code="not_found", params={"id": id}, outcome=False)

    name = getattr(target, "name", id)
    
    if parent is None:
        # remove from roots
        ctx.app.nodes = [r for r in ctx.app.nodes if r is not target]
        Node.relabel_roots(ctx.app.nodes)

        return CommandResult(
            code="deleted_root",
            params={"target_id": id, "target_name": name}, outcome=True
        )
    
    # remove from parent's children
    parent.children = [c for c in getattr(parent, "children", []) if c is not target]
    Node.relabel_children(target.parent)
    return CommandResult(
        code="deleted_child",
        params={"target_id": id, "target_name": name, "target_parent_id": parent.id}, outcome=True
    )




def _find_node_and_parent(ctx, target_id: str) -> Tuple[Optional[object], Optional[object]]:
    """
    Depth-first search for a node and its parent among ctx.nodes.

    Args:
        ctx: Application context (must contain ctx.nodes list).
        target_id (str): Node ID to search for.

    Returns:
        tuple(Node|None, Node|None):
            (target node, parent node) or (None, None) if not found.
    """
    if not target_id:
        return None, None

    for root in getattr(ctx, "nodes", []):
        if root.id == target_id:
            return root, None
        found, parent = _dfs_find_with_parent(root, target_id)
        if found:
            return found, parent

    return None, None


def _dfs_find_with_parent(node, target_id: str) -> Tuple[Optional[object], Optional[object]]:
    """
    Recursive DFS helper to locate a node and its parent.

    Args:
        node (Node): Current node in traversal.
        target_id (str): Node ID to search for.

    Returns:
        tuple(Node|None, Node|None): (found node, parent node) or (None, None).
    """
    for child in getattr(node, "children", []):
        if child.id == target_id:
            return child, node
        found, parent = _dfs_find_with_parent(child, target_id)
        if found:
            return found, parent
    return None, None
