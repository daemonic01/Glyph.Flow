from __future__ import annotations
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union

DEFAULT_CONFIG: Dict[str, Any] = {
    "version": "0.1.0",
    "theme": "crimson",
    "paths": {
        "data": "data/node_data.json",
        "help": "assets/help.txt",
        "messages": "loc/en/messages.json",
        "file_tests": "tests/files.txt",
        "syslog": "logs/app.log"
    },
    "node_properties": {
        "short_desc_length_limit": 100,
        "full_desc_length_limit": 300
    },
    "default_schema": ["Project", "Phase", "Task", "Subtask"],
    "custom_schema": [],
    "logging": True,
    "test_mode": False,
    "log": {"rotate": {"max_bytes": 262144, "backup_count": 5}},
    "autosave": True,
    "assume_yes": False,
    "command_history_maxlen": 50,
    "undo_redo_limit": 50
}

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = BASE_DIR / "config.json"


# small utilities
def _deep_get(d: Dict[str, Any], path: str, default: Any = None) -> Any:
    cur: Any = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur

def _deep_set(d: Dict[str, Any], path: str, value: Any) -> None:
    cur = d
    parts = path.split(".")
    for p in parts[:-1]:
        cur = cur.setdefault(p, {})
    cur[parts[-1]] = value

def _deep_merge(base: Dict[str, Any], patch: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    for k, v in (patch or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out

def _atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        shutil.move(tmp_name, str(path))
    finally:
        try:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)
        except Exception:
            pass


class ConfigVault:
    """
    Minimal, ergonomic JSON-backed configuration store.

    Features:
      - Load/Save (atomic save)
      - Dot-path get/set
      - Deep-merge edit(patch)
      - Dict-like read access for backward compatibility
    """

    def __init__(self, path: Union[str, Path] = CONFIG_PATH, defaults: Dict[str, Any] = DEFAULT_CONFIG):
        self._path = Path(path)
        self._defaults = defaults
        self._data: Dict[str, Any] = {}
        self.load()



    # I/O
    def load(self) -> Dict[str, Any]:
        """Load config from disk if present; otherwise write defaults."""
        if not self._path.exists():
            self._data = dict(self._defaults)
            self.save()
            return self._data

        try:
            with self._path.open("r", encoding="utf-8") as f:
                on_disk = json.load(f)
        except json.JSONDecodeError:
            # fallback to defaults if invalid file
            on_disk = dict(self._defaults)

        # merge defaults <- on_disk (on_disk wins)
        self._data = _deep_merge(self._defaults, on_disk or {})
        return self._data



    def reload(self) -> Dict[str, Any]:
        """Alias for load(); re-read from disk."""
        return self.load()



    def save(self) -> None:
        """Persist current in-memory config to disk (atomic)."""
        _atomic_write_json(self._path, self._data)



    # accessors
    def get(self, path: str, default: Any = None, cast: Optional[Callable[[Any], Any]] = None) -> Any:
        """
        Get a value via dot-path. Optionally cast it (e.g. bool/int).
        Example: cfg.get("node_properties.short_desc_length_limit", 80, int)
        """
        val = _deep_get(self._data, path, default)
        if cast is not None and val is not None:
            try:
                return cast(val)
            except Exception:
                return default
        return val



    def edit(self, key_or_patch: Union[str, Dict[str, Any]], value: Any = None) -> None:
        """
        Edit the in-memory config.

        - If key_or_patch is a dict, deep-merge it into the config.
          e.g. config.edit({"node_properties": {"short_desc_length_limit": 120}})
        - If key_or_patch is a dot-path string, set that key to `value`.
          e.g. config.edit("autosave", False)  or  cconfigg.edit("log.rotate.max_bytes", 524288)
        """
        if isinstance(key_or_patch, dict):
            self._data = _deep_merge(self._data, key_or_patch)
        elif isinstance(key_or_patch, str):
            _deep_set(self._data, key_or_patch, value)
        else:
            raise TypeError("edit() expects a dict patch or a dot-path string and a value.")

    # alias
    set = edit

    def as_dict(self, *, copy: bool = True) -> Dict[str, Any]:
        """Return the whole config mapping (optionally a shallow copy)."""
        return dict(self._data) if copy else self._data

    # dict-like read
    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __contains__(self, key: str) -> bool:
        return key in self._data

    # misc
    @property
    def path(self) -> Path:
        return self._path

    def __repr__(self) -> str:
        return f"ConfigVault(path={self._path!s}, keys={list(self._data.keys())})"
