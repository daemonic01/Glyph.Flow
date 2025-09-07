from __future__ import annotations

from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path
import json

from core.controllers.command_result import CommandResult
from core.node import Node


def import_handler(ctx, *,
                   file: Optional[str] = None,
                   mode: str = "append",
                   **kwargs) -> CommandResult:
    """
    Import JSON into the node tree.

    Parameters (registry -> handler):
      - file: path to a JSON file that contains a list[ node_dict ]  (Node.to_dict() shape)
      - mode: "replace" | "append" | "merge"

    Returns:
      CommandResult with 'success' or an error code (file_missing, parse_error, invalid_mode).
    """
    if not file:
        return CommandResult(code="file_missing",
                             params={"file": str(file or "")},
                             outcome=False)

    mode = (mode or "append").lower()
    if mode not in {"replace", "append", "merge"}:
        return CommandResult(code="invalid_mode",
                             params={"mode": mode},
                             outcome=False)

    src = Path(file)
    if not src.exists():
        return CommandResult(code="file_missing",
                             params={"file": str(src)},
                             outcome=False)

    # Load JSON -> list[Node]
    try:
        new_roots = _load_roots_from_json(src)
    except Exception as e:
        return CommandResult(code="parse_error",
                             params={"file": str(src), "error": str(e)},
                             outcome=False)

    # Apply according to mode
    if mode == "replace":
        removed_count = _count_nodes(ctx.nodes)
        ctx.app.nodes = new_roots
        # Assign missing/invalid IDs safely
        Node.relabel_missing_ids(ctx.nodes)

        _safe_sort_roots(ctx.nodes)
        Node.relabel_roots(ctx.nodes)
        created_count = _count_nodes(new_roots)
        return CommandResult(code="replaced",
                             params={"file": str(src),
                                     "removed": removed_count,
                                     "created": created_count},
                             outcome=True)

    if mode == "append":
        created = _append_roots(ctx.nodes, new_roots)
        Node.relabel_missing_ids(ctx.nodes)
        _safe_sort_roots(ctx.nodes)
        Node.relabel_roots(ctx.nodes)
        return CommandResult(code="appended",
                             params={"file": str(src), "created": created},
                             outcome=True)

    # mode == "merge"
    updated, created = _merge_into(ctx.nodes, new_roots)

    Node.relabel_missing_ids(ctx.nodes)
    _safe_sort_roots(ctx.nodes)
    Node.relabel_roots(ctx.nodes)
    return CommandResult(code="merged",
                         params={"file": str(src),
                                 "updated": updated,
                                 "created": created},
                         outcome=True)


# JSON loading

def _load_roots_from_json(path: Path) -> List[Node]:
    """
    Expect a JSON array of Node dicts (as produced by Node.to_dict()) and rebuild roots.
    """
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Top-level JSON must be a list of node objects.")
    roots = [Node.from_dict(d) for d in data]
    # Ensure missing IDs filled and children fixed under each parent
    Node.relabel_missing_ids(roots)
    return roots


# Counters / helpers

def _count_nodes(roots: List[Node]) -> int:
    def count(n: Node) -> int:
        return 1 + sum(count(c) for c in n.children)
    return sum(count(r) for r in roots or [])


def _safe_sort_roots(roots: List[Node]) -> None:
    """
    Sort roots by their numeric id if possible, otherwise keep stable order.
    """
    try:
        roots.sort(key=lambda r: int(r.id))
    except Exception:
        pass


# APPEND mode

def _append_roots(existing_roots: List[Node], incoming_roots: List[Node]) -> int:
    """
    Append incoming roots to existing tree; prefer keeping incoming IDs.
    If an incoming root has no valid id or collides, we will fix afterwards via relabel_missing_ids.
    """
    created = 0
    for r in incoming_roots:
        r.parent = None
        existing_roots.append(r)
        created += _count_nodes([r])
    return created


# MERGE mode

def _merge_into(existing_roots: List[Node], incoming_roots: List[Node]) -> Tuple[int, int]:
    """
    Merge incoming into existing by ID.
    - Root with the same id -> merge fields + children by id.
    - Otherwise -> append as new root (keep provided id if possible).
    Returns: (updated_count, created_count)
    """
    existing_by_id = _index_by_id(existing_roots)
    updated = 0
    created = 0

    for inc in incoming_roots:
        if inc.id and inc.id in existing_by_id:
            tgt = existing_by_id[inc.id]
            u, c = _merge_node(tgt, inc)
            updated += u
            created += c
        else:
            # New root
            inc.parent = None
            existing_roots.append(inc)
            created += _count_nodes([inc])
            # update index for potential next iterations
            if inc.id:
                existing_by_id[inc.id] = inc

    return updated, created


def _index_by_id(roots: List[Node]) -> Dict[str, Node]:
    out: Dict[str, Node] = {}
    def walk(n: Node):
        if isinstance(n.id, str):
            out[n.id] = n
        for c in n.children:
            walk(c)
    for r in roots:
        walk(r)
    return out


def _merge_node(target: Node, incoming: Node) -> Tuple[int, int]:
    """
    Merge 'incoming' into 'target' (same id). Keep 'target' identity; update scalar fields,
    then merge children by id recursively. Returns (updated, created).
    """
    updated = 0
    created = 0

    if target.name != incoming.name:
        target.name = incoming.name; updated += 1
    if target.type != incoming.type:
        target.type = incoming.type; updated += 1
    if target.deadline != incoming.deadline:
        target.deadline = incoming.deadline; updated += 1
    if target.short_desc != incoming.short_desc:
        target.short_desc = incoming.short_desc; updated += 1
    if target.full_desc != incoming.full_desc:
        target.full_desc = incoming.full_desc; updated += 1
    if target.completed != incoming.completed:
        target.completed = incoming.completed; updated += 1
    if (not getattr(target, "created_at", None)) and getattr(incoming, "created_at", None):
        target.created_at = incoming.created_at; updated += 1

    # Merge children by id
    tgt_by_id: Dict[str, Node] = {c.id: c for c in target.children if isinstance(c.id, str)}
    for child_in in incoming.children:
        if isinstance(child_in.id, str) and child_in.id in tgt_by_id:
            # Merge into existing child
            child_tgt = tgt_by_id[child_in.id]
            u, c = _merge_node(child_tgt, child_in)
            updated += u
            created += c
        else:
            # Insert as new child, keep the given id if possible
            child_in.parent = target
            target.children.append(child_in)
            created += _count_nodes([child_in])

    return updated, created
