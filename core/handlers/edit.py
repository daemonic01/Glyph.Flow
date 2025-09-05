from typing import Optional, Tuple, List, Dict
from core.controllers.command_result import CommandResult
from datetime import datetime

from core.controllers.undo_redo import Diff

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
          (payload contains a Diff for undo/redo)
        - If no changes applied → returns code="edit_no_change".
    """

    node, parent = _find_node_and_parent(ctx, id)
    if not node:
        return CommandResult(code="not_found", params={"id": id}, outcome=False)

    # Collect candidate field updates (param_name -> (attr_name, new_value))
    candidates: Dict[str, Tuple[str, Optional[str]]] = {
        "name": ("name", name),
        "short_desc": ("short_desc", short_desc),
        "full_desc": ("full_desc", full_desc),
        "deadline": ("deadline", deadline),
    }

    # Compute real changes
    applied_changes: List[str] = []
    forward_ops: List[dict] = []
    backward_ops: List[dict] = []


    for param_key, (attr_name, new_value) in candidates.items():
        if new_value is None:
            continue

        # datetime validation
        if attr_name == "deadline" and new_value is not None:
            if datetime.strptime(new_value, "%Y-%m-%d") <= datetime.today():
                return CommandResult(code="past_date_error", outcome=False)
            if parent and datetime.strptime(parent.deadline, "%Y-%m-%d") < datetime.strptime(new_value, "%Y-%m-%d"):
                return CommandResult(code="deadline_too_early", outcome=False)

        # short and full description length check
        if attr_name == "short_desc" and len(new_value) > ctx.config.get("node_properties.short_desc_length_limit", 100, int):
            return CommandResult(code="short_desc_too_long",
                                params = {"limit": ctx.config.get("node_properties.short_desc_length_limit", 100, int),
                                        "length": len(new_value)},
                                outcome=False)
        if attr_name == "full_desc" and len(new_value) > ctx.config.get("node_properties.full_desc_length_limit", 100, int):
            return CommandResult(code="full_desc_too_long",
                                params = {"limit": ctx.config.get("node_properties.full_desc_length_limit", 100, int),
                                        "length": len(new_value)},
                                outcome=False)



        before_value = getattr(node, attr_name, None)
        if before_value == new_value:
            continue  # no real change; skip

        # Apply the change
        setattr(node, attr_name, new_value)
        applied_changes.append(f"{attr_name} → '{new_value}'" if new_value is not None else f"{attr_name} → None")

        # Build diff actions (forward = redo, backward = undo)
        forward_ops.append({
            "op": "edit",
            "node_id": node.id,
            "field": attr_name,
            "value": new_value,
        })
        backward_ops.append({
            "op": "edit",
            "node_id": node.id,
            "field": attr_name,
            "value": before_value,
        })

    #
    if applied_changes:
        info = ", ".join(applied_changes)
        diff = Diff(forward=forward_ops, backward=backward_ops)
        return CommandResult(
            code="edit_done",
            params={"id": node.id, "info": info},
            outcome=True,
            payload={"diff": diff}
        )

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
