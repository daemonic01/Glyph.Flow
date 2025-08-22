from textual.app import App, ComposeResult
from textual.widgets import Input, RichLog
from textual.containers import Vertical
from textual.reactive import reactive
from textual import events
from core.data_io import load_node_tree
from core.node import Node
from typing import Optional
from core.config_loader import load_config
from core.message_styler import MessageCatalog
from core.log import log
from core.command_history import CommandHistory
from core.controllers.command_factory import summon
from core.services.confirm import ConfirmService
from core.services.schema import NodeSchema

class GlyphApp(App):
    CSS_PATH = "app.tcss"
    BINDINGS = [
        ("q", "quit", "Quit")
    ]
    pending_confirm: Optional[tuple] = None
    nodes: list[Node] = reactive([])


    def compose(self) -> ComposeResult:
        self.log_widget = RichLog(highlight=False, markup=True, id="log")
        self.input = Input(placeholder="Enter command (e.g. help, ls, save, load, tree, sample)", id="input")
        yield Vertical(self.log_widget, self.input)


    def on_mount(self):
        # --- CONFIG ---
        self.config = load_config()
        self.schema = NodeSchema(self.config["custom_schema"] if self.config["custom_schema"] else self.config["default_schema"])

        # --- DATA ---
        self.nodes = load_node_tree()

        # --- SERVICES ---
        self.confirm = ConfirmService(self)
        messages_path = self.config["paths"].get("messages", "loc/en/messages.json")
        self.message_catalog = MessageCatalog.from_file(messages_path)
        log.configure(writer=self.log_widget.write, catalog=self.message_catalog, debug=self.config.get("debug", False))
        log.configure_from_config(self.config)
        self.terminal_history = CommandHistory(self.config["command_history_maxlen"])

        # --- STARTUP ---
        autosave_state = "ON" if self.config.get("autosave") else "OFF"
        log.key("system.startup", version=self.config["version"], autosave=autosave_state)
        log.key("system.startup_hint")
        
        self.input.focus()


    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle command input from the user and execute corresponding actions."""
        self.schema = NodeSchema(self.config["custom_schema"] if self.config["custom_schema"] else self.config["default_schema"])

        self.mutated = False
        cmd = event.value.strip()
        self.input.value = ""
        log.key("system.cmd_input", cmd=cmd)
        self.terminal_history.add(cmd)

        if self.confirm.has_pending():
            if self.confirm.handle_response(cmd):
                return
        
        try:
            ccmd = summon(cmd, ctx=self.get_ctx())
        except Exception as e:
            log.error(str(e))
            return
        
        if ccmd is None:
            return
        else:
            ccmd.execute()


    async def on_key(self, event: events.Key) -> None:
        """Arrow history when the Input has focus."""
        if not self.input.has_focus:
            return
        if event.key == "up":
            prev = self.terminal_history.prev()
            if prev is not None:
                self.input.value = prev
                self.input.cursor_position = len(prev)
                event.prevent_default()
                event.stop()
        elif event.key == "down":
            nxt = self.terminal_history.next()
            if nxt is not None:
                self.input.value = nxt
                self.input.cursor_position = len(nxt)
                event.prevent_default()
                event.stop()



    def get_ctx(self):
        from core.context import Context
        return Context(
            app=self,
        )
    
    # 630