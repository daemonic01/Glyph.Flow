from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from core.node import Node

@dataclass
class Diff:
    """
    Represents a reversible change in the node tree.

    A Diff contains two sets of low-level operations:
      - forward: actions to reapply the change (redo).
      - backward: actions to revert the change (undo).

    Each action is stored as a dict with an "op" field
    (e.g. "create", "delete", "edit", "toggle", "move")
    and additional metadata required to replay it.

    Attributes:
        forward (list[dict]): List of actions for redo.
        backward (list[dict]): List of actions for undo.
    """
    forward: List[Dict[str, Any]]
    backward: List[Dict[str, Any]]



def snapshot_node(node: Node) -> Dict[str, Any]:
    """
    Create a deep snapshot of a node and its subtree.

    The snapshot captures structural and descriptive
    attributes of the node, plus recursively includes
    snapshots of all children. This enables undo/redo
    and persistence by reconstructing nodes later.

    Args:
        node (Node): Node to snapshot.

    Returns:
        dict: Serialized representation containing:
              - id, type, name, short_desc, full_desc, deadline
              - children: list of child snapshots
    """
    return {
        "id": node.id,
        "type": node.type,
        "name": node.name,
        "short_desc": node.short_desc,
        "full_desc": node.full_desc,
        "deadline": node.deadline,
        "children": [snapshot_node(ch) for ch in getattr(node, "children", [])],
    }



def node_from_snapshot(snap: Dict[str, Any]) -> Node:
    """
    Reconstruct a Node tree from a snapshot.

    Creates a new Node instance with the same attributes
    as stored in the snapshot, recursively restoring
    all children and reassigning parent references.

    Args:
        snap (dict): Snapshot dict (as produced by snapshot_node).

    Returns:
        Node: Fully reconstructed Node tree with correct IDs,
              fields, children, and parent links.
    """
    n = Node(
        type=snap.get("type"),
        name=snap.get("name"),
        short_desc=snap.get("short_desc"),
        full_desc=snap.get("full_desc"),
        deadline=snap.get("deadline"),
    )
    n.id = snap.get("id")
    for ch_snap in snap.get("children", []):
        child = node_from_snapshot(ch_snap)
        child.parent = n
        n.children.append(child)
    return n



class UndoRedoManager:
    """
    Manage undo and redo stacks for tree-editing commands.

    Provides a bounded history of Diffs (max_size) and
    supports recording, undoing, and redoing changes.

    Attributes:
        undo_stack (list[Diff]): Stack of past changes.
        redo_stack (list[Diff]): Stack of undone changes.
        max_size (int): Maximum history size (oldest diffs dropped).

    Methods:
        record(diff): Add a new Diff and clear redo history.
        can_undo(): Whether there is at least one Diff to undo.
        can_redo(): Whether there is at least one Diff to redo.
        undo(ctx): Apply the backward part of the latest Diff.
        redo(ctx): Apply the forward part of the latest Diff.
    """
    def __init__(self, max_size: int = 50) -> None:
        self.undo_stack: List[Diff] = []
        self.redo_stack: List[Diff] = []
        self.max_size = max_size



    def record(self, diff: Diff) -> None:
        self.undo_stack.append(diff)
        self.redo_stack.clear()
        if len(self.undo_stack) > self.max_size:
            self.undo_stack.pop(0)



    def can_undo(self) -> bool:
        return bool(self.undo_stack)



    def can_redo(self) -> bool:
        return bool(self.redo_stack)



    def undo(self, ctx) -> bool:
        if not self.undo_stack:
            return False
        diff = self.undo_stack.pop()
        self._apply(ctx, diff.backward)
        self.redo_stack.append(diff)
        return True



    def redo(self, ctx) -> bool:
        if not self.redo_stack:
            return False
        diff = self.redo_stack.pop()
        self._apply(ctx, diff.forward)
        self.undo_stack.append(diff)
        return True



    def _apply(self, ctx, actions: List[Dict[str, Any]]) -> None:
        for act in actions:
            op = act.get("op")
            if op == "edit":
                node = _find_node(ctx, act["node_id"])
                if node is not None:
                    setattr(node, act["field"], act["value"])

            elif op == "toggle":
                node = _find_node(ctx, act["node_id"])
                if node is not None:
                    setattr(node, act["field"], bool(act["value"]))

            elif op == "create":
                snap = act["snapshot"]
                parent_id = act.get("parent_id")
                index = act.get("index")
                new_node = node_from_snapshot(snap)
                if parent_id:
                    parent = _find_node(ctx, parent_id)
                    if parent is None:
                        continue
                    new_node.parent = parent
                    if index is None or index > len(parent.children):
                        parent.children.append(new_node)
                    else:
                        parent.children.insert(index, new_node)
                else:
                    new_node.parent = None
                    roots = ctx.app.nodes
                    if index is None or index > len(roots):
                        roots.append(new_node)
                    else:
                        roots.insert(index, new_node)

            elif op == "delete":
                _remove_node_by_id(ctx, act["node_id"])

            elif op == "move":
                # resolve parents
                old_parent = _find_node(ctx, act.get("old_parent_id")) if act.get("old_parent_id") else None
                new_parent = _find_node(ctx, act.get("new_parent_id")) if act.get("new_parent_id") else None
                if old_parent is None or new_parent is None:
                    ctx.log.warn(f"move: parent missing old={act.get('old_parent_id')} new={act.get('new_parent_id')}")
                    continue

                old_index = act.get("old_index")
                new_index = act.get("new_index")

                # try to pick the node by the stored old_index
                node = None
                if isinstance(old_index, int) and 0 <= old_index < len(old_parent.children):
                    node = old_parent.children[old_index]

                # fallback: find by node_id if given (best-effort)
                if node is None and act.get("node_id"):
                    node = _find_node(ctx, act["node_id"])

                if node is None:
                    ctx.log.warn("move: node not found at old_index and by node_id; skipping")
                    continue

                # remove from old_parent (by identity)
                removed = False
                if isinstance(old_index, int) and 0 <= old_index < len(old_parent.children) and old_parent.children[old_index] is node:
                    del old_parent.children[old_index]
                    removed = True
                else:
                    # identity-based removal
                    for i, ch in enumerate(old_parent.children):
                        if ch is node:
                            del old_parent.children[i]
                            removed = True
                            break
                if not removed:
                    ctx.log.warn("move: could not remove node from old_parent; skipping")
                    continue


                node.parent = new_parent
                if isinstance(new_index, int) and 0 <= new_index <= len(new_parent.children):
                    new_parent.children.insert(new_index, node)
                else:
                    new_parent.children.append(node)

                Node.relabel_children(old_parent)
                Node.relabel_children(new_parent)



