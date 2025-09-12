from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Input, RichLog, Label, Rule, Static
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
from pathlib import Path

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
        ("a", "adjust", "Adjust"),
        ("t", "switch_theme", "switch Theme")
    ]
    pending_confirm: Optional[tuple] = None
    nodes: list[Node] = reactive([])


    def compose(self) -> ComposeResult:

        image_map = {
            "crimson": "assets/images/gf_art.png",
            "arctic":  "assets/images/gf_art_arctic.png",
            "desert":  "assets/images/gf_art_desert.png",
            "*":       "assets/images/gf_art.png",
        }
        default_theme = self.config.get("theme", "crimson")

        self.output_focus = False

        # prepare environment info box labels
        self.version_label = Label("", classes="InfoLabel")
        self.autosave_label = Label("", classes="InfoLabel")
        self.logging_label = Label("", classes="InfoLabel")

        # prepare project info box labels
        self.project_count_label = Label("", classes="DataInfoLabel")
        self.project_status_label = Label("", classes="DataInfoLabel")

        self.header = Horizontal(
            Container(
                self.version_label,
                self.autosave_label,
                self.logging_label,
                id="info-box"
            ),
            GlyphArt(image_map, default_theme=default_theme, art_size=(100, 18)),
            Container(
                self.project_count_label,
                self.project_status_label,
                id="data-info-box"
            ),
            id="header")

        self.log_widget = GlyphRichLog(highlight=False, markup=True, id="log", wrap=True, min_width=25)
        self.log_widget.border_title = "MESSAGE LOG"
        self.output_widget = GlyphRichLog(highlight=False, markup=True, id="output-log", wrap=True, min_width=25)
        self.output_widget.border_title = "OUTPUT PANEL"
        self.input = Input(placeholder="Enter command (e.g. help, create, ls, save, tree, sample, config)", id="input")
        self.footer = Static("A = Adjust Panels | T = Switch Theme", id="footer", markup=False)

        self.footer_container = Container(
            self.input,
            Rule(line_style="solid"),
            self.footer, id="footer-container"
            
        )
        yield Vertical(self.header,
                       Rule(line_style="double"),
                       Horizontal(self.log_widget, self.output_widget),
                       self.footer_container
                       )
        
    def on_mount(self):
        # --- CONFIG ---
        self.ctx = GlyphNexus()

        # --- SERVICES ---
        messages_path = self.ctx.config.get("paths.messages", "loc/en/messages.json", str)
        self.message_catalog = MessageCatalog.from_file(messages_path)
        self.confirm = ConfirmService(ctx=self.ctx)
        self.ctx.bind_app_core(app=self.app)

        # --- THEME ---
        self.apply_theme_from_json(self.ctx.base_dir / f"tui/palettes/{self.ctx.config.get("theme")}.json")

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
        self.refresh_data_info_box()
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

    
    
    def action_switch_theme(self) -> None:
        if self.ctx.config.get("theme") == "crimson":
            self.ctx.config.edit("theme", "arctic")
        elif self.ctx.config.get("theme") == "arctic":
            self.ctx.config.edit("theme", "desert")
        else:
            self.ctx.config.edit("theme", "crimson")
        self.apply_theme_from_json(self.ctx.base_dir / f"tui/palettes/{self.ctx.config.get("theme")}.json")
        try:
            self.query_one("#gf-logo", GlyphArt).theme_name = self.ctx.config.get("theme")
        except Exception:
            pass

        self.refresh_css()
        self.screen.refresh()


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

    def refresh_data_info_box(self):
        self.project_count_label.update(f"Active projects: {len(self.ctx.app.nodes)}")
        completed_count = len([p for p in self.ctx.app.nodes if p.completed])
        self.project_status_label.update(f"In progress: {len(self.ctx.app.nodes) - completed_count} | Done: {completed_count}")



    def apply_theme_from_json(app, json_path: str | Path) -> None:
        import json
        from pathlib import Path
        from textual.theme import Theme
        data = json.loads(Path(json_path).read_text(encoding="utf-8"))
        colors = data.get("colors", {})

        theme = Theme(
            name=data.get("name", "custom"),
            dark=bool(data.get("dark", True)),
            primary=colors.get("primary"),
            secondary=colors.get("secondary"),
            accent=colors.get("accent"),
            foreground=colors.get("foreground"),
            background=colors.get("background"),
            surface=colors.get("surface"),
            panel=colors.get("panel"),
            success=colors.get("success"),
            warning=colors.get("warning"),
            error=colors.get("error"),
            boost=colors.get("boost"),
            variables=data.get("variables") or {},
        )
        app.register_theme(theme)
        app.theme = theme.name 