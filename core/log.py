# core/log.py
from __future__ import annotations
from collections import deque
from dataclasses import dataclass
from typing import Callable, Deque, Optional, Any, Tuple, TextIO
import os
from .config_loader import load_config

from .message_styler import (
    MessageCatalog, FormatterFuncs, ResolvedMessage,
    format_info, format_warning, format_error, format_success, format_debug, format_help
)

cfg = load_config()

Writer = Callable[..., None]

@dataclass
class _PendingKey:
    key: str
    kwargs: dict

@dataclass
class _PendingRendered:
    text: str

class _Log:
    """Global, app-wide logger facade. Configure once in app.on_mount()."""
    def __init__(self) -> None:
        self._catalog: Optional[MessageCatalog] = None
        self._formatters = FormatterFuncs(
            info=format_info, warn=format_warning, error=format_error, success=format_success, debug=format_debug, help=format_help
        )
        self.debug_enabled: bool = False
        self._buffer: Deque[Tuple[str, Any]] = deque(maxlen=512)  # ('key'| 'rendered', payload)
        self._sinks: list[Callable[[str], None]] = []
        self._file_handle: Optional[TextIO] = None
        self._rotate_max_bytes: Optional[int] = None
        self._rotate_backup_count: int = 0

    # ---- configuration -----------------------------------------------------

    def _render_resolved(self, msg: ResolvedMessage, **opts: Any) -> str:
        """Pick the correct formatter based on msg.level and render Rich markup."""
        level_map = {
            "ERROR": self._formatters.error,
            "WARNING": self._formatters.warn,
            "SUCCESS": self._formatters.success,
            "DEBUG": self._formatters.debug,
            "HELP": self._formatters.help,
            "INFO": self._formatters.info,
        }
        fmt = level_map.get(msg.level.value, self._formatters.info)
        return fmt(
            msg.text,
            badge=msg.badge,
            body_style=msg.color,
            **opts
        )

    def _fanout_writer(self, rendered: str) -> None:
        if self._sinks:
            for sink in list(self._sinks):
                try:
                    sink(rendered)  # kulcsos rendernél nincs level/raw_text
                except Exception:
                    pass
        else:
            self._buffer.append(("rendered", _PendingRendered(rendered)))

    def set_writer(self, writer: Callable[[str], None]) -> None:
        self._sinks.append(lambda rendered, **meta: writer(rendered))
        self._flush()

    def set_catalog(self, catalog: MessageCatalog) -> None:
        self._catalog = catalog
        self._flush()

    def configure(self, *, writer: Writer, catalog: MessageCatalog, debug: bool = False) -> None:
        self._sinks.append(lambda rendered, **meta: writer(rendered))
        self._catalog = catalog
        self.debug_enabled = debug
        self._flush()

    def configure_from_config(self, cfg: dict[str, Any]) -> None:
        if cfg.get("logging"):
            path = (
                cfg["paths"].get("syslog")
                or "logs/app.log"
            )
            rot = (cfg.get("log") or {}).get("rotate") or {}
            self._rotate_max_bytes = int(rot.get("max_bytes") or 0) or None
            self._rotate_backup_count = int(rot.get("backup_count") or 0)

            os.makedirs(os.path.dirname(path), exist_ok=True)
            self._file_handle = open(path, "a", encoding="utf-8")
            self._sinks.append(self._write_file)

    def _maybe_rotate_file(self) -> None:
        """Rotate app.log -> app.log.1 -> app.log.2 ... if size limit reached."""
        if not (self._file_handle and self._rotate_max_bytes and self._rotate_max_bytes > 0):
            return

        try:
            path = self._file_handle.name
            if not os.path.exists(path):
                return
            size = os.path.getsize(path)
            if size < self._rotate_max_bytes:
                return

            self._file_handle.close()
            self._file_handle = None

            if self._rotate_backup_count > 0:
                for i in range(self._rotate_backup_count - 1, 0, -1):
                    src = f"{path}.{i}"
                    dst = f"{path}.{i+1}"
                    if os.path.exists(src):
                        try:
                            os.replace(src, dst)
                        except Exception:
                            pass

                try:
                    os.replace(path, f"{path}.1")
                except Exception:
                    open(path, "w").close()
            else:
                open(path, "w").close()

            self._file_handle = open(path, "a", encoding="utf-8")

        except Exception:
            try:
                if not self._file_handle:
                    self._file_handle = open(path, "a", encoding="utf-8")
            except Exception:
                pass

    def _write_file(self, rendered: str, **meta) -> None:
        if not self._file_handle:
            return
        from datetime import datetime
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lvl = (meta.get("level") or "INFO").upper()
        raw = meta.get("raw_text") or None

        line = f"[{ts}] [{lvl}] {raw if raw is not None else rendered}"
        self._file_handle.write(line + "\n")
        self._file_handle.flush()

    def close(self) -> None:
        if self._file_handle:
            try: self._file_handle.close()
            finally: self._file_handle = None

    # ---- public API: anywhere in code -------------------------------------

    def key(self, key: str, **params: Any) -> None:
        """Write by messages.json key; fan-out to sinks with meta for plain file logging."""
        if self._catalog:
            try:
                msg = self._catalog.get(key, **params)
                rendered = self._render_resolved(
                    msg,
                    timestamp=True,
                    as_panel=False,
                    inherit_level_style=True
                )
                for sink in list(self._sinks) or []:
                    try:
                        sink(rendered, level=msg.level.value, raw_text=msg.text, badge=msg.badge)
                    except Exception:
                        pass
                if not self._sinks:
                    self._buffer.append(("rendered", _PendingRendered(msg.level.value.lower(), msg.text, {})))
                return
            except Exception:
                self._buffer.append(("key", _PendingKey(key, params)))
                return
        self._buffer.append(("key", _PendingKey(key, params)))


    def info(self, text: str, **kwargs: Any) -> None:
        self._emit_rendered("info", text, **kwargs)

    def warn(self, text: str, **kwargs: Any) -> None:
        self._emit_rendered("warn", text, **kwargs)

    def error(self, text: str, **kwargs: Any) -> None:
        self._emit_rendered("error", text, **kwargs)

    def success(self, text: str, **kwargs: Any) -> None:
        self._emit_rendered("success", text, **kwargs)

    def debug(self, text: str, **kwargs: Any) -> None:
        self._emit_rendered("debug", text, **kwargs)

    def help(self, text: str, **kwargs: Any) -> None:
        self._emit_rendered("help", text, **kwargs)

    # ---- internals ---------------------------------------------------------

    def _emit_rendered(self, level: str, text: str, **kwargs: Any) -> None:
        rendered = self._render(level, text, **kwargs)
        if self._sinks:
            for sink in list(self._sinks):
                try:
                    sink(rendered, level=level, raw_text=text)
                except Exception:
                    pass
        else:
            self._buffer.append(("rendered", _PendingRendered(rendered)))

    def _render(self, level: str, text: str, **kwargs: Any):
        if level == "error":
            return self._formatters.error(text, **kwargs)
        if level == "warn":
            return self._formatters.warn(text, **kwargs)
        if level == "success":
            return self._formatters.success(text, **kwargs)
        if level == "debug":
            return self._formatters.debug(text, **kwargs)
        if level == "help":
            return self._formatters.help(text, **kwargs)
        return self._formatters.info(text, **kwargs)

    def _flush(self) -> None:
        if not self._sinks:
            return
        while self._buffer:
            kind, payload = self._buffer.popleft()
            if kind == "key":
                if not self._catalog:
                    continue
                try:
                    self._catalog.emit(self._fanout_writer, payload.key, **payload.kwargs)
                except Exception:
                    continue
            else:
                self._fanout_writer(payload.text)


log = _Log()
