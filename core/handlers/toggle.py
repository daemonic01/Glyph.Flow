from typing import Optional, Tuple, Iterable
from core.controllers.command_result import CommandResult

def toggle_handler(ctx, *, id: Optional[str] = None) -> CommandResult:
    """
    Toggle a node's completion state by ID (applies to the whole subtree).
    Returns codes:
      - "not_found"
      - "toggled"
    """

    node, _ = _find_node_and_parent(ctx, id)
    if not node:
        return CommandResult(code="not_found", params={"id": id})

    old_status = bool(getattr(node, "completed", False))
    new_status = not old_status
    _apply_completed_recursive(node, new_status)

    name = getattr(node, "name", id)
    return CommandResult(
        code="toggled",
        params={"target_name": name, "old_status": old_status, "new_status": new_status},
        payload={"id": id, "new_status": new_status},
    )


# --- helpers -----------------------------------------------------------------

def _find_node_and_parent(ctx, target_id: str) -> Tuple[Optional[object], Optional[object]]:
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
    for child in getattr(node, "children", []) or []:
        if getattr(child, "id", None) == target_id:
            return child, node
        found, parent = _dfs_find_with_parent(child, target_id)
        if found:
            return found, parent
    return None, None

def _apply_completed_recursive(node, value: bool) -> None:
    setattr(node, "completed", bool(value))
    for ch in getattr(node, "children", []) or []:
        _apply_completed_recursive(ch, value)
