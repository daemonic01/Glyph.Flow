from typing import Optional
from core.controllers.command_result import CommandResult
from core.node import Node


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
    """Create a node either as root or as a child under `parent_id`."""

    parent: Optional[Node] = None
    if parent_id:
        parent = _find_node_by_id(ctx, parent_id)
        if not parent:
            return CommandResult(
                code="parent_not_found_error",
                params={"parent_id": parent_id},
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
        )

    new_node = Node(
        type=type,
        name=name,
        short_desc=short_desc,
        full_desc=full_desc,
        deadline=deadline,
    )

    if parent:
        parent.add_child(new_node)
    else:
        ctx.nodes.append(new_node)
    return CommandResult(
        code="success",
        params={
            "type": type,
            "name": name,
            "id": new_node.id,
        },
    )




def _find_node_by_id(ctx, target_id: str) -> Optional[Node]:
    """Depth-first search in the current tree to locate a node by its ID."""
    if not target_id:
        return None
    for root in getattr(ctx, "nodes", []):
        found = _search_recursive(root, target_id)
        if found:
            return found
    return None


def _search_recursive(node: Node, target_id: str) -> Optional[Node]:
    if node.id == target_id:
        return node
    for child in getattr(node, "children", []):
        found = _search_recursive(child, target_id)
        if found:
            return found
    return None
