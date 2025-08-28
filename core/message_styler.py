from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime
import json


class MsgLevel(str, Enum):
    """Severity / category of a message rendered to the UI / logs."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"
    DEBUG = "DEBUG"
    HELP = "HELP"


@dataclass
class ResolvedMessage:
    """
    Fully resolved message ready to render.

    Attributes:
        level: Message severity (MsgLevel).
        badge: Short uppercase label (e.g., "INFO", "ERROR") shown alongside text.
        color: Preferred body color for the message content.
        text:  Final formatted text (parameters already substituted).
    """
    level: MsgLevel
    badge: str
    color: str
    text: str



class MessageCatalog:
    """
    Message catalog loader and resolver.

    Loads messages from a JSON file and resolves dot-notation keys like:
      get("node.create_root", name="Task", id="01.02")

    Returns a ResolvedMessage ready to pass into a formatter/wrapper.
    """
    def __init__(self, data: Dict[str, Any], lang: str = "en", version: str = "1.0") -> None:
        self.data = data
        self.lang = lang
        self.version = version
        self.default_level = MsgLevel.INFO
        self.default_badge = "INFO"
        self.default_color = "cyan"



    @classmethod
    def from_file(cls, path: str | Path) -> "MessageCatalog":
        """
        Load a catalog from a JSON file.

        The file may optionally contain a `meta` node:
          {
            "meta": { "lang": "en", "version": "1.2" },
            ...
          }
        """
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        lang = raw.get("meta", {}).get("lang", "en")
        version = raw.get("meta", {}).get("version", "1.0")
        return cls(raw, lang=lang, version=version)



    def get(self, key: str, **params: Any) -> ResolvedMessage:
        """
        Resolve a message key to a ResolvedMessage.

        Args:
            key:     Dot-notation lookup key (e.g., "cmd.create.success").
            **params Arbitrary fields used to format the message template.

        Returns:
            ResolvedMessage with level/badge/color/text derived from the catalog
            node or sensible defaults if the key is missing.
        """
        node = self._lookup_node(key)
        if node is None or not isinstance(node, dict):
            text = key.format(**params) if params else key
            return ResolvedMessage(self.default_level, self.default_badge, self.default_color, text)

        level_str = (node.get("level") or self.default_level.value).upper()
        badge     = node.get("badge") or level_str
        color     = node.get("color") or _default_color_for_level(level_str)
        template  = node.get("text")  or key

        try:
            text = template.format(**params)
        except Exception:
            text = template

        level = _coerce_level(level_str)
        return ResolvedMessage(level, badge, color, text)
    


    def emit(self, log_widget, key: str, *,
        formatter_funcs: Optional["FormatterFuncs"] = None,
        timestamp: bool = True, as_panel: bool = False,
        inherit_level_style: bool = True, **params: Any,
    ) -> None:
        """
        Convenience utility: resolve a message by key, select the
        corresponding formatter function based on the resolved level,
        render it, and write it to the provided sink.

        The `log_widget` can be either:
          - a Textual/Rich widget that exposes `.write(rendered)`, or
          - a callable that accepts a single rendered string.

        Args:
            log_widget: Sink to write to (widget with `write` or a callable).
            key:        Message key to resolve.
            formatter_funcs: Optional FormatterFuncs; if not provided, uses
                            DEFAULT_FORMATTERS.
            timestamp:  Include timestamp in rendered output.
            as_panel:   Render as a Rich Panel (if Rich is available).
            inherit_level_style:
                         If True, use level-based color defaults when the
                         catalog or caller did not specify a color.
            **params:   Parameters for catalog formatting.
        """


        def _coerce_writer(sink):
            # Accept either a widget (with .write) or a direct callable sink.
            if hasattr(sink, "write"):
                return sink.write
            if callable(sink):
                return sink
            raise TypeError("emit(): expected a widget with .write or a callable(writer)")
    
        msg = self.get(key, **params)

        # Map the resolved level to a formatter name in FormatterFuncs
        dispatch_map = {
            MsgLevel.ERROR: "error",
            MsgLevel.WARNING: "warn",
            MsgLevel.SUCCESS: "success",
            MsgLevel.INFO: "info",
            MsgLevel.DEBUG: "debug",
            MsgLevel.HELP: "help"
        }


        func_name = dispatch_map.get(msg.level, "info")
        ff = formatter_funcs or DEFAULT_FORMATTERS
        formatter = getattr(ff, func_name) 

        # Render with the resolved style information.
        rendered = formatter(
            msg.text,
            timestamp=timestamp,
            as_panel=as_panel,
            body_style=msg.color,
            inherit_level_style=inherit_level_style,
            badge=msg.badge,
        )

        writer = _coerce_writer(log_widget)
        writer(rendered)



    def _lookup_node(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Traverse the nested dictionary using a dot-notation key.

        Returns:
            The innermost dict for the key, or None if any segment is missing.
        """

        parts = key.split(".")
        node: Any = self.data
        for p in parts:
            if not isinstance(node, dict) or p not in node:
                return None
            node = node[p]
        return node if isinstance(node, dict) else None



