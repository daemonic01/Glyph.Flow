# core/controls/cmd_factory.py
from __future__ import annotations

import shlex
import importlib
from typing import Any, Dict, Iterable, Optional, List

from .command_core import Command
from core.errors.command_errors import (
    UnknownCommandError, ParseError, ValidationError,
)
from .registry import COMMANDS


# ---- helpers ---------------------------------------------------------------

def _resolve_import(path: str):
    """
    Resolve 'pkg.mod.func' -> callable object.
    Raises ParseError if cannot be resolved.
    """
    try:
        mod_path, attr = path.rsplit(".", 1)
    except ValueError as e:
        raise ParseError(f"Invalid import path: '{path}'") from e
    try:
        mod = importlib.import_module(mod_path)
    except Exception as e:
        raise ParseError(f"Cannot import module '{mod_path}'") from e
    try:
        obj = getattr(mod, attr)
    except AttributeError as e:
        raise ParseError(f"Attribute '{attr}' not found in '{mod_path}'") from e
    return obj


def _find_spec(name: str) -> Optional[dict]:
    """Find spec by name or alias in REGISTRY."""
    spec = COMMANDS.get(name)
    if spec:
        return spec

    for _name, s in COMMANDS.items():
        aliases: Iterable[str] = s.get("aliases", ()) or ()
        if name in aliases:
            return s
    return None

def _strip_variadic_marker(key: str) -> str:
    return key[:-1] if key and key[-1] in ("+", "*") else key

def _parse_by_schema(argv: List[str], schema: Any) -> Dict[str, Any]:
    """
    Minimal schema-based parser.
    - None / [] / {}  -> {}
    - list -> positional names (supports variadic last positional: 'name+' or 'name*')
    - dict -> {
        positionals: [...],            # supports variadic last positional: 'name+' or 'name*'
        options: {"--flag": "param" | {"to":"param","flag":true}},
        defaults: {...}
      }
    """
    if not schema:
        return {}

    # --- list schema ---------------------------------------------------------
    if isinstance(schema, list):
        pos_keys_raw: List[str] = schema
        variadic_key: str | None = None
        variadic_kind: str | None = None  # '+' or '*'

        if pos_keys_raw:
            last = pos_keys_raw[-1]
            if last and last[-1] in ("+", "*"):
                variadic_key = _strip_variadic_marker(last)
                variadic_kind = last[-1]


        sanitized = [_strip_variadic_marker(k) for k in pos_keys_raw]
        params: Dict[str, Any] = {k: None for k in sanitized}

        i = 0
        fixed_upto = len(pos_keys_raw) - 1 if variadic_key else len(pos_keys_raw)
        for idx in range(fixed_upto):
            key = _strip_variadic_marker(pos_keys_raw[idx])
            if i < len(argv) and not argv[i].startswith("-"):
                params[key] = argv[i]
                i += 1

        if variadic_key:
            values: List[str] = []
            while i < len(argv) and not argv[i].startswith("-"):
                values.append(argv[i]); i += 1
            params[variadic_key] = values if (variadic_kind == "+" and values) or variadic_kind == "*" else None

        if i < len(argv):

            raise ParseError(f"Unknown token: {argv[i]}")
        return params

    # --- dict schema ---------------------------------------------------------
    if isinstance(schema, dict):
        pos_keys_raw: List[str] = (schema.get("positionals", []) or [])
        opt_map: Dict[str, Any] = (schema.get("options", {}) or {})
        defaults: Dict[str, Any] = dict(schema.get("defaults", {}) or {})


        variadic_key: str | None = None
        variadic_kind: str | None = None  # '+' or '*'
        if pos_keys_raw:
            last = pos_keys_raw[-1]
            if last and last[-1] in ("+", "*"):
                variadic_key = _strip_variadic_marker(last)
                variadic_kind = last[-1]


        sanitized_pos = [_strip_variadic_marker(k) for k in pos_keys_raw]
        params: Dict[str, Any] = {k: None for k in sanitized_pos}
        params.update(defaults)

        i = 0
        fixed_upto = len(pos_keys_raw) - 1 if variadic_key else len(pos_keys_raw)

        for idx in range(fixed_upto):
            key = _strip_variadic_marker(pos_keys_raw[idx])
            if i < len(argv) and not argv[i].startswith("-"):
                params[key] = argv[i]
                i += 1
            else:
                
                pass


        if variadic_key:
            values: List[str] = []
            while i < len(argv) and not argv[i].startswith("-"):
                values.append(argv[i]); i += 1
            params[variadic_key] = values if (variadic_kind == "+" and values) or variadic_kind == "*" else None

        while i < len(argv):
            tok = argv[i]
            spec = opt_map.get(tok)
            if spec is None:
                raise ParseError(f"Unknown token: {tok}")


            if isinstance(spec, dict) and spec.get("flag"):
                dest = spec.get("to") or spec.get("name") or tok.lstrip("-")
                params[dest] = True
                i += 1
                continue


            dest = spec if isinstance(spec, str) else (spec.get("to") or spec.get("name"))
            if i + 1 >= len(argv) or argv[i + 1].startswith("-"):
                raise ParseError(f"Missing value for option: {tok}")
            params[dest] = argv[i + 1]
            i += 2

        return params

    raise ParseError("Unsupported schema type for params")


# ---- public API ------------------------------------------------------------

def summon(raw: str, ctx) -> Command:
    """
    Turn a raw input line into a ready-to-run Command:
      - tokenizes raw
      - looks up blueprint (spec) from REGISTRY (by name or alias)
      - parses argv using the blueprint 'params' schema
      - resolves handler/before/after import paths (strings) to callables
      - returns Command(...) (INIT fázisban van ekkor)
    Raises:
      - ParseError, UnknownCommandError, ValidationError  (INIT fázis)
    """
    parts = shlex.split(raw)
    if not parts:
        raise ParseError("Empty input")

    name, argv = parts[0], parts[1:]

    spec = _find_spec(name)
    if not spec:
        raise UnknownCommandError(name)
    
    wants_help = (len(argv) == 1 and argv[0] in ("-h", "--help"))
    if (spec.get("params") and not argv) or wants_help:
        usage = spec.get("usage") or name
        if spec.get("usage"):
            ctx.log.key(spec["usage"])
        else:
            ctx.log.info(f"Usage: {usage}")
        return None

    if spec.get("require_data") and not ctx.nodes:
        raise ValidationError("No data loaded.")

    params = _parse_by_schema(argv, spec.get("params"))

    handler_path = spec.get("handler")
    if not handler_path:
        raise ParseError(f"Missing handler path for command '{name}'")
    handler = _resolve_import(handler_path)
    mutate = spec.get("mutate", True)
    destructive = bool(spec.get("destructive", False))

    def _resolve_maybe_list(x):
        if not x:
            return []
        if isinstance(x, str):
            return [_resolve_import(x)]
        if isinstance(x, (list, tuple)):
            return [_resolve_import(p) if isinstance(p, str) else p for p in x]
        return [x]

    spec = dict(spec)


    return Command(
        ctx=ctx,
        name=name,
        raw=raw,
        spec=spec,
        params=params,
        handler=handler,
        mutate=mutate,
        destructive=destructive
    )
