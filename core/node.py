from datetime import date
from typing import Optional, List


class Node:
    """
    A tree node representing a workflow entity (e.g., Project / Phase / Task / Subtask).

    ID scheme
    ---------
    * Root nodes use 2-digit numeric IDs: "01", "02", ...
    * Child nodes are dot-separated, 2-digit segments under their parent:
        "01.01", "01.02", "02.01.03", ...
    * IDs are assigned lazily on insert (via `add_child` for non-roots, or
      externally via `next_free_root_id` for roots).

    Invariants
    ----------
    * A parent must have a valid `id` before children are added (enforced in `add_child`).
    * `children` preserves insertion order; relabel helpers enforce sequential numbering.

    Notes
    -----
    * This model stores basic metadata (`created_at`, `deadline`, `*desc`, `completed`)
      but does not enforce schema constraints about allowed child types; that belongs
      to higher layers (e.g., `NodeSchema`).
    """

    def __init__(
        self,
        name: str,
        type: str = "item",
        parent: Optional["Node"] = None,
        deadline: str = "",
        short_desc: str = "",
        full_desc: str = "",
    ):
        """
        Create a new Node instance.

        Args:
            name: Human-readable label.
            type: Logical type, e.g. "Project" / "Phase" / "Task" / "Subtask".
            parent: Optional parent node reference (not required for roots).
            deadline: Optional ISO-ish date string; validation is up to the caller.
            short_desc: Optional short description.
            full_desc: Optional long description.
        """
        self.name = name
        self.type = type
        self.parent = parent
        self.children: List["Node"] = []

        self.created_at = date.today().isoformat()
        self.deadline = deadline
        self.short_desc = short_desc
        self.full_desc = full_desc
        self.completed = False


        self.id: Optional[str] = None



    @staticmethod
    def next_free_root_id(roots: List["Node"]) -> str:
        """
        Compute the next available root ID in 2-digit format ("01", "02", ...).

        Scans only root nodes (parent is None) and collects used numeric IDs.

        Args:
            roots: List of current root nodes.

        Returns:
            str: Next free 2-digit root id (gap-aware).
        """
        used = {
            int(r.id) for r in roots
            if r.parent is None and isinstance(r.id, str) and r.id.isdigit()
        }
        i = 1
        while i in used:
            i += 1
        return f"{i:02d}"



    @staticmethod
    def next_free_child_id(parent: "Node") -> str:
        """
        Compute the next available child ID under the given parent.

        The new ID appends a 2-digit segment to `parent.id`, respecting existing gaps.

        Args:
            parent: The parent node with a valid `id`.

        Returns:
            str: e.g. "01.03" (if the next free child index is 3).
        """
        used = set()
        for c in parent.children:
            try:
                used.add(int(str(c.id).split(".")[-1]))
            except Exception:
                pass
        i = 1
        while i in used:
            i += 1
        return f"{parent.id}.{i:02d}"



    def add_child(self, node: "Node"):
        """
        Attach `node` as a child and assign it a sequential child ID.

        Preconditions:
            * `self.id` must be a non-empty string (root or already-labeled node).

        Raises:
            ValueError: If the parent has no ID yet.
        """
        if not self.id:
            raise ValueError(
                f"Parent '{self.name}' has no ID yet. "
                "Assign a root ID before adding children."
            )
        node.parent = self
        node.id = Node.next_free_child_id(self)
        self.children.append(node)



    def toggle(self):
        """Invert the completion status of the current node."""
        self.completed = not self.completed



    def progress(self) -> int:
        """
        Calculate completion percentage for this node (0..100).

        Leaf rule:
            * If the node has no children → 100 if `completed` else 0.

        Composite rule:
            * Average of child progresses (integer floor via int()).

        Returns:
            int: Progress value from 0 to 100.
        """
        if not self.children:
            return 100 if self.completed else 0
        return int(sum(child.progress() for child in self.children) / len(self.children))



    def to_dict(self) -> dict:
        """
        Convert a node and its descendants into a JSON-serializable dict.

        Returns:
            dict: Serialized payload suitable for persistence.
        """
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
        """
        Reconstruct a Node (and its subtree) from a dictionary.

        Args:
            data: Serialized node data (as produced by `to_dict()`).
            parent: Optional parent for the reconstructed node.

        Returns:
            Node: The reconstructed Node instance (with children attached).
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



    @staticmethod
    def relabel_missing_ids(roots: List["Node"]) -> None:
        """
        Assign IDs to all roots/children that are missing IDs (gap-aware).

        Behavior:
            * Roots without a valid 2-digit numeric ID receive `next_free_root_id`.
            * Children are recursively checked; any child whose ID does not start
              with its parent's prefix gets a `next_free_child_id`.

        Raises:
            ValueError: If a parent's ID becomes invalid during relabel.
        """

        for r in roots:
            if not (isinstance(r.id, str) and r.id.isdigit()):
                r.id = Node.next_free_root_id(roots)

        def fix_children(p: "Node"):
            for c in p.children:
                if not (isinstance(p.id, str) and p.id):
                    raise ValueError("Parent lost ID during relabel.")
                if not (isinstance(c.id, str) and c.id.startswith(p.id + ".")):
                    c.id = Node.next_free_child_id(p)
                fix_children(c)
        for r in roots:
            fix_children(r)



    @staticmethod
    def _relabel_subtree(node: "Node") -> None:
        """
        Re-label **all descendants** of `node` to be sequential under each parent.

        Child indices start at 1 and are formatted as 2 digits, e.g. ".01", ".02".
        """

        for idx, child in enumerate(node.children, start=1):
            child.id = f"{node.id}.{idx:02d}"
            Node._relabel_subtree(child)



    @staticmethod
    def relabel_children(parent: "Node") -> None:
        """
        Re-label the direct children of `parent` as .01, .02, ... and fix subtrees.

        Useful after deletions or reordering to restore contiguous numbering.
        """
        Node._relabel_subtree(parent)



    @staticmethod
    def relabel_roots(roots: list["Node"]) -> None:
        """
        Re-label root level as 01, 02, ... and fix every subtree accordingly.

        Precondition:
            * All roots must currently have numeric IDs (coercible via int()).
              Use `relabel_missing_ids` first if this is not guaranteed.
        """

        roots.sort(key=lambda r: int(r.id))

        for idx, r in enumerate(roots, start=1):
            r.id = f"{idx:02d}"
            Node._relabel_subtree(r)