from typing import Tuple, Optional
from core.controllers.command_result import CommandResult
from core.node import Node
from core.controllers.undo_redo import Diff


def move_handler(ctx, *, id, target_parent_id):
    """
    Handle the 'move' command: relocate a node to a new parent in the tree.

    This operation removes a node from its current parent and appends it to
    the children of a new parent, if schema rules allow. It updates parent
    references, reindexes sibling labels, and produces a reversible diff
    for undo/redo support.

    Args:
        ctx (Context): Shared application context containing schema, nodes,
            config, and logging services.
        id (str): ID of the node to move.
        target_parent_id (str): ID of the target parent node to move under.

    Returns:
        CommandResult: Structured outcome of the move operation.
            - outcome=False with error codes if:
                * node not found ("node_not_found"),
                * node is root ("move_root_error"),
                * target parent not found ("target_parent_not_found"),
                * target parent is same as old parent ("already_there"),
                * schema rejects the new parent-child type ("type_error").
            - outcome=True with code "move_success" on success.
              The payload includes a Diff object with forward and backward
              operations for undo/redo.

    Side Effects:
        - Mutates the node tree structure.
        - Relabels children of both old and new parents.
    """
    node, old_parent = _find_node_and_parent(ctx, id)

    if not node:
        return CommandResult(code="node_not_found", params={"id": id}, outcome=False)
    if not old_parent:
        return CommandResult(code="move_root_error", params={"id": id}, outcome=False)

    new_parent, _ = _find_node_and_parent(ctx, target_parent_id)
    if not new_parent:
        return CommandResult(code="target_parent_not_found", params={"target_parent_id": target_parent_id}, outcome=False)

    if old_parent == new_parent:
        return CommandResult(code="already_there", params={"id": id, "target_parent_id": target_parent_id}, outcome=False)

    if not ctx.schema.is_valid_child(new_parent, node.type):
        return CommandResult(code="type_error", params={"id": id, "target_parent_id": target_parent_id}, outcome=False)

    # perform move (remove from old, append to new)
    old_index = old_parent.children.index(node)

    # remove from old without add_child side-effects
    del old_parent.children[old_index]

    # set new parent + append
    node.parent = new_parent
    new_parent.children.append(node)
    new_index = len(new_parent.children) - 1

    # relabel on both sides
    Node.relabel_children(old_parent)
    Node.relabel_children(new_parent)

    # build diff
    forward = [{
        "op": "move",
        "old_parent_id": old_parent.id,
        "old_index": old_index,
        "new_parent_id": new_parent.id,
        "new_index": new_index,
        "node_id": getattr(node, "id", None),
    }]
    backward = [{
        "op": "move",
        "old_parent_id": new_parent.id,
        "old_index": new_index,
        "new_parent_id": old_parent.id,
        "new_index": old_index,
        "node_id": getattr(node, "id", None),
    }]
    diff = Diff(forward=forward, backward=backward)

    return CommandResult(
        code="move_success",
        params={"id": id, "target_parent_id": target_parent_id},
        outcome=True,
        payload={"diff": diff}
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