from typing import Optional
from core.controllers.command_result import CommandResult
from core.node import Node
from core.controllers.undo_redo import Diff, snapshot_node
from datetime import datetime


def create_handler(
    ctx,
    *,
    type: str = None,
    name: str = None,
    short_desc: Optional[str] = None,
    full_desc: Optional[str] = None,
    deadline: Optional[str] = None,
    parent_id: Optional[str] = None,
) -> CommandResult:
    """
    Handler for the 'create' command.

    Creates a new Node either at the root level or as a child of `parent_id`.

    Args:
        ctx: Application context (contains schema, nodes, log, etc.).
        type (str): Type of the node to create (e.g. "Project", "Phase", ...).
        name (str): Human-readable name of the node.
        short_desc (str | None): Optional short description.
        full_desc (str | None): Optional full description.
        deadline (str | None): Optional deadline (string, format depends on schema).
        parent_id (str | None): Optional ID of the parent node to attach under.

    Returns:
        CommandResult:
            - code="success" if node was created successfully.
            - code="parent_not_found_error" if parent_id does not exist.
            - code="tree_level_error" if parent cannot accept children.
            - code="root_type_error" if type is invalid at given level.
    """

    parent: Optional[Node] = None
    # find parent if parent_id was given
    if parent_id:
        parent = _find_node_by_id(ctx, parent_id)
        if not parent:
            return CommandResult(
                code="parent_not_found_error",
                params={"parent_id": parent_id},
                outcome=False
            )
    
    # schema validation
    expected = ctx.schema.get_expected_child_type(parent)
    if parent is not None and expected is None:
        return CommandResult(
            code="tree_level_error",
            params={"parent_id": parent.id, "parent_type": parent.type},
            outcome=False
        )
    
    
    if not ctx.schema.is_valid_child(parent, type):
        expected = ctx.schema.get_expected_child_type(parent)
        return CommandResult(
            code="root_type_error",
            params={
                "type": type,
                "parent_type": (parent.type if parent else "root"),
                "expected": expected,
            },
            outcome=False
        )

    # datetime validation
    if deadline:
        if datetime.strptime(deadline, "%Y-%m-%d") <= datetime.today():
            return CommandResult(code="past_date_error", outcome=False)
        if parent and parent.deadline and datetime.strptime(parent.deadline, "%Y-%m-%d") < datetime.strptime(deadline, "%Y-%m-%d"):
            return CommandResult(code="deadline_too_early", outcome=False)

    # short and full description length check
    if short_desc and len(short_desc) > ctx.config.get("node_properties.short_desc_length_limit", 100, int):
        return CommandResult(code="short_desc_too_long",
                             params = {"limit": ctx.config.get("node_properties.short_desc_length_limit", 100, int),
                                       "length": len(short_desc)},
                             outcome=False)
    if full_desc and len(full_desc) > ctx.config.get("node_properties.full_desc_length_limit", 300, int):
        return CommandResult(code="full_desc_too_long",
                             params = {"limit": ctx.config.get("node_properties.full_desc_length_limit", 300, int),
                                       "length": len(full_desc)},
                             outcome=False)

    # create node instance
    new_node = Node(
        type=type,
        name=name,
        short_desc=short_desc,
        full_desc=full_desc,
        deadline=deadline,
    )

    # make new root node or attach node to tree
    if parent:
        parent.add_child(new_node)
        real_index = parent.children.index(new_node)
    else:
        new_node.id = Node.next_free_root_id(ctx.nodes)
        ctx.nodes.append(new_node)
        real_index = ctx.nodes.index(new_node)

    snapshot = snapshot_node(new_node)
    forward = [{
        "op": "create",
        "snapshot": snapshot,
        "parent_id": getattr(parent, "id", None),
        "index": real_index,
    }]
    backward = [{
        "op": "delete",
        "node_id": new_node.id
    }]
    diff = Diff(forward=forward, backward=backward)

    return CommandResult(
        code="success",
        params={
            "type": type,
            "name": name,
            "id": new_node.id,
        },
        outcome=True,
        payload={"diff": diff}
    )




def _find_node_by_id(ctx, target_id: str) -> Optional[Node]:
    """
    Depth-first search in the current tree to locate a node by its ID.

    Args:
        ctx: Application context (must contain ctx.nodes list).
        target_id (str): Node ID to search for.

    Returns:
        Node | None: The found node, or None if not found.
    """
    if not target_id:
        return None
    for root in getattr(ctx, "nodes", []):
        found = _search_recursive(root, target_id)
        if found:
            return found
    return None


def _search_recursive(node: Node, target_id: str) -> Optional[Node]:
    """
    Recursive depth-first search helper.

    Args:
        node (Node): Current node in traversal.
        target_id (str): ID to search for.

    Returns:
        Node | None: The matching node, or None if not found.
    """
    if node.id == target_id:
        return node
    for child in getattr(node, "children", []):
        found = _search_recursive(child, target_id)
        if found:
            return found
    return None