@dataclass
class FormatterFuncs:
    """
    Adapter that carries references to concrete formatting functions.

    The rendering layer (e.g., Rich/Textual) provides these functions.
    Each function must support the following signature subset:

        f(text: str, *,
          timestamp: bool,
          as_panel: bool,
          body_style: Optional[str],
          inherit_level_style: bool,
          badge: Optional[str]) -> str

    Attributes:
        info, warn, error, success, debug, help: Callables for each level.
    """
    info:  Any
    warn:  Any
    error: Any
    success: Any
    debug: Any
    help: Any


# Default body color per level (used if catalog and caller omit a color).
LEVEL_BODY_COLOR: Dict[MsgLevel, str] = {
    MsgLevel.INFO: "cyan",
    MsgLevel.WARNING: "yellow",
    MsgLevel.ERROR: "red",
    MsgLevel.SUCCESS: "green",
    MsgLevel.DEBUG: "magenta",
    MsgLevel.HELP: "white"
}

# Default border color per level (used by Panel border).
LEVEL_BORDER_COLOR: Dict[MsgLevel, str] = {
    MsgLevel.INFO: "cyan",
    MsgLevel.WARNING: "yellow",
    MsgLevel.ERROR: "red",
    MsgLevel.SUCCESS: "green",
    MsgLevel.DEBUG: "magenta",
    MsgLevel.HELP: "white"
}


def _default_color_for_level(level_str: str) -> str:
    """Map a textual level to a default body color."""
    ls = level_str.upper()
    if ls == "ERROR":
        return "red"
    if ls in ("WARN", "WARNING"):
        return "yellow"
    if ls == "SUCCESS":
        return "green"
    return "cyan"


def _coerce_level(level_str: str) -> MsgLevel:
    """Map a textual level to a MsgLevel enum (fallback to INFO)."""
    ls = level_str.upper()
    if ls == "INFO":
        return MsgLevel.INFO
    if ls in ("WARN", "WARNING"):
        return MsgLevel.WARNING
    if ls == "ERROR":
        return MsgLevel.ERROR
    if ls == "SUCCESS":
        return MsgLevel.SUCCESS
    if ls == "DEBUG":
        return MsgLevel.DEBUG
    if ls == "HELP":
        return MsgLevel.HELP
    return MsgLevel.INFO


def _timestamp() -> str:
    """Return a short timestamp string suitable for inline log prefixes."""
    return datetime.now().strftime("%H:%M:%S")


# LOW LEVEL RENDERER

try:
    from rich.panel import Panel
except Exception:
    Panel = None


