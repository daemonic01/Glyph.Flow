from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from core.node import Node

@dataclass
class Diff:
    forward: List[Dict[str, Any]]
    backward: List[Dict[str, Any]]

def snapshot_node(node: Node) -> Dict[str, Any]:
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
    n = Node(
        type=snap.get("type"),
        name=snap.get("name"),
        short_desc=snap.get("short_desc"),
        full_desc=snap.get("full_desc"),
        deadline=snap.get("deadline"),
    )
    n.id = snap.get("id")  # fontos: tartsuk meg a snapshot ID-t
    for ch_snap in snap.get("children", []):
        child = node_from_snapshot(ch_snap)
        child.parent = n
        n.children.append(child)
    return n

class UndoRedoManager:
    def __init__(self, max_size: int = 200) -> None:
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

def _find_node(ctx, target_id: str) -> Optional[Node]:
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
    for child in getattr(node, "children", []):
        if getattr(child, "id", None) == target_id:
            return child
        found = _dfs(child, target_id)
        if found:
            return found
    return None

def _remove_node_by_id(ctx, target_id: str) -> None:
    parent, idx = _find_parent_and_index(ctx, target_id)
    if idx is None:
        return
    if parent is None:
        del ctx.app.nodes[idx]
    else:
        del parent.children[idx]

def _find_parent_and_index(ctx, target_id: str) -> tuple[Optional[Node], Optional[int]]:
    for i, root in enumerate(getattr(ctx.app, "nodes", [])):
        if getattr(root, "id", None) == target_id:
            return None, i
        found, parent = _dfs_find_with_parent(root, target_id)
        if found:
            return parent, parent.children.index(found)
    return None, None

def _dfs_find_with_parent(node: Node, target_id: str) -> tuple[Optional[Node], Optional[Node]]:
    for child in getattr(node, "children", []):
        if getattr(child, "id", None) == target_id:
            return child, node
        found, parent = _dfs_find_with_parent(child, target_id)
        if found:
            return found, parent
    return None, None