def _find_node(ctx, target_id: str) -> Optional[Node]:
    """
    Locate a node by ID in the entire tree.

    Args:
        ctx (Context): Application context containing the root nodes.
        target_id (str): ID to search for.

    Returns:
        Node | None: Matching node, or None if not found.
    """
    if not target_id:
        return None
    for root in getattr(ctx.app, "nodes", []):
        if getattr(root, "id", None) == target_id:
            return root
        found = _dfs(root, target_id)
        if found:
            return found
    return None



def _dfs(node: Node, target_id: str) -> Optional[Node]:
    """
    Depth-first search for a node with the given ID.

    Args:
        node (Node): Current subtree root.
        target_id (str): ID to search for.

    Returns:
        Node | None: Found node or None if not found.
    """
    for child in getattr(node, "children", []):
        if getattr(child, "id", None) == target_id:
            return child
        found = _dfs(child, target_id)
        if found:
            return found
    return None



def _remove_node_by_id(ctx, target_id: str) -> None:
    """
    Remove a node from the tree by its ID.

    Finds the node and its parent, then deletes it
    from the parent's children or from the root list.

    Args:
        ctx (Context): Application context containing the tree.
        target_id (str): ID of node to remove.
    """
    parent, idx = _find_parent_and_index(ctx, target_id)
    if idx is None:
        return
    if parent is None:
        del ctx.app.nodes[idx]
    else:
        del parent.children[idx]



def _find_parent_and_index(ctx, target_id: str) -> tuple[Optional[Node], Optional[int]]:
    """
    Find the parent node and child index for a given node ID.

    Args:
        ctx (Context): Application context.
        target_id (str): ID of the node to locate.

    Returns:
        tuple (parent, index):
            parent (Node | None): Parent node, or None if node is root.
            index (int | None): Index of the node within parent's children,
                                or within root list if parent is None.
    """
    for i, root in enumerate(getattr(ctx.app, "nodes", [])):
        if getattr(root, "id", None) == target_id:
            return None, i
        found, parent = _dfs_find_with_parent(root, target_id)
        if found:
            return parent, parent.children.index(found)
    return None, None



def _dfs_find_with_parent(node: Node, target_id: str) -> tuple[Optional[Node], Optional[Node]]:
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