def _render(level: MsgLevel,
            text: str,
            *,
            badge: Optional[str] = None,
            color: Optional[str] = None,
            timestamp: bool = True,
            as_panel: bool = False,
            inherit_level_style: bool = True,
            body_style: Optional[str] = None) -> Any:
    """
    Render a message either as a Rich Panel or as a styled string.

    Args:
        level:    Message severity used for default styles.
        text:     Message body text (already formatted).
        badge:    Short label shown with the message; falls back to level name.
        color:    Preferred body color (from catalog).
        timestamp:
                  If True, prefix the string with a dim time marker.
        as_panel: If True and Rich is available, render as a Panel.
        inherit_level_style:
                  If True, apply level-based default colors when the caller
                  didn't set `color`/`body_style`.
        body_style:
                  Explicit override for body color (takes precedence over `color`).

    Returns:
        Rich Panel or a markup string (depending on environment/flags).
    """

    badge_text = badge or level.value

    effective_body_color = body_style or color or (LEVEL_BODY_COLOR[level] if inherit_level_style else None)
    badge_color = effective_body_color or LEVEL_BORDER_COLOR[level]
    badge_markup = f"[bold {badge_color}]{badge_text}[/]"

    if as_panel and Panel is not None:
        return Panel(
            text,
            title=f"[{badge_markup}]",
            border_style=color or LEVEL_BORDER_COLOR[level],
            style=effective_body_color or "",
            padding=(0, 1),
        )

    ts = f"[dim]{_timestamp()}[/]" if timestamp else ""
    body = f"[{effective_body_color}]{text}[/]" if effective_body_color else text
    return f"{ts} [{badge_markup}]: {body}" if timestamp else f"[{badge_markup}]: {body}"


# PUBLIC WRAPPERS (for direct use)
# They work in two modes:
#   A) Literal text:
#         format_info("Hello")
#   B) Catalog key:
#         format_info(key="node.create_root", catalog=catalog, name="Task", id="01.02")
# If `key` is provided, the function resolves the message via the catalog and
# uses the level/color/badge from the catalog (ignoring the wrapper's nominal level).

def _resolve_if_key(level: MsgLevel, text: Optional[str], key: Optional[str],
                    catalog: Optional[MessageCatalog], **params: Any) -> ResolvedMessage:
    """
    If `key` is supplied, resolve from catalog; otherwise create a literal
    ResolvedMessage with defaults derived from the wrapper's level.
    """
    if key:
        if not catalog:
            raise ValueError("catalog is required when using key=...")
        return catalog.get(key, **params)
    return ResolvedMessage(level=level, badge=level.value, color=LEVEL_BODY_COLOR[level], text=text or "")


from functools import update_wrapper

def _format_dispatch(level: MsgLevel,
                     text: Optional[str] = None, *,
                     key: Optional[str] = None,
                     catalog: Optional[MessageCatalog] = None,
                     timestamp: bool = True,
                     as_panel: bool = False,
                     inherit_level_style: bool = True,
                     body_style: Optional[str] = None,
                     badge: Optional[str] = None,
                     **params: Any) -> Any:
    """
    Internal dispatcher used by all `format_*` wrappers.

    Resolves the message (literal vs. catalog), then delegates to `_render`.
    """
    msg = _resolve_if_key(level, text, key, catalog, **params)
    return _render(
        msg.level, msg.text,
        badge=badge or msg.badge,
        color=msg.color,
        timestamp=timestamp,
        as_panel=as_panel,
        inherit_level_style=inherit_level_style,
        body_style=body_style,
    )

def _make_wrapper(level: MsgLevel):
    """
    Factory that builds the public `format_<level>` functions with the same
    uniform signature.
    """
    def wrapper(text: Optional[str] = None, *,
                key: Optional[str] = None,
                catalog: Optional[MessageCatalog] = None,
                timestamp: bool = True,
                as_panel: bool = False,
                inherit_level_style: bool = True,
                body_style: Optional[str] = None,
                badge: Optional[str] = None,
                **params: Any) -> Any:
        return _format_dispatch(level, text,
                                key=key, catalog=catalog,
                                timestamp=timestamp, as_panel=as_panel,
                                inherit_level_style=inherit_level_style,
                                body_style=body_style, badge=badge, **params)
    wrapper.__name__ = f"format_{level.name.lower()}"
    wrapper.__doc__ = f"Format a {level.name} message. Same signature as other format_* wrappers."
    return update_wrapper(wrapper, _format_dispatch, assigned=())

_WRAPPER_LEVELS = [MsgLevel.INFO, MsgLevel.WARNING, MsgLevel.ERROR, MsgLevel.SUCCESS, MsgLevel.DEBUG, MsgLevel.HELP]

for _lvl in _WRAPPER_LEVELS:
    globals()[f"format_{_lvl.name.lower()}"] = _make_wrapper(_lvl)

DEFAULT_FORMATTERS = FormatterFuncs(
    info=format_info,
    warn=format_warning,
    error=format_error,
    success=format_success,
    debug=format_debug,
    help=format_help
)