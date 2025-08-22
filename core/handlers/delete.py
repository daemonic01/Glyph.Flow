from typing import Optional, Tuple
from core.controllers.command_result import CommandResult

def delete_handler(ctx, *, id: Optional[str] = None) -> CommandResult:
    """
    Delete a node by ID. Assumes confirm is handled centrally when 'destructive=True'.
    Returns:
      - not_found
      - deleted_root
      - deleted_child
    """

    target, parent = _find_node_and_parent(ctx, id)
    if not target:
        return CommandResult(code="not_found", params={"id": id})

    name = getattr(target, "name", id)
    
    if parent is None:
        # remove from roots
        ctx.app.nodes = [r for r in ctx.app.nodes if r is not target]

        return CommandResult(
            code="deleted_root",
            params={"target_id": id, "target_name": name},
        )
    
    # remove from parent's children
    parent.children = [c for c in getattr(parent, "children", []) if c is not target]
    return CommandResult(
        code="deleted_child",
        params={"target_id": id, "target_name": name, "target_parent_id": parent.id},
    )


# --- helpers -----------------------------------------------------------------

def _find_node_and_parent(ctx, target_id: str) -> Tuple[Optional[object], Optional[object]]:
    """Depth-first search for node and its parent among roots in ctx.nodes."""
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
    for child in getattr(node, "children", []):
        if child.id == target_id:
            return child, node
        found, parent = _dfs_find_with_parent(child, target_id)
        if found:
            return found, parent
    return None, None
