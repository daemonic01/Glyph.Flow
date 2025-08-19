from .node import Node

def get_level(node: Node) -> int:
    """Determine the depth level of the given node in the hierarchy.

    Args:
        node (Node): Node to evaluate.

    Returns:
        int: Level index, where 0 = root.
    """
    level = 0
    while node.parent is not None:
        node = node.parent
        level += 1
    return level


def toggle_all(node: Node):
    """Toggle the completion state of a node and certain descendants.

    Descendants are toggled only if they matched the node's original state,
    preserving intentional differences deeper in the hierarchy.
    """
    old_state = node.completed
    new_state = not old_state

    def _toggle_recursive(current: Node):
        if current.completed == old_state:
            current.completed = new_state
            for child in current.children:
                _toggle_recursive(child)

    _toggle_recursive(node)