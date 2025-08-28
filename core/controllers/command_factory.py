from __future__ import annotations

import shlex
import importlib
from typing import Any, Dict, Iterable, Optional, List

from .command_core import Command
from core.errors.command_errors import (
    UnknownCommandError, ParseError, ValidationError,
)
from .registry import COMMANDS




def _resolve_import(path: str):
    """
    Resolve a string path like 'pkg.module.func' into a Python callable.

    Args:
        path (str): Import path in dot-notation.

    Returns:
        Callable: The resolved function or object.

    Raises:
        ParseError: If the path is invalid, module cannot be imported,
                    or the attribute does not exist.
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
    """
    Find a command spec in the registry by name or alias.

    Args:
        name (str): Command name or alias.

    Returns:
        dict | None: Command spec if found, else None.
    """
    spec = COMMANDS.get(name)
    if spec:
        return spec

    for _name, s in COMMANDS.items():
        aliases: Iterable[str] = s.get("aliases", ()) or ()
        if name in aliases:
            return s
    return None



def _strip_variadic_marker(key: str) -> str:
    """
    Remove variadic marker ('+' or '*') from the end of a key.

    Example:
        'items+' -> 'items'
        'args*'  -> 'args'
    """

    return key[:-1] if key and key[-1] in ("+", "*") else key



def _parse_by_schema(argv: List[str], schema: Any) -> Dict[str, Any]:
    """
    Parse arguments based on a schema definition.

    Schema forms:
      - None / [] / {}  -> {}
      - list -> positional params (supports variadic last positional: 'arg+' or 'arg*')
      - dict -> {
            positionals: [...],            # supports variadic last positional
            options: {"--flag": "param" | {"to":"param","flag":true}},
            defaults: {...}
        }

    Args:
        argv (list[str]): Command-line arguments (already tokenized).
        schema (Any): Schema definition (list or dict).

    Returns:
        dict: Parsed parameters.

    Raises:
        ParseError: On unknown tokens, missing values, or unsupported schema.
    """

    if not schema:
        return {}

    # --- LIST SCHEMA (simple positionals) ---
    if isinstance(schema, list):
        pos_keys_raw: List[str] = schema
        variadic_key: str | None = None
        variadic_kind: str | None = None  # '+' or '*'

        # detect variadic last positional
        if pos_keys_raw:
            last = pos_keys_raw[-1]
            if last and last[-1] in ("+", "*"):
                variadic_key = _strip_variadic_marker(last)
                variadic_kind = last[-1]


        sanitized = [_strip_variadic_marker(k) for k in pos_keys_raw]
        params: Dict[str, Any] = {k: None for k in sanitized}

        # parse fixed positionals
        i = 0
        fixed_upto = len(pos_keys_raw) - 1 if variadic_key else len(pos_keys_raw)
        for idx in range(fixed_upto):
            key = _strip_variadic_marker(pos_keys_raw[idx])
            if i < len(argv) and not argv[i].startswith("-"):
                params[key] = argv[i]
                i += 1

        # parse variadic positional (collects multiple values)
        if variadic_key:
            values: List[str] = []
            while i < len(argv) and not argv[i].startswith("-"):
                values.append(argv[i]); i += 1
            params[variadic_key] = values if (variadic_kind == "+" and values) or variadic_kind == "*" else None

        if i < len(argv):

            raise ParseError(f"Unknown token: {argv[i]}")
        return params

    # --- DICT SCHEMA (positionals + options + defaults) ---
    if isinstance(schema, dict):
        pos_keys_raw: List[str] = (schema.get("positionals", []) or [])
        opt_map: Dict[str, Any] = (schema.get("options", {}) or {})
        defaults: Dict[str, Any] = dict(schema.get("defaults", {}) or {})

        # detect variadic last positional
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

        # parse fixed positionals
        i = 0
        fixed_upto = len(pos_keys_raw) - 1 if variadic_key else len(pos_keys_raw)

        for idx in range(fixed_upto):
            key = _strip_variadic_marker(pos_keys_raw[idx])
            if i < len(argv) and not argv[i].startswith("-"):
                params[key] = argv[i]
                i += 1
            else:
                
                pass

        # parse variadic positional
        if variadic_key:
            values: List[str] = []
            while i < len(argv) and not argv[i].startswith("-"):
                values.append(argv[i]); i += 1
            params[variadic_key] = values if (variadic_kind == "+" and values) or variadic_kind == "*" else None

        # parse options
        while i < len(argv):
            tok = argv[i]
            spec = opt_map.get(tok)
            if spec is None:
                raise ParseError(f"Unknown token: {tok}")

            # boolean flag option
            if isinstance(spec, dict) and spec.get("flag"):
                dest = spec.get("to") or spec.get("name") or tok.lstrip("-")
                params[dest] = True
                i += 1
                continue

            # key-value option
            dest = spec if isinstance(spec, str) else (spec.get("to") or spec.get("name"))
            if i + 1 >= len(argv) or argv[i + 1].startswith("-"):
                raise ParseError(f"Missing value for option: {tok}")
            params[dest] = argv[i + 1]
            i += 2

        return params

    raise ParseError("Unsupported schema type for params")




def summon(raw: str, ctx) -> Command:
    """
    Turn a raw input line into a ready-to-run Command.

    Steps:
      1. Tokenize input with shlex.
      2. Find command spec by name/alias from REGISTRY.
      3. Parse argv using the spec's schema.
      4. Resolve handler import path to callable.
      5. Build Command object in INIT state.

    Args:
        raw (str): Raw input line from user.
        ctx: Application context.

    Returns:
        Command | None: Ready-to-run Command, or None if help was requested.

    Raises:
        ParseError: On invalid syntax, missing handler path, or schema errors.
        UnknownCommandError: If command not found.
        ValidationError: If spec requires data but no data is loaded.
    """
    parts = shlex.split(raw)
    if not parts:
        raise ParseError("Empty input")

    name, argv = parts[0], parts[1:]

    # lookup command spec
    spec = _find_spec(name)
    if not spec:
        raise UnknownCommandError(name)
    
    # show usage/help if requested
    wants_help = (len(argv) == 1 and argv[0] in ("-h", "--help"))
    if (spec.get("params") and not argv) or wants_help:
        usage = spec.get("usage") or name
        if spec.get("usage"):
            ctx.log.key(spec["usage"])
        else:
            ctx.log.info(f"Usage: {usage}")
        return None

    # enforce data requirement
    if spec.get("require_data") and not ctx.nodes:
        raise ValidationError("No data loaded.")

    # parse arguments
    params = _parse_by_schema(argv, spec.get("params"))

    # resolve handler
    handler_path = spec.get("handler")
    if not handler_path:
        raise ParseError(f"Missing handler path for command '{name}'")
    handler = _resolve_import(handler_path)
    
    mutate = spec.get("mutate", True)
    mutate_config = spec.get("mutate_config", True)
    destructive = bool(spec.get("destructive", False))

    spec = dict(spec)


    return Command(
        ctx=ctx,
        name=name,
        raw=raw,
        spec=spec,
        params=params,
        handler=handler,
        mutate=mutate,
        mutate_config=mutate_config,
        destructive=destructive
    )
