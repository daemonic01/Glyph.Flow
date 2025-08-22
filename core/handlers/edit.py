from typing import Optional, Tuple
from core.controllers.command_result import CommandResult

def edit_handler(
    ctx,
    *,
    id: Optional[str] = None,
    name: Optional[str] = None,
    short_desc: Optional[str] = None,
    full_desc: Optional[str] = None,
    deadline: Optional[str] = None,
) -> CommandResult:
    """
    Edit a node's fields by ID.
    Returns codes:
      - "not_found"
      - "edit_done"
      - "edit_no_change"
    """

    node, _ = _find_node_and_parent(ctx, id)
    if not node:
        return CommandResult(code="not_found", params={"id": id})

    changes = []

    if name:
        node.name = name
        changes.append(f"name → '{name}'")
    if short_desc:
        node.short_desc = short_desc
        changes.append(f"short_desc → '{short_desc}'")
    if full_desc:
        node.full_desc = full_desc
        changes.append(f"full_desc → '{full_desc}'")
    if deadline:
        node.deadline = deadline
        changes.append(f"deadline → {deadline}")

    if changes:
        info = ", ".join(changes)
        return CommandResult(code="edit_done", params={"id": node.id, "info": info})

    return CommandResult(code="edit_no_change", params={"id": node.id})


# --- helpers -----------------------------------------------------------------

def _find_node_and_parent(ctx, target_id: str) -> Tuple[Optional[object], Optional[object]]:
    """Depth-first search for node and its parent among roots in ctx.app.nodes."""
    if not target_id:
        return None, None

    for root in getattr(ctx.app, "nodes", []):
        if getattr(root, "id", None) == target_id:
            return root, None
        found, parent = _dfs_find_with_parent(root, target_id)
        if found:
            return found, parent

    return None, None


def _dfs_find_with_parent(node, target_id: str) -> Tuple[Optional[object], Optional[object]]:
    for child in getattr(node, "children", []):
        if getattr(child, "id", None) == target_id:
            return child, node
        found, parent = _dfs_find_with_parent(child, target_id)
        if found:
            return found, parent
    return None, None
