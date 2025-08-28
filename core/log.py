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

# A sink is any callable that can accept a rendered (Rich-markup) string,
# plus optional metadata (level, raw_text, badge) when we fan out programmatically.
Writer = Callable[..., None]


# ----------------------------
# Buffer payload representations
# ----------------------------

@dataclass
class _PendingKey:
    """Deferred 'messages.json' key emission, kept until a catalog/sink is ready."""
    key: str
    kwargs: dict

@dataclass
class _PendingRendered:
    """Deferred already-rendered string for late fan-out to sinks."""
    text: str


class _Log:
    """
    Global, app-wide logger facade.

    Configure once (e.g. in `App.on_mount`) with a writer (sink) and a MessageCatalog.
    Features:
      - Write by literal text (`info/warn/error/...`) OR by catalog key (`key()`).
      - Fan-out to multiple sinks (UI log pane, file writer, etc.).
      - Graceful buffering before sinks are configured.
      - Optional file logging with simple size-based rotation.

    Typical setup:
        log.configure(writer=rich_log.write, catalog=MessageCatalog.from_file(...))
        log.configure_from_config(app_config)  # enables file logging if configured
    """
    def __init__(self) -> None:
        # Messages.json catalog (for key-based logging). Optional at start.
        self._catalog: Optional[MessageCatalog] = None

        # Formatter function bundle. These map logical levels → concrete Rich rendering.
        self._formatters = FormatterFuncs(
            info=format_info, warn=format_warning, error=format_error,
            success=format_success, debug=format_debug, help=format_help
        )

        # Toggle runtime debug features if needed (not used in this snippet).
        self.debug_enabled: bool = False

        # Pre-sink buffer (ring): stores ('key', _PendingKey) OR ('rendered', _PendingRendered)
        # until at least one sink is configured. Prevents message loss at startup.
        self._buffer: Deque[Tuple[str, Any]] = deque(maxlen=512)

        # Fan-out sinks: each sink is called with (rendered, **meta)
        # where rendered is a Rich-markup string, meta includes 'level', 'raw_text', 'badge'.
        self._sinks: list[Callable[[str], None]] = []

        # File logging state (enabled via configure_from_config)
        self._file_handle: Optional[TextIO] = None
        self._rotate_max_bytes: Optional[int] = None
        self._rotate_backup_count: int = 0


    # ---------------------------------------------------------------------
    # Rendering helpers
    # ---------------------------------------------------------------------

    def _render_resolved(self, msg: ResolvedMessage, **opts: Any) -> str:
        """
        Render a resolved catalog message into a Rich-markup string.

        Chooses the correct formatter from level → formatter map, and applies:
        - badge (level label),
        - body style (color),
        - any additional rendering options (timestamp, as_panel, …).
        """
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
        """
        Write a rendered string to all configured sinks.

        If no sinks are present yet, enqueue into the buffer as already-rendered text.
        """
        if self._sinks:
            for sink in list(self._sinks):
                try:
                    sink(rendered)
                except Exception:
                    # Never let a single misbehaving sink break logging
                    pass
        else:
            self._buffer.append(("rendered", _PendingRendered(rendered)))


    # ---------------------------------------------------------------------
    # Public configuration API
    # ---------------------------------------------------------------------

    def set_writer(self, writer: Callable[[str], None]) -> None:
        """
        Add a new sink that accepts rendered strings.

        Useful when you want to attach additional sinks (e.g., a secondary pane)
        after the initial `configure()`.
        """
        self._sinks.append(lambda rendered, **meta: writer(rendered))
        self._flush()

    def set_catalog(self, catalog: MessageCatalog) -> None:
        """
        Set/replace the active message catalog used by `key()`.
        """
        self._catalog = catalog
        self._flush()

    def configure(self, *, writer: Writer, catalog: MessageCatalog, debug: bool = False) -> None:
        """
        Primary setup: attach a sink and the catalog, enable/disable debug mode.

        Args:
            writer: Callable that accepts the rendered Rich string (e.g., RichLog.write).
            catalog: MessageCatalog instance loaded from messages.json.
            debug: Optional debug toggle.
        """
        self._sinks.append(lambda rendered, **meta: writer(rendered))
        self._catalog = catalog
        self.debug_enabled = debug
        self._flush()

    def configure_from_config(self, cfg: dict[str, Any]) -> None:
        """
        Optional file logging setup based on app config.

        Expected structure:
            {
              "logging": true,
              "paths": { "syslog": "logs/app.log" },
              "log": {
                  "rotate": { "max_bytes": 524288, "backup_count": 3 }
              }
            }
        """
        if cfg.get("logging"):
            path = (cfg["paths"].get("syslog") or "logs/app.log")
            rot = (cfg.get("log") or {}).get("rotate") or {}

            # Rotation policy (None disables rotation)
            self._rotate_max_bytes = int(rot.get("max_bytes") or 0) or None
            self._rotate_backup_count = int(rot.get("backup_count") or 0)

            os.makedirs(os.path.dirname(path), exist_ok=True)
            self._file_handle = open(path, "a", encoding="utf-8")

            # Register file writer as another sink (receives meta)
            self._sinks.append(self._write_file)


    # ---------------------------------------------------------------------
    # File rotation & writing
    # ---------------------------------------------------------------------

    def _maybe_rotate_file(self) -> None:
        """
        Rotate the log file when size exceeds the limit:

            app.log → app.log.1 → app.log.2 → ...

        Only active if a file sink is open and rotation is enabled.
        """
        if not (self._file_handle and self._rotate_max_bytes and self._rotate_max_bytes > 0):
            return

        try:
            path = self._file_handle.name
            if not os.path.exists(path):
                return

            size = os.path.getsize(path)
            if size < self._rotate_max_bytes:
                return

            # Close current file before moving/rotating
            self._file_handle.close()
            self._file_handle = None

            if self._rotate_backup_count > 0:
                # Shift older backups upward: .(n-1) → .n
                for i in range(self._rotate_backup_count - 1, 0, -1):
                    src = f"{path}.{i}"
                    dst = f"{path}.{i+1}"
                    if os.path.exists(src):
                        try:
                            os.replace(src, dst)
                        except Exception:
                            pass

                # Move current log to .1 (or create a fresh file on failure)
                try:
                    os.replace(path, f"{path}.1")
                except Exception:
                    open(path, "w").close()
            else:
                # If no backups kept, just truncate the file
                open(path, "w").close()

            # Re-open fresh log file handle
            self._file_handle = open(path, "a", encoding="utf-8")

        except Exception:
            # Best-effort recovery if anything fails during rotation
            try:
                if not self._file_handle:
                    self._file_handle = open(path, "a", encoding="utf-8")
            except Exception:
                pass

    def _write_file(self, rendered: str, **meta) -> None:
        """
        File sink writer: persists either the raw_text (uncolored) or the rendered markup.

        The raw_text is cleaner for plain-text logs; rendered includes Rich markup.
        """
        if not self._file_handle:
            return

        from datetime import datetime
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lvl = (meta.get("level") or "INFO").upper()
        raw = meta.get("raw_text") or None

        # Optional rotation check per write
        self._maybe_rotate_file()

        line = f"[{ts}] [{lvl}] {raw if raw is not None else rendered}"
        self._file_handle.write(line + "\n")
        self._file_handle.flush()

    def close(self) -> None:
        """
        Close the file sink if open. Safe to call multiple times.
        """
        if self._file_handle:
            try:
                self._file_handle.close()
            finally:
                self._file_handle = None


    # ---------------------------------------------------------------------
    # Public logging API
    # ---------------------------------------------------------------------

    def key(self, key: str, **params: Any) -> None:
        """
        Write by a `messages.json` key.

        - Resolves the key via the MessageCatalog.
        - Renders with the appropriate formatter (level/style from catalog).
        - Fans out to sinks with extra metadata (level, raw_text, badge).
        - If no sinks yet, buffers the *rendered* string.

        Falls back to buffering the key if catalog is not yet available.
        """
        if self._catalog:
            try:
                msg = self._catalog.get(key, **params)
                rendered = self._render_resolved(
                    msg,
                    timestamp=True,
                    as_panel=False,
                    inherit_level_style=True
                )
                # Fan out: include structured metadata for sinks that want raw/plain text
                for sink in list(self._sinks) or []:
                    try:
                        sink(rendered, level=msg.level.value, raw_text=msg.text, badge=msg.badge)
                    except Exception:
                        pass

                # If still no sinks, enqueue the rendered text (buffer-safe)
                if not self._sinks:
                    self._buffer.append(("rendered", _PendingRendered(rendered)))
                return

            except Exception:
                # Catalog lookup/formatting failed → defer by key for later retry
                self._buffer.append(("key", _PendingKey(key, params)))
                return

        # No catalog yet → store the key for later resolution
        self._buffer.append(("key", _PendingKey(key, params)))


    def info(self, text: str, **kwargs: Any) -> None:
        """Log an INFO-level literal message (not catalog-based)."""
        self._emit_rendered("info", text, **kwargs)

    def warn(self, text: str, **kwargs: Any) -> None:
        """Log a WARNING-level literal message."""
        self._emit_rendered("warn", text, **kwargs)

    def error(self, text: str, **kwargs: Any) -> None:
        """Log an ERROR-level literal message."""
        self._emit_rendered("error", text, **kwargs)

    def success(self, text: str, **kwargs: Any) -> None:
        """Log a SUCCESS-level literal message."""
        self._emit_rendered("success", text, **kwargs)

    def debug(self, text: str, **kwargs: Any) -> None:
        """Log a DEBUG-level literal message."""
        self._emit_rendered("debug", text, **kwargs)

    def help(self, text: str, **kwargs: Any) -> None:
        """Log a HELP-level literal message."""
        self._emit_rendered("help", text, **kwargs)


    # ---------------------------------------------------------------------
    # Internal fan-out for literal messages
    # ---------------------------------------------------------------------

    def _emit_rendered(self, level: str, text: str, **kwargs: Any) -> None:
        """
        Render a literal text with the level's formatter and fan out to sinks.

        If no sinks are present yet, the rendered string is buffered.
        """
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
        """
        Apply the level-specific formatter to a literal text and return Rich markup.
        """
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
        """
        Drain the pre-sink buffer to the now-configured sinks.

        - For 'key' items: resolve against the catalog and render on the fly.
        - For 'rendered' items: write as-is to sinks.
        """
        if not self._sinks:
            return

        while self._buffer:
            kind, payload = self._buffer.popleft()
            if kind == "key":
                # If catalog not ready, we cannot resolve yet — skip (or re-buffer).
                if not self._catalog:
                    continue
                try:
                    # Use MessageCatalog.emit to render and write via _fanout_writer
                    self._catalog.emit(
                        self._fanout_writer,
                        payload.key,
                        **payload.kwargs
                    )
                except Exception:
                    # Skip silently; we do not re-buffer to avoid infinite loops.
                    continue
            else:
                # Already rendered: write directly
                self._fanout_writer(payload.text)


# Module-level singleton used across the app
log = _Log()
