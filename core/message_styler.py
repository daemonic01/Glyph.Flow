from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime
import json

# ---------- Levels ----------

class MsgLevel(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"
    DEBUG = "DEBUG"
    HELP = "HELP"


# ---------- Resolved message object ----------

@dataclass
class ResolvedMessage:
    level: MsgLevel
    badge: str
    color: str
    text: str


# ---------- Message catalog (file-backed) ----------

class MessageCatalog:
    """
    Loads messages from a JSON file and resolves dot-notation keys like:
      get("node.create_root", name="Task", id="01.02")
    Returns a ResolvedMessage ready to pass into your formatter/wrappers.
    """
    def __init__(self, data: Dict[str, Any], lang: str = "en", version: str = "1.0") -> None:
        self.data = data
        self.lang = lang
        self.version = version
        # fallbacks (used only if fields are omitted in messages.json)
        self.default_level = MsgLevel.INFO
        self.default_badge = "INFO"
        self.default_color = "cyan"

    @classmethod
    def from_file(cls, path: str | Path) -> "MessageCatalog":
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        lang = raw.get("meta", {}).get("lang", "en")
        version = raw.get("meta", {}).get("version", "1.0")
        return cls(raw, lang=lang, version=version)

    def get(self, key: str, **params: Any) -> ResolvedMessage:
        """
        Resolve a message key to a fully formatted message object.
        If key is missing, we fail-soft by returning the key as text.
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
    
    def emit(
        self,
        log_widget,
        key: str,
        *,
        formatter_funcs: Optional["FormatterFuncs"] = None,
        timestamp: bool = True,
        as_panel: bool = False,
        inherit_level_style: bool = True,
        **params: Any,
    ) -> None:
        """
        Convenience: resolve a message, pick the right formatter, and write to RichLog.
        """

        def _coerce_writer(sink):
            # accepts either a widget (with .write) or a callable writer
            if hasattr(sink, "write"):
                return sink.write
            if callable(sink):
                return sink
            raise TypeError("emit(): expected a widget with .write or a callable(writer)")
    
        msg = self.get(key, **params)


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

    # ---- Internals ----


    def _lookup_node(self, key: str) -> Optional[Dict[str, Any]]:
        parts = key.split(".")
        node: Any = self.data
        for p in parts:
            if not isinstance(node, dict) or p not in node:
                return None
            node = node[p]
        return node if isinstance(node, dict) else None


# ---------- Formatter adapter type ----------

@dataclass
class FormatterFuncs:
    """
    Pass your formatter helpers here when writing to the log.
    Example:
        FormatterFuncs(info=format_info, warn=format_warn, error=format_error, success=format_success)
    Each function must accept this signature subset:
        f(text: str, *, timestamp: bool, as_panel: bool,
          body_style: Optional[str], inherit_level_style: bool, badge: Optional[str]) -> str
    """
    info:  Any
    warn:  Any
    error: Any
    success: Any
    debug: Any
    help: Any


# ---------- Styling helpers (no external defaults) ----------

# Default body color per level (used only when the message does not supply a color
# and the caller did not pass body_style)
LEVEL_BODY_COLOR: Dict[MsgLevel, str] = {
    MsgLevel.INFO: "cyan",
    MsgLevel.WARNING: "yellow",
    MsgLevel.ERROR: "red",
    MsgLevel.SUCCESS: "green",
    MsgLevel.DEBUG: "magenta",
    MsgLevel.HELP: "white"
}

LEVEL_BORDER_COLOR: Dict[MsgLevel, str] = {
    MsgLevel.INFO: "cyan",
    MsgLevel.WARNING: "yellow",
    MsgLevel.ERROR: "red",
    MsgLevel.SUCCESS: "green",
    MsgLevel.DEBUG: "magenta",
    MsgLevel.HELP: "white"
}


def _default_color_for_level(level_str: str) -> str:
    ls = level_str.upper()
    if ls == "ERROR":
        return "red"
    if ls in ("WARN", "WARNING"):
        return "yellow"
    if ls == "SUCCESS":
        return "green"
    return "cyan"


def _coerce_level(level_str: str) -> MsgLevel:
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
    return datetime.now().strftime("%H:%M:%S")


# ---------- Low-level renderer ----------

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
    Returns either a Rich Panel or a styled string.
    - `color`: message color from messages.json.
    - `body_style`: explicit override for the content of the message.
    - Badge: bold, inherits the (body/border) color.
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


# ---------- Public wrappers (direct use) ----------
# They work in two modes:
#   A) Literal text:  format_info("Hello")
#   B) Catalog key:   format_info(key="node.create_root", catalog=catalog, name="Task", id="01.02")
# If `key` is provided, the function resolves the message via the catalog and
# uses the level/color/badge from the catalog (ignoring the wrapper's nominal level).

def _resolve_if_key(level: MsgLevel, text: Optional[str], key: Optional[str],
                    catalog: Optional[MessageCatalog], **params: Any) -> ResolvedMessage:
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
    """Internal: single implementation all wrappers call."""
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