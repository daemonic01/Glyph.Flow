from typing import Optional, Tuple, Iterable
from core.controllers.command_result import CommandResult
from core.controllers.undo_redo import Diff

def toggle_handler(ctx, *, id: Optional[str] = None) -> CommandResult:
    """
    Handler for the 'toggle' command.

    Toggles a node's `completed` status (True/False) by ID.
    The toggle is applied recursively to the entire subtree of that node.

    Behavior:
        - If node not found → returns code="not_found".
        - If node found → flips its completion status and updates all children.

    Args:
        ctx: Application context (must provide ctx.app.nodes).
        id (str | None): ID of the node to toggle.

    Returns:
        CommandResult:
            - code="not_found" with {"id"} if target not found.
            - code="toggled" with:
                params={"target_name", "old_status", "new_status"}
                payload={"id", "new_status"} if toggle succeeded.
    """

    node, _ = _find_node_and_parent(ctx, id)
    if not node:
        return CommandResult(code="not_found", params={"id": id}, outcome=False)

    old_status = bool(getattr(node, "completed", False))
    new_status = not old_status

    affected = _gather_subtree(node)
    forward_ops = []
    backward_ops = []

    for n in affected:
        before = bool(getattr(n, "completed", False))
        setattr(n, "completed", bool(new_status))
        forward_ops.append({"op": "toggle", "node_id": n.id, "field": "completed", "value": bool(new_status)})
        backward_ops.append({"op": "toggle", "node_id": n.id, "field": "completed", "value": before})

    name = getattr(node, "name", id)
    diff = Diff(forward=forward_ops, backward=backward_ops)
    ctx.app.refresh_data_info_box()

    return CommandResult(
        code="toggled",
        params={"target_name": name, "old_status": old_status, "new_status": new_status},
        payload={"id": id, "new_status": new_status, "diff": diff}, outcome=True
    )



def _find_node_and_parent(ctx, target_id: str) -> Tuple[Optional[object], Optional[object]]:
    """
    Depth-first search for a node and its parent among ctx.app.nodes.

    Args:
        ctx: Application context (must provide ctx.app.nodes).
        target_id (str): Node ID to search for.

    Returns:
        tuple(Node|None, Node|None):
            (target node, parent node) if found, otherwise (None, None).
    """
    """Depth-first search for node and its parent among roots in ctx.app.nodes."""
    if not target_id:
        return None, None
    for root in getattr(ctx.app, "nodes", []) or []:
        if getattr(root, "id", None) == target_id:
            return root, None
        found, parent = _dfs_find_with_parent(root, target_id)
        if found:
            return found, parent
    return None, None

def _dfs_find_with_parent(node, target_id: str) -> Tuple[Optional[object], Optional[object]]:
    """
    Recursive DFS helper to locate a node and its parent.

    Args:
        node (Node): Current node being traversed.
        target_id (str): Node ID to find.

    Returns:
        tuple(Node|None, Node|None): (found node, parent) or (None, None).
    """
    for child in getattr(node, "children", []) or []:
        if getattr(child, "id", None) == target_id:
            return child, node
        found, parent = _dfs_find_with_parent(child, target_id)
        if found:
            return found, parent
    return None, None

def _apply_completed_recursive(node, value: bool) -> None:
    """
    Recursively set the `completed` attribute of a node and all its children.

    Args:
        node (Node): The node to update.
        value (bool): New completion status.
    """
    setattr(node, "completed", bool(value))
    for ch in getattr(node, "children", []) or []:
        _apply_completed_recursive(ch, value)

def _gather_subtree(node) -> list:
    stack = [node]
    out = []
    while stack:
        cur = stack.pop()
        out.append(cur)
        stack.extend(getattr(cur, "children", []) or [])
    return out