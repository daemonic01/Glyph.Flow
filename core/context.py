from pathlib import Path
from core.controllers.undo_redo import UndoRedoManager
from core.config.config_vault import ConfigVault
from core.services.schema import NodeSchema

class Context:
    """
    Shared runtime context passed into command handlers.

    The Context provides unified access to the main application state
    and services, so handlers don't need to know about the internals
    of the Textual app directly.

    Attributes:
        app: Reference to the main application instance.
        log: Global logger facade (`core.log.log`).
        presenter: Secondary log/presenter (e.g. output pane).
        msg: Message catalog (for localized/system messages).
        schema: Current NodeSchema (validates node types/structure).
        config: Application configuration dict.
    """

    def __init__(self, app):
        """
        Initialize a new Context.

        Args:
            app: The main application instance (Textual App).
        """
        self.base_dir = Path(__file__).resolve().parent.parent
        self.app = app
        self.log = app.message_log
        self.presenter = app.presenter
        self.msg = app.message_catalog
        self.config = ConfigVault(path=self.base_dir / "config.json")
        self.schema = NodeSchema(self.config.get("custom_schema") or self.config.get("default_schema"))

        if not hasattr(self.app, "undo_redo"):
            self.app.undo_redo = UndoRedoManager(max_size=self.config["undo_redo_limit"])

    @property
    def undo_redo(self):
        return self.app.undo_redo



    @property
    def nodes(self):
        """Shortcut: access the app's node tree (list of root nodes)."""
        return self.app.nodes
    


    @property
    def confirm(self):
        """Shortcut: access the app's ConfirmService."""
        return self.app.confirm



    def set_nodes(self, new_nodes):
        """
        Replace the entire node tree.

        Args:
            new_nodes (list[Node]): New list of root nodes.
        """
        self.app.nodes = new_nodes
        