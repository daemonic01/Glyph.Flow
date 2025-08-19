from textual.app import App, ComposeResult
from textual.widgets import Input, RichLog
from textual.containers import Vertical
from textual.reactive import reactive
from textual import events
from core.data_io import save_node_tree, load_node_tree, create_sample_tree
from core.node import Node
from typing import Optional
import shlex
from core.schema import NodeSchema
from core.parser import parse_create_args
from core.utils import toggle_all
from core.config_loader import load_config, save_config
from core.message_styler import MessageCatalog
from core.log import log
from core.command_history import CommandHistory


class GlyphApp(App):
    config = load_config()
    CSS_PATH = "app.tcss"
    BINDINGS = [
        ("q", "quit", "Quit")
    ]
    pending_confirm: Optional[tuple] = None
    schema = NodeSchema(["Project", "Phase", "Task", "Subtask"])
    nodes: list[Node] = reactive([])


    def compose(self) -> ComposeResult:
        self.log_widget = RichLog(highlight=False, markup=True, id="log")
        self.input = Input(placeholder="Enter command (e.g. help, ls, save, load, tree, sample)", id="input")
        yield Vertical(self.log_widget, self.input)


    def on_mount(self):
        messages_path = self.config["paths"].get("messages", "loc/en/messages.json")
        self.msg = MessageCatalog.from_file(messages_path)
        log.configure(writer=self.log_widget.write, catalog=self.msg, debug=self.config.get("debug", False))
        log.configure_from_config(self.config)
        self.history = CommandHistory(self.config["command_history_maxlen"])

        autosave_state = "ON" if self.config.get("autosave") else "OFF"
        log.key("system.startup", version=self.config["version"], autosave=autosave_state)
        log.key("system.startup_hint")
        
        self.input.focus()



    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle command input from the user and execute corresponding actions."""
        self.mutated = False
        cmd = event.value.strip()
        self.input.value = ""
        log.key("system.cmd_input", cmd=cmd)
        self.history.add(cmd)

        try:
            if cmd == "q" or cmd == "quit":
                log.close()
                self.exit()

            elif cmd == "sample":
                self.nodes = create_sample_tree()
                log.key("file.sample_tree_created")
                self.mutated = True

            elif cmd == "save":
                save_node_tree(self.nodes)

            elif cmd == "load":
                self.nodes = load_node_tree()

            elif cmd == "ls":
                if not self.nodes:
                    log.key("file.no_data")
                else:
                    self.log_widget.write("[bold cyan]Root nodes:")
                    for n in self.nodes:
                        self.log_widget.write(f"[white]- {n.name} ({n.type}, ID = {n.id})")

            elif cmd == "tree":
                if not self.nodes:
                    log.key("file.no_data")
                else:
                    self.log_widget.write("[bold cyan]Tree view:")
                    for n in self.nodes:
                        await self.print_node_recursive(n)
            
            elif cmd == "ascii":
                if not self.nodes:
                    log.key("file.no_data")
                else:
                    self.log_widget.write("[bold cyan]ASCII Tree View:")
                    for i, root in enumerate(self.nodes):
                        self.log_widget.write(f"[#2B9995]{root.name} ({root.type}, ID = {root.id})")
                        for j, child in enumerate(root.children):
                            is_last = (j == len(root.children) - 1)
                            await self.print_ascii_tree(child, "", is_last)

            elif cmd == "table":
                if not self.nodes:
                    log.key("file.no_data")
                else:
                    self.render_table_view()
            
            elif cmd == "clear":
                self.log_widget.clear()



            elif cmd.startswith("create"):
                try:
                    parts = shlex.split(cmd)

                    if len(parts) >= 2 and parts[1] == "--help":
                        log.help("Usage:")
                        log.help("  create <type> <name> [--desc \"...\"] [--full \"...\"] [--deadline YYYY-MM-DD] [--parent <id>]")
                        log.help("Example:")
                        log.help("  create Task \"Refactor\" --desc \"Cleanup\" --full \"Split\" --deadline 2025-08-12 --parent 01.01")
                        return
        
                    args = parse_create_args(parts)

                    new_node = Node(
                        name=args["name"],
                        type=args["type"],
                        short_desc=args["short_desc"],
                        full_desc=args["full_desc"],
                        deadline=args["deadline"]
                    )

                    if args["parent_id"]:
                        parent = self.find_node_by_id(args["parent_id"])
                        if parent:
                            if not self.schema.is_valid_child(parent, args["type"]):
                                expected = self.schema.get_expected_child_type(parent)
                                log.key("node.create_invalid", type=args['type'], parent_type=parent.type, expected=expected)
                                return

                            parent.add_child(new_node)
                            log.key("node.create_child", name=args['name'], parent_id=parent.id, id=new_node.id)
                            self.mutated = True
                        else:
                            log.key("node.create_parent_not_found", parent_id=args['parent_id'])
                    else:
                        if not self.schema.is_valid_child(None, args["type"]):
                            expected = self.schema.get_expected_child_type(None)
                            log.key("node.create_root_node_type_error", expected=expected, type=args['type'])
                            return

                        self.nodes.append(new_node)
                        log.key("node.create_root", name=args['name'], id=new_node.id)
                        self.mutated = True

                except Exception as e:
                    log.error(f"{e}")



            elif cmd.startswith("schema"):
                parts = shlex.split(cmd)
                if len(parts) < 2:
                    log.help("Usage: schema Project Phase Task Subtask")
                else:
                    new_hierarchy = parts[1:]
                    if not self.nodes:
                        self.schema = NodeSchema(new_hierarchy)
                        log.key("schema.set_success", schema=' > '.join(new_hierarchy))
                    else:
                        try:
                            for root in self.nodes:
                                depth = self.schema.validate_tree_depth(root)
                                if depth != len(new_hierarchy):
                                    log.key("schema.depth_error", depth=depth, new_depth=len(new_hierarchy))
                                    return
                                
                            for root in self.nodes:
                                NodeSchema(new_hierarchy).relabel_tree_to_match(root)

                            self.schema = NodeSchema(new_hierarchy)
                            log.key("schema.switch_success", schema=' > '.join(new_hierarchy))
                            self.mutated = True
                        except Exception as e:
                            log.key("schema.error", error=e)
                
            
            elif cmd.startswith("delete"):
                parts = shlex.split(cmd)
                if len(parts) < 2:
                    log.help("Usage: delete <id>")
                    return

                target_id = parts[1]
                target = self.find_node_by_id(target_id)
                if not target:
                    log.key("node.node_not_found", id=target_id)
                    return

                log.key("confirmation.delete_confirm", target_name=target.name, target_id=target.id)
                self.pending_confirm = ("delete", target)

            elif cmd.startswith("clearall"):
                parts = shlex.split(cmd)

                if len(parts) >= 2 and parts[1] == "--help":
                    log.help("Usage:")
                    log.help("  clearall mem    # Clear all nodes from memory")
                    log.help("  clearall file   # Delete saved data file (node_data.json)")
                    log.help("  clearall both   # Clear memory and delete file")
                    return

                if len(parts) < 2 or parts[1] not in ("mem", "file", "both"):
                    log.help("Usage: clearall <mem|file|both>")
                    return

                action = parts[1]

                if not self.pending_confirm:
                    self.log_widget.write(
                        f"[yellow]Are you sure you want to clear '{action}'? "
                        f"Type: 'confirm clearall {action}' or 'abort clearall' to cancel."
                    )
                    self.pending_confirm = ("clearall", action)
                    return

            elif cmd.startswith("confirm"):
                parts = shlex.split(cmd)
                if len(parts) < 3:
                    log.help("Usage: confirm delete <id>")
                    return

                action = parts[1]
                target_id = parts[2]

                if self.pending_confirm and self.pending_confirm[0] == "delete":
                    target = self.pending_confirm[1]
                    if target.id != target_id:
                        log.key("confirmation.mismatched_id", targets_id=target.id, target_id=target_id)
                        return

                    if target.parent:
                        target.parent.children = [c for c in target.parent.children if c.id != target.id]
                        log.key("node.delete_done", target_name=target.name, target_id=target.id, target_parent_id=target.parent.id)
                        self.mutated = True
                    else:
                        self.nodes = [n for n in self.nodes if n.id != target.id]
                        log.key("node.delete_root_done", target_name=target.name, target_id=target.id)
                        self.mutated = True

                    self.pending_confirm = None
                    return


                if self.pending_confirm and self.pending_confirm[0] == "clearall":
                    from core.data_io import delete_data_file
                    target = self.pending_confirm[1]

                    if target == "mem":
                        self.nodes.clear()
                        log.key("clearall.in_memory_done")
                    elif target == "file":
                        deleted = delete_data_file()
                        if deleted:
                            log.key("clearall.data_file_done")
                            self.mutated = True
                        else:
                            log.key("clearall.file_not_found")
                    elif target == "both":
                        self.nodes.clear()
                        deleted = delete_data_file()
                        if deleted:
                            log.key("both_done")
                        else:
                            log.key("both_mem_done")
                        self.mutated = True

                    self.pending_confirm = None
                    return
                
                else:
                    log.key("confirmation.no_pending_confirm")



            elif cmd.startswith("abort"):
                parts = shlex.split(cmd)
                if len(parts) < 2:
                    log.help("Usage: abort <delete|clearall>")
                    return

                action = parts[1]

                if action == "delete":
                    if self.pending_confirm and self.pending_confirm[0] == "delete":
                        log.key("abort.delete_aborted", target=self.pending_confirm[1].name)
                        self.pending_confirm = None
                    else:
                        log.key("abort.no_pending_delete")

                elif action == "clearall":
                    if self.pending_confirm and self.pending_confirm[0] == "clearall":
                        target = self.pending_confirm[1]  # string: mem/file/both
                        log.key("abort.clearall_aborted", target=target)
                        self.pending_confirm = None
                    else:
                        log.key("abort.no_pending_clearall")

                else:
                    log.key("abort.unknown_target_action", action=action)




            elif cmd.startswith("toggle"):
                parts = shlex.split(cmd)

                if len(parts) < 2:
                    log.help("Usage: toggle <id>")
                    return

                target_id = parts[1]
                target = self.find_node_by_id(target_id)
                if not target:
                    log.key("node.node_not_found", id=target_id)
                    return

                old_status = target.completed
                toggle_all(target)
                new_status = target.completed

                log.key("node.toggled", target_name=target.name, old_status=old_status, new_status=new_status)
                self.mutated = True



            elif cmd.startswith("edit"):
                try:
                    parts = shlex.split(cmd)

                    if len(parts) >= 2 and parts[1] == "--help":
                        log.help("[cyan]Usage:")
                        log.help("  edit <id> [--name \"...\"] [--desc \"...\"] [--full \"...\"] [--deadline YYYY-MM-DD]")
                        log.help("Example:")
                        log.help("  edit 01.02 --name \"New Name\" --desc \"Short\" --full \"Detailed\" --deadline 2025-08-15")
                        self.mutated = True

                    from core.parser import parse_edit_args
                    args = parse_edit_args(parts)

                    node = self.find_node_by_id(args["id"])
                    if not node:
                        log.key("node.node_not_found", id=args['id'])
                        return

                    changes = []
                    if args["name"]:
                        node.name = args["name"]
                        changes.append(f"name → '{args['name']}'")
                    if args["short_desc"]:
                        node.short_desc = args["short_desc"]
                        changes.append(f"short_desc → '{args['short_desc']}'")
                    if args["full_desc"]:
                        node.full_desc = args["full_desc"]
                        changes.append(f"full_desc → '{args['full_desc']}'")
                    if args["deadline"]:
                        node.deadline = args["deadline"]
                        changes.append(f"deadline → {args['deadline']}")

                    if changes:
                        info = ", ".join(changes)
                        log.key("node.edit_done", id=node.id, info=info)
                        self.mutated = True
                    else:
                        log.key("node.edit_no_change", id=node.id)

                except Exception as e:
                    log.error(f"{e}")

            

            elif cmd.startswith("search"):
                try:
                    parts = shlex.split(cmd)

                    if len(parts) >= 2 and parts[1] == "--help":
                        self.log_widget.write("[cyan]Usage:")
                        self.log_widget.write("  search <substring>")
                        self.log_widget.write("  search name <substring>")
                        self.log_widget.write("  search id <prefix-or-exact>")
                        return

                    from core.parser import parse_search_args
                    args = parse_search_args(parts)

                    matches = []
                    if args["mode"] == "id":
                        q = args["query"]
                        for n in self.iter_nodes():
                            if n.id == q or n.id.startswith(q):
                                matches.append(n)
                    else:  # name
                        q = args["query"].lower()
                        for n in self.iter_nodes():
                            if q in n.name.lower():
                                matches.append(n)

                    if not matches:
                        if not self.nodes:
                            log.key("file.no_data")
                            return
                        else:
                            log.key("node.search_no_matches")
                            return

                    from rich.table import Table
                    table = Table(show_header=True, header_style="bold cyan")
                    table.add_column("ID", style="bold", width=12)
                    table.add_column("Name", style="white")
                    table.add_column("Type", style="cyan", width=10)
                    table.add_column("Ready", style="green", width=6)
                    table.add_column("Deadline", style="white", width=12)

                    for n in matches:
                        ready = "[X]" if n.completed else "[ ]"
                        deadline = n.deadline if n.deadline else "-"
                        table.add_row(n.id, n.name, n.type, ready, deadline)

                    log.key("node.search_results", nmatches=len(matches))
                    self.log_widget.write(table)

                except Exception as e:
                    log.error(f"{e}")


            elif cmd.startswith("autosave"):
                parts = shlex.split(cmd)

                if len(parts) >= 2 and parts[1] == "--help" or len(parts) == 1:
                    log.help("Usage: autosave <on/off>")
                    return
                
                if parts[1] not in ("on", "off"):
                    log.key("system.autosave_invalid_state")
                    return
                
                if parts[1] == "on":
                    self.config["autosave"] = True
                else:
                    self.config["autosave"] = False
                save_config(self.config)
                log.key("system.autosave_changed", state=parts[1])
                    
                
                



            elif cmd == "help":
                from core.data_io import load_help_text
                for line in load_help_text():
                    self.log_widget.write(line)

            else:
                log.key("system.unknown_command", cmd=cmd)


        finally:
            if self.mutated and self.config["autosave"]:
                try:
                    save_node_tree(self.nodes)
                    log.key("system.autosave_done")
                except Exception as e:
                    log.key("system.autosave_failed", error=e)


    async def on_key(self, event: events.Key) -> None:
        """Arrow history when the Input has focus."""
        if not self.input.has_focus:
            return
        if event.key == "up":
            prev = self.history.prev()
            if prev is not None:
                self.input.value = prev
                self.input.cursor_position = len(prev)
                event.prevent_default()
                event.stop()
        elif event.key == "down":
            nxt = self.history.next()
            if nxt is not None:
                self.input.value = nxt
                self.input.cursor_position = len(nxt)
                event.prevent_default()
                event.stop()


    async def print_node_recursive(self, node: Node, indent: int = 0, delay: float = 0.05):
        """Print the tree view recursively in indented format with optional delay."""
        from asyncio import sleep
        status = "[X]" if node.completed else "[ ]"

        if indent == 0:
            color = "#2B9995"
        elif indent == 1:
            color = "#2AA7A2"
        elif indent == 2:
            color = "#71DDD9"
        else:
            color = "#C9F0EF"

        line = f"[{color}]{status} {node.name} ({node.type}, ID = {node.id})[/{color}]"
        self.log_widget.write("  " * indent + line)
        await sleep(delay)
        for child in node.children:
            await self.print_node_recursive(child, indent + 1)

    
    async def print_ascii_tree(self, node: Node, prefix: str = "", is_last: bool = True, level: int = 1, delay: float = 0.05):
        """Render an ASCII branch view of the tree recursively."""
        from asyncio import sleep
        connector = "└── " if is_last else "├── "

        if level == 0:
            color = "#2B9995"
        elif level == 1:
            color = "#2AA7A2"
        elif level == 2:
            color = "#71DDD9"
        else:
            color = "#C9F0EF"

        line = f"{prefix}{connector}[{color}]{node.name} ({node.type}, ID = {node.id})[/{color}]"
        self.log_widget.write(line)
        await sleep(delay)

        new_prefix = prefix + ("    " if is_last else "│   ")
        for i, child in enumerate(node.children):
            is_last_child = (i == len(node.children) - 1)
            await self.print_ascii_tree(child, new_prefix, is_last_child, level + 1)
            



    def find_node_by_id(self, target_id: str) -> Optional[Node]:
        """Find a node in the entire tree by its ID."""
        for root in self.nodes:
            result = self._search_recursive(root, target_id)
            if result:
                return result
        return None

    def _search_recursive(self, node: Node, target_id: str) -> Optional[Node]:
        if node.id == target_id:
            return node
        for child in node.children:
            result = self._search_recursive(child, target_id)
            if result:
                return result
        return None
    
    def render_table_view(self):
        """Render a table view of all nodes in the tree using Rich Table."""
        from rich.table import Table

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("ID", style="bold", width=12)
        table.add_column("Name", style="white", no_wrap=True)
        table.add_column("Type", style="cyan", width=10)
        table.add_column("Created", style="white", width=12)
        table.add_column("Deadline", style="magenta", width=12)
        table.add_column("Ready", style="green", width=6)
        table.add_column("Short description", style="dim", max_width=30)
        table.add_column("Full description", style="dim", max_width=50)

        for root in self.nodes:
            self._add_node_to_table(root, table)

        self.log_widget.write("[bold cyan]Table view:")
        self.log_widget.write(table)

    def _add_node_to_table(self, node: Node, table):
        """Helper function to add nodes/rows to tables."""
        status = "[X]" if node.completed else "[ ]"
        table.add_row(
            node.id,
            node.name,
            node.type,
            node.created_at,
            node.deadline if node.deadline else "-",
            status,
            node.short_desc or "-",
            node.full_desc or "-"
        )
        for child in node.children:
            self._add_node_to_table(child, table)


    def iter_nodes(self):
        """Helper function for iterating through nodes recursively."""
        for root in self.nodes:
            yield from self._iter_nodes_recursive(root)

    def _iter_nodes_recursive(self, node):
        yield node
        for child in node.children:
            yield from self._iter_nodes_recursive(child)
