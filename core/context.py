from core.log import log

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

    def __init__(self, *, app):
        """
        Initialize a new Context.

        Args:
            app: The main application instance (Textual App).
        """
        self.app = app
        self.log = log
        self.presenter = app.presenter
        self.msg = app.message_catalog
        self.schema = app.schema
        self.config = app.config



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

    
