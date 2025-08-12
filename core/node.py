from datetime import date
from typing import Optional, List


class Node:
    _root_counter = 1

    def __init__(
        self,
        name: str,
        type: str = "item",
        parent: Optional["Node"] = None,
        deadline: str = "",
        short_desc: str = "",
        full_desc: str = "",
    ):
        self.name = name
        self.type = type
        self.parent = parent
        self.children: List["Node"] = []

        self.created_at = date.today().isoformat()
        self.deadline = deadline
        self.short_desc = short_desc
        self.full_desc = full_desc
        self.completed = False


        if parent is None:
            self.id = f"{Node._root_counter:02d}"
            Node._root_counter += 1
        else:
            self.id = None


    def add_child(self, node: "Node"):
        """Attach a child node to the current node and assign it an ID.

        Args:
            node (Node): The Node instance to add as a child.
        """
        node.parent = self
        index = len(self.children) + 1
        prefix = self.id
        node.id = f"{prefix}.{index:02d}"
        self.children.append(node)


    def toggle(self):
        """Invert the completion status of the current node."""
        self.completed = not self.completed


    def progress(self) -> int:
        """Calculate completion percentage for this node.

        Returns:
            int: Progress value from 0 to 100.
        """
        if not self.children:
            return 100 if self.completed else 0
        return int(sum(child.progress() for child in self.children) / len(self.children))


    def to_dict(self) -> dict:
        """Convert this node and its descendants into a serializable dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "created_at": self.created_at,
            "deadline": self.deadline,
            "short_desc": self.short_desc,
            "full_desc": self.full_desc,
            "completed": self.completed,
            "children": [child.to_dict() for child in self.children]
        }


    @classmethod
    def from_dict(cls, data: dict, parent: Optional["Node"] = None) -> "Node":
        """Reconstruct a Node (and its children) from a dictionary.

        Args:
            data (dict): Serialized node data.
            parent (Optional[Node]): Parent node for the reconstructed node.

        Returns:
            Node: The reconstructed Node object.
        """
        node = cls(
            name=data["name"],
            type=data.get("type", "item"),
            deadline=data.get("deadline", ""),
            short_desc=data.get("short_desc", ""),
            full_desc=data.get("full_desc", ""),
            parent=parent
        )
        node.id = data["id"]
        node.completed = data.get("completed", False)
        node.created_at = data.get("created_at", date.today().isoformat())

        for child_data in data.get("children", []):
            child_node = cls.from_dict(child_data, parent=node)
            node.children.append(child_node)

        return node
