# --- Log formatting (message + body styling) ---
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
import re
from rich.panel import Panel


class LogLevel(Enum):
    INFO = "INFO"
    WARNING = "WARN"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"

LEVEL_STYLES: Dict[LogLevel, str] = {
    LogLevel.SUCCESS: "bold green",
    LogLevel.INFO: "#D1C693",
    LogLevel.WARNING: "bold yellow",
    LogLevel.ERROR: "bold red",
}
LEVEL_TEXT_STYLES: Dict[LogLevel, str] = {
    LogLevel.SUCCESS: "#35C718",
    LogLevel.INFO: "#DDD6B8",
    LogLevel.WARNING: "#CC9C00",
    LogLevel.ERROR: "#B60000",
}
LEVEL_CODES: Dict[LogLevel, str] = {
    LogLevel.SUCCESS: "GF-S",
    LogLevel.INFO: "GF-I",
    LogLevel.WARNING: "GF-W",
    LogLevel.ERROR: "GF-E",
}
BORDER_STYLES: Dict[LogLevel, str] = {
    LogLevel.SUCCESS: "green",
    LogLevel.INFO: "cyan",
    LogLevel.WARNING: "yellow",
    LogLevel.ERROR: "red",
}

@dataclass
class MessageCatalog:
    data: Dict[str, str]
    def resolve(self, key: str, **params: Any) -> str:
        template = self.data.get(key, key)
        try:
            return template.format(**params)
        except Exception:
            return template

# In-memory catalog; later load from loc/en/messages.json // Currently not in use. //
DEFAULT_CATALOG = MessageCatalog(data={
    "save.ok": "Save complete → {file}.",
    "save.fail": "Save failed: {reason}",
    "cmd.unknown": "Unknown command: {cmd}",
    "create.invalid_type": (
        "Invalid type: cannot create {child_type} under {parent_type} "
        "(expected: {expected})."
    ),
    "node.added": "Added {name} under {parent_id} → New ID: {id}",
    "node.created_root": "Created root node: {name} → ID: {id}",
    "node.not_found": "Node with ID {id} not found.",
})

# ---- token stylers (by param name) ---------------------------------------
def style_id(v: Any) -> str:       return f"[bold magenta]{v}[/]"
def style_file(v: Any) -> str:     return f"[italic]{v}[/]"
def style_cmd(v: Any) -> str:      return f"[bold white]{v}[/]"
def style_type(v: Any) -> str:     return f"[bold cyan]{v}[/]"
def style_name(v: Any) -> str:     return f"[white]{v}[/]"
def style_reason(v: Any) -> str:   return f"[bold red]{v}[/]"
def style_value(v: Any) -> str:    return f"[bold]{v}[/]"

STYLE_RULES: Dict[str, Any] = {
    # ids
    "id": style_id, "parent_id": style_id, "target_id": style_id,
    # files / paths
    "file": style_file, "filename": style_file, "path": style_file,
    # commands/types/names
    "cmd": style_cmd, "command": style_cmd, "type": style_type,
    "child_type": style_type, "parent_type": style_type, "expected": style_type,
    "name": style_name,
    # misc
    "reason": style_reason, "count": style_value,
}

ID_PATTERN = re.compile(r"\b\d{2}(?:\.\d{2})+\b")  # e.g., 01.02 or 01.02.03

def _apply_param_styles(params: Dict[str, Any]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for k, v in params.items():
        styler = STYLE_RULES.get(k)
        out[k] = styler(v) if styler else str(v)
    return out

def _auto_style_literals(text: str) -> str:
    # Style quoted literals: "..." → white
    text = re.sub(r'"([^"]+)"', r'[\#ffffff]\1[/]', text)
    # Style IDs if present and not already styled
    text = ID_PATTERN.sub(lambda m: style_id(m.group(0)), text)
    return text

def _timestamp() -> str:
    return datetime.now().strftime("%H:%M:%S")

def _badge(level: LogLevel) -> str:
    return f"[{LEVEL_STYLES[level]}]{level.value}[/]"

def _code(level: LogLevel) -> str:
    return f"[dim]{LEVEL_CODES[level]}[/]"



def _format(
    level: LogLevel,
    text: Optional[str] = None,
    *,
    key: Optional[str] = None,
    catalog: MessageCatalog = DEFAULT_CATALOG,
    timestamp: bool = True,
    as_panel: bool = False,
    inherit_level_style: bool = True,      # default = follow badge color
    body_style: Optional[str] = None,      # explicit override if needed
    **params: Any,
):
    # Resolve message body
    if text is not None:
        body = _auto_style_literals(text)
    else:
        styled = _apply_param_styles(params)
        body = catalog.resolve(key or "", **styled)

    # Decide the style to apply to the message body
    effective_body_style = body_style or (LEVEL_TEXT_STYLES[level] if inherit_level_style else None)

    ts = f"[dim]{_timestamp()}[/]"
    badge = _badge(level)
    code = _code(level)

    if as_panel and Panel is not None:
        return Panel(
            body,
            title=f"• {level.value} •",
            border_style=BORDER_STYLES[level],
            style=effective_body_style or "",
            padding=(0, 1),
        )

    # Non-panel: wrap the body in the chosen color (outer style, inner tags still override)
    if effective_body_style:
        body = f"[{effective_body_style}]{body}[/]"

    return f"{ts} [{badge}]: {body}" if timestamp else f"[{badge}]: {body}"



def format_success(text: Optional[str] = None, *, key: Optional[str] = None, timestamp: bool = True, as_panel: bool = False, **params: Any):
    return _format(LogLevel.SUCCESS, text, key=key, timestamp= timestamp, as_panel=as_panel, **params)

def format_info(text: Optional[str] = None, *, key: Optional[str] = None, timestamp: bool = True, as_panel: bool = False, **params: Any):
    return _format(LogLevel.INFO, text, key=key, timestamp= timestamp, as_panel=as_panel, **params)

def format_warn(text: Optional[str] = None, *, key: Optional[str] = None, timestamp: bool = True, as_panel: bool = False, **params: Any):
    return _format(LogLevel.WARNING, text, key=key, timestamp= timestamp, as_panel=as_panel, **params)

def format_error(text: Optional[str] = None, *, key: Optional[str] = None, timestamp: bool = True, as_panel: bool = True, **params: Any):
    return _format(LogLevel.ERROR, text, key=key, timestamp= timestamp, as_panel=as_panel, **params)
