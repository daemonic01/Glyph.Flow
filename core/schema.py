from typing import List, Optional
from .node import Node
from .utils import get_level

class NodeSchema:
    def __init__(self, hierarchy: List[str]):
        self.hierarchy = hierarchy

    def get_expected_child_type(self, parent: Optional[Node]) -> Optional[str]:
        """Get the expected child type based on the schema and parent node level."""
        if parent is None:
            return self.hierarchy[0]
        level = get_level(parent)
        return self.hierarchy[level + 1] if level + 1 < len(self.hierarchy) else None

    def is_valid_child(self, parent: Optional[Node], child_type: str) -> bool:
        """Check if a child type is valid for the given parent node."""
        return self.get_expected_child_type(parent) == child_type
    
    def validate_tree_depth(self, node: Node) -> int:
        """Return the maximum depth of a given tree."""
        if not node.children:
            return 1
        return 1 + max(self.validate_tree_depth(child) for child in node.children)
    
    def relabel_tree_to_match(self, node: Node, level: int = 0):
        """Update node types throughout the tree to match the schema hierarchy."""
        if level < len(self.hierarchy):
            node.type = self.hierarchy[level]
        for child in node.children:
            self.relabel_tree_to_match(child, level + 1)
