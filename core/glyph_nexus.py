from __future__ import annotations

from pathlib import Path
from typing import Any, Optional
from core.config.config_vault import ConfigVault
from core.services.schema import NodeSchema
from core.controllers.undo_redo import UndoRedoManager

class GlyphNexus:
    """
    Context nexus for Glyph.Flow that grants access important data and tools across the app:
      - __init__: load configurations only
      - bind_core: attach non-UI services (registry, history, factory, schema, logger)
      - bind_ui: attach UI objects (presenter, log widgets, app reference)
    """

    # construction
    def __init__(self) -> None:
        # NexusCore
        self.base_dir = Path(__file__).resolve().parent.parent
        self.config = ConfigVault(path=self.base_dir / "config.json")
        self.schema = NodeSchema(self.config.get("custom_schema") or self.config.get("default_schema"))

        # AppCore
        self.app: Optional[Any] = None
        self.msg: Optional[Any] = None

        # Ui
        self.log: Optional[Any] = None
        self.presenter: Optional[Any] = None

        # Phase Flags
        self._core_bound: bool = False
        self._ui_bound: bool = False

    @property
    def undo_redo(self):
        if not hasattr(self.app, "undo_redo"):
            self.app.undo_redo = UndoRedoManager(max_size=self.config["undo_redo_limit"])
        return self.app.undo_redo
    
    @property
    def nodes(self):
        """Shortcut: access the app's node tree (list of root nodes)."""
        return self.app.nodes
    
    @property
    def confirm(self):
        """Shortcut: access the app's ConfirmService."""
        return self.app.confirm
    
    
    # binding phases
    def bind_app_core(
        self,
        *,
        app: Any
    ) -> "GlyphNexus":
        if self._core_bound:
            raise RuntimeError("Core already bound. Call bind_core only once.")
        self.app = app
        self.msg = self.app.message_catalog

        self._core_bound = True
        return self

    def bind_ui(self) -> "GlyphNexus":
        if not self._core_bound:
            raise RuntimeError("bind_core must be called before bind_ui.")
        if self._ui_bound:
            raise RuntimeError("UI already bound. Call bind_ui only once.")
        
        self.log = self.app.message_log
        self.presenter = self.app.presenter
        self._ui_bound = True
        return self

    # convenience helpers
    @property
    def ready(self) -> bool:
        """True if both core and UI are wired."""
        return self._core_bound and self._ui_bound
