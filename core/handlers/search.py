from typing import Any, Dict, Iterable, List, Optional
from core.controllers.command_result import CommandResult


def search_handler(
    ctx,
    *,
    first: Optional[str] = None,
    rest: Optional[List[str]] = None,
    mode: str = "name",
) -> CommandResult:
    """
    Handler for the 'search' command.

    Supports two modes:
      - Name search (substring, case-insensitive).
      - ID search (exact match or prefix).

    Example inputs:
        search <substring>
        search name <substring>
        search id <prefix-or-exact>

    Schema (from registry/parser):
        positionals: ["first", "rest*"]
        defaults: { "mode": "name" }

    Args:
        ctx: Application context (with ctx.app.nodes).
        first (str | None): First token (can be mode or part of query).
        rest (list[str] | None): Remaining tokens (rest of query).
        mode (str): Default search mode ("name" or "id").

    Returns:
        CommandResult:
            - code="usage" if no query provided.
            - code="no_data" if no nodes are loaded.
            - code="search_no_matches" if nothing matched.
            - code="search_results" with payload {"matches": [...]} on success.
    """
    rest = rest or []


    tokens: List[str] = []
    effective_mode = mode

    # if user explicitly gave mode ("id"/"name") as first token
    if first in ("id", "name"):
        effective_mode = cast_mode(first)
        tokens = rest
    else:
        # otherwise treat everything as query tokens
        if first:
            tokens = [first] + rest
        else:
            tokens = rest


    query = " ".join(tokens).strip()

    if not query:
        return CommandResult(code="usage", params={}, outcome=False)

    roots = list(getattr(ctx.app, "nodes", []) or [])
    if not roots:
        return CommandResult(code="no_data", params={}, outcome=False)

    matches = _run_search(roots, effective_mode, query)

    if not matches:
        return CommandResult(code="search_no_matches", params={}, outcome=True)

    return CommandResult(
        code="search_results",
        params={"nmatches": len(matches)},
        payload={"matches": matches},
        outcome=True
    )



def cast_mode(value: str) -> str:
    """Normalize search mode value into 'id' or 'name'."""
    v = (value or "").strip().lower()
    return "id" if v == "id" else "name"


def _iter_nodes(roots: Iterable[Any]) -> Iterable[Any]:
    """Iterate over all nodes in the tree (root + descendants)."""
    for r in roots:
        yield r
        for x in _dfs(r):
            yield x


def _dfs(node: Any) -> Iterable[Any]:
    """Depth-first traversal generator over a node's descendants."""
    for ch in getattr(node, "children", []) or []:
        yield ch
        yield from _dfs(ch)


def _run_search(roots: List[Any], mode: str, query: str) -> List[Dict[str, Any]]:
    """
    Execute the search query over given roots.

    Args:
        roots (list[Node]): Root nodes of the tree.
        mode (str): "id" or "name".
        query (str): Search string.

    Returns:
        list[dict]: Summarized matches (id, name, type, completed, deadline).
    """
    out: List[Dict[str, Any]] = []
    if mode == "id":
        q = query
        for n in _iter_nodes(roots):
            nid = getattr(n, "id", "")
            if nid == q or (q and nid.startswith(q)):
                out.append(_summarize(n))
    else:
        q = query.lower()
        for n in _iter_nodes(roots):
            name = getattr(n, "name", "")
            if q in name.lower():
                out.append(_summarize(n))
    return out


def _summarize(n: Any) -> Dict[str, Any]:
    """Return a compact dict representation of a node for search results."""
    return {
        "id": getattr(n, "id", ""),
        "name": getattr(n, "name", ""),
        "type": getattr(n, "type", ""),
        "completed": bool(getattr(n, "completed", False)),
        "deadline": getattr(n, "deadline", None),
    }
