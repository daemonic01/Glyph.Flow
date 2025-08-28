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
    Handler for the 'edit' command.

    Updates fields of a node identified by ID. Any combination of fields
    can be updated in a single call. If no new values are provided, no
    changes are made.

    Behavior:
        - If node not found → returns code="not_found".
        - If one or more fields updated → returns code="edit_done".
        - If no changes applied → returns code="edit_no_change".

    Args:
        ctx: Application context (must contain ctx.nodes).
        id (str | None): ID of the node to edit.
        name (str | None): New name for the node.
        short_desc (str | None): New short description.
        full_desc (str | None): New full description.
        deadline (str | None): New deadline string.

    Returns:
        CommandResult: outcome of the edit operation with appropriate code and params.
    """

    node, _ = _find_node_and_parent(ctx, id)
    if not node:
        return CommandResult(code="not_found", params={"id": id}, outcome=False)

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
        return CommandResult(code="edit_done", params={"id": node.id, "info": info}, outcome=True)

    return CommandResult(code="edit_no_change", params={"id": node.id}, outcome=False)




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

    for root in getattr(ctx.app, "nodes", []):
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
        node (Node): Current node in traversal.
        target_id (str): Node ID to search for.

    Returns:
        tuple(Node|None, Node|None): (found node, parent node) or (None, None).
    """
    for child in getattr(node, "children", []):
        if getattr(child, "id", None) == target_id:
            return child, node
        found, parent = _dfs_find_with_parent(child, target_id)
        if found:
            return found, parent
    return None, None
