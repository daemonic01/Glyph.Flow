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