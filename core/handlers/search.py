from typing import Any, Dict, Iterable, List, Optional, Tuple
from core.controllers.command_result import CommandResult


def search_handler(
    ctx,
    *,
    first: Optional[str] = None,   # may be "id"/"name" OR the first token of the query
    rest: Optional[List[str]] = None,  # rest of tokens (from variadic positional)
    # defaults can inject this too, but we normalize below anyway:
    mode: str = "name",
) -> CommandResult:
    """
    Search nodes either by name-substring (default) or by ID exact/prefix.
    Accepts:
      - `search <substring>`
      - `search name <substring>`
      - `search id <prefix-or-exact>`

    Params (from registry/parser):
      positionals: ["first", "rest*"]
      defaults: { "mode": "name" }
    """
    rest = rest or []

    # Normalize inputs:
    tokens: List[str] = []
    effective_mode = mode

    if first in ("id", "name"):
        effective_mode = cast_mode(first)
        tokens = rest
    else:
        # `first` is actually part of the query
        if first:
            tokens = [first] + rest
        else:
            tokens = rest

    # Build the query string
    query = " ".join(tokens).strip()

    # Usage if no query at all
    if not query:
        return CommandResult(code="usage", params={})

    # No data at all?
    roots = list(getattr(ctx.app, "nodes", []) or [])
    if not roots:
        return CommandResult(code="no_data", params={})

    # Do the search
    matches = _run_search(roots, effective_mode, query)

    if not matches:
        return CommandResult(code="search_no_matches", params={})

    # Return as payload for presenter (optional)
    # Keep params minimal for logging
    return CommandResult(
        code="search_results",
        params={"nmatches": len(matches)},
        payload={"matches": matches},
    )


# --- helpers -----------------------------------------------------------------

def cast_mode(value: str) -> str:
    v = (value or "").strip().lower()
    return "id" if v == "id" else "name"


def _iter_nodes(roots: Iterable[Any]) -> Iterable[Any]:
    for r in roots:
        yield r
        for x in _dfs(r):
            yield x


def _dfs(node: Any) -> Iterable[Any]:
    for ch in getattr(node, "children", []) or []:
        yield ch
        yield from _dfs(ch)


def _run_search(roots: List[Any], mode: str, query: str) -> List[Dict[str, Any]]:
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
    return {
        "id": getattr(n, "id", ""),
        "name": getattr(n, "name", ""),
        "type": getattr(n, "type", ""),
        "completed": bool(getattr(n, "completed", False)),
        "deadline": getattr(n, "deadline", None),
    }
