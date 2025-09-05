from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Input, RichLog, Label, Rule
from textual.containers import Vertical, Horizontal
from textual.reactive import reactive
from textual import events
from core.data_io import load_node_tree
from core.node import Node
from typing import Optional
from core.message_styler import MessageCatalog
from core.log import _Log
from core.command_history import CommandHistory
from core.controllers.command_factory import summon
from core.services.confirm import ConfirmService
from asyncio import get_running_loop
from time import sleep as time_sleep
from .gf_art import GlyphArt
from core.config.config_vault import ConfigVault
from core.glyph_nexus import GlyphNexus

class GlyphRichLog(RichLog):
    def __init__(self, *args, buffer_cap=100, **kwargs):
        super().__init__(*args, **kwargs)
        self._buffer: list[tuple[tuple, dict]] = []
        self._buffer_cap = buffer_cap
        self._replaying = False

    def write(self, *args, **kwargs):
        if not self._replaying:
            self._buffer.append((args, kwargs.copy()))
            if self._buffer_cap and len(self._buffer) > self._buffer_cap:
                self._buffer = self._buffer[-self._buffer_cap:]
        return super().write(*args, **kwargs)

    def reflow(self):
        self._replaying = True
        try:
            self.clear()
            for args, kwargs in self._buffer:
                super().write(*args, **kwargs)
        finally:
            self._replaying = False

    def on_resize(self):
        self.reflow()



class GlyphApp(App):
    config = ConfigVault()
    CSS_PATH = "app.tcss"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("a", "adjust", "Adjust")
    ]
    pending_confirm: Optional[tuple] = None
    nodes: list[Node] = reactive([])

    

    def compose(self) -> ComposeResult:
        self.output_focus = False

        self.version_label = Label("", classes="InfoLabel")
        self.autosave_label = Label("", classes="InfoLabel")
        self.logging_label = Label("", classes="InfoLabel")

        self.header = Horizontal(
            Container(
                self.version_label,
                self.autosave_label,
                self.logging_label,
                id="info-box"
            ),
            GlyphArt(image_path="assets/images/gf_art.png"),
            Container(),
            id="header")

        self.log_widget = GlyphRichLog(highlight=False, markup=True, id="log", wrap=True, min_width=25)
        self.log_widget.border_title = "MESSAGE LOG"
        self.output_widget = GlyphRichLog(highlight=False, markup=True, id="output-log", wrap=True, min_width=25)
        self.output_widget.border_title = "OUTPUT PANEL"
        self.input = Input(placeholder="Enter command (e.g. help, create, ls, save, tree, sample, config)", id="input")
        yield Vertical(self.header,
                       Rule(line_style="double"),
                       Horizontal(self.log_widget, self.output_widget),
                       self.input, id="TUI")

    def on_mount(self):
        # --- CONFIG ---
        self.ctx = GlyphNexus()

        # --- SERVICES ---
        messages_path = self.ctx.config.get("paths.messages", "loc/en/messages.json", str)
        self.message_catalog = MessageCatalog.from_file(messages_path)
        self.confirm = ConfirmService(ctx=self.ctx)
        self.ctx.bind_app_core(app=self.app)

        # --- UI ---
        self.message_log = _Log(config=self.config)
        self.message_log.configure(writer=self.log_widget.write, catalog=self.message_catalog, debug=self.config.get("debug", False))
        self.message_log.configure_from_config(self.config)
        self.presenter = _Log(config=self.config)
        self.presenter.configure(writer=self.output_widget.write, catalog=self.message_catalog, debug=self.config.get("debug", False))
        self.terminal_history = CommandHistory(self.config.get("command_history_maxlen"))
        self.ctx.bind_ui()

        # --- DATA ---
        self.nodes = load_node_tree(self.ctx) or []

        # --- STARTUP ---
        self.refresh_header_from_config()
        self.call_after_refresh(
        lambda: (
            self.ctx.log.key("system.startup_hint")
            )
        )

        
        self.input.focus()


    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle command input from the user and execute corresponding actions."""
        self.mutated = False
        cmd = event.value.strip()
        self.input.value = ""
        self.ctx.log.key("system.cmd_input", cmd=cmd)
        self.terminal_history.add(cmd)

        if self.confirm.has_pending():
            if self.confirm.handle_response(cmd):
                return
        
        try:
            ccmd = summon(cmd, ctx=self.ctx)
        except Exception as e:
            self.ctx.log.error(str(e))
            return
        
        if ccmd is None:
            return
        else:
            ccmd.execute()
            self.ctx.config.reload()
            self.refresh_header_from_config()



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
        """Create a Context object with the configuration data already loaded and passing in the necessary widgets."""
        return Context(
            app=self,
        )



    async def action_adjust(self) -> None:
        """Adjust the width of the left (log_widget) and right (output_widget) log panels."""
        if not self.output_focus:

            self.log_widget.styles.animate("opacity", 0.0, duration=0.25, easing="in_out_cubic")
            self.output_widget.styles.animate("opacity", 0.0, duration=0.25, easing="in_out_cubic")
            await get_running_loop().run_in_executor(None, time_sleep, 0.25)

            self.log_widget.styles.width = "30%"
            self.output_widget.styles.width = "70%"


            self.log_widget.styles.animate("opacity", 1.0, duration=0.25, easing="in_out_cubic")
            self.output_widget.styles.animate("opacity", 1.0, duration=0.25, easing="in_out_cubic")

            self.output_focus = True
        else:
            self.log_widget.styles.animate("opacity", 0.0, duration=0.25, easing="in_out_cubic")
            self.output_widget.styles.animate("opacity", 0.0, duration=0.25, easing="in_out_cubic")
            await get_running_loop().run_in_executor(None, time_sleep, 0.25)

            self.log_widget.styles.width = "50%"
            self.output_widget.styles.width = "50%"


            self.log_widget.styles.animate("opacity", 1.0, duration=0.25, easing="in_out_cubic")
            self.output_widget.styles.animate("opacity", 1.0, duration=0.25, easing="in_out_cubic")

            self.output_focus = False

    def refresh_header_from_config(self) -> None:
        self.version_label.update(f"Active version: {self.ctx.config.get('version', 'unknown')}")
        self.autosave_label.update(f"Autosave: {'ON' if self.ctx.config.get('autosave') else 'OFF'}")
        self.logging_label.update(f"Logging: {'ON' if self.ctx.config.get('logging') else 'OFF'}")