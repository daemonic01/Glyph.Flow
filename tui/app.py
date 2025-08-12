from textual.app import App, ComposeResult
from textual.widgets import Input, RichLog
from textual.containers import Vertical
from textual.reactive import reactive
from core.data_io import save_node_tree, load_node_tree, create_sample_tree
from core.node import Node
from typing import Optional
import shlex
from core.schema import NodeSchema
from core.parser import parse_create_args
from core.utils import toggle_all


class NodeTestApp(App):
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
        self.log_widget.write("[bold green]Node test environment initialized.")
        self.log_widget.write("Type 'help' to see all commands. Type 'sample' to generate a demo tree.")
        self.input.focus()


    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle command input from the user and execute corresponding actions."""
        cmd = event.value.strip()
        self.input.value = ""
        self.log_widget.write(f"[bold magenta]> {cmd}")

        if cmd == "q" or cmd == "quit":
            self.exit()

        elif cmd == "sample":
            self.nodes = create_sample_tree()
            self.log_widget.write("[green]Sample tree created.")

        elif cmd == "save":
            save_node_tree(self.nodes)
            self.log_widget.write("[green]Data saved to 'node_data.json'.")

        elif cmd == "load":
            self.nodes = load_node_tree()
            self.log_widget.write("[green]Data loaded from 'node_data.json'.")

        elif cmd == "ls":
            if not self.nodes:
                self.log_widget.write("[yellow]No data loaded.")
            else:
                self.log_widget.write("[bold cyan]Root nodes:")
                for n in self.nodes:
                    self.log_widget.write(f"[white]- {n.name} ({n.type}, ID = {n.id})")

        elif cmd == "tree":
            if not self.nodes:
                self.log_widget.write("[yellow]No data loaded.")
            else:
                self.log_widget.write("[bold cyan]Tree view:")
                for n in self.nodes:
                    await self.print_node_recursive(n)
        
        elif cmd == "ascii":
            if not self.nodes:
                self.log_widget.write("[yellow]No data loaded.")
            else:
                self.log_widget.write("[bold cyan]ASCII Tree View:")
                for i, root in enumerate(self.nodes):
                    self.log_widget.write(f"[#2B9995]{root.name} ({root.type}, ID = {root.id})")
                    for j, child in enumerate(root.children):
                        is_last = (j == len(root.children) - 1)
                        await self.print_ascii_tree(child, "", is_last)

        elif cmd == "table":
            if not self.nodes:
                self.log_widget.write("[yellow]No data loaded.")
            else:
                self.render_table_view()
        
        elif cmd == "clear":
            self.log_widget.clear()



        elif cmd.startswith("create"):
            try:
                parts = shlex.split(cmd)

                if len(parts) >= 2 and parts[1] == "--help":
                    self.log_widget.write("[cyan]Usage:")
                    self.log_widget.write("  create <type> <name> [--desc \"...\"] [--full \"...\"] [--deadline YYYY-MM-DD] [--parent <id>]")
                    self.log_widget.write("Example:")
                    self.log_widget.write("  create Task \"Refactor\" --desc \"Cleanup\" --full \"Split\" --deadline 2025-08-12 --parent 01.01")
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
                            self.log_widget.write(
                                f"[red]Invalid type: cannot create '{args['type']}' under '{parent.type}' "
                                f"(expected: '{expected}')"
                            )
                            return

                        parent.add_child(new_node)
                        self.log_widget.write(f"[green]Added '{args['name']}' under {parent.id} → New ID: {new_node.id}")
                    else:
                        self.log_widget.write(f"[red]Parent ID '{args['parent_id']}' not found.")
                else:
                    if not self.schema.is_valid_child(None, args["type"]):
                        expected = self.schema.get_expected_child_type(None)
                        self.log_widget.write(f"[red]Root node must be of type '{expected}', not '{args['type']}'")
                        return

                    self.nodes.append(new_node)
                    self.log_widget.write(f"[green]Created root node: {args['name']} → ID: {new_node.id}")

            except Exception as e:
                self.log_widget.write(f"[red]Error: {e}")



        elif cmd.startswith("schema"):
            parts = shlex.split(cmd)
            if len(parts) < 2:
                self.log_widget.write("[red]Usage: schema Project Phase Task Subtask")
            else:
                new_hierarchy = parts[1:]
                if not self.nodes:
                    self.schema = NodeSchema(new_hierarchy)
                    self.log_widget.write(f"[cyan]Schema set to: {' > '.join(new_hierarchy)} (no data to update)")
                else:
                    try:
                        for root in self.nodes:
                            depth = self.schema.validate_tree_depth(root)
                            if depth != len(new_hierarchy):
                                self.log_widget.write(
                                    f"[red]Cannot switch schema: current tree depth = {depth}, new schema = {len(new_hierarchy)}"
                                )
                                return
                            
                        for root in self.nodes:
                            NodeSchema(new_hierarchy).relabel_tree_to_match(root)

                        self.schema = NodeSchema(new_hierarchy)
                        self.log_widget.write(f"[green]Schema switched and node types updated to: {' > '.join(new_hierarchy)}")
                    except Exception as e:
                        self.log_widget.write(f"[red]Schema change error: {e}")
            
        
        elif cmd.startswith("delete"):
            parts = shlex.split(cmd)
            if len(parts) < 2:
                self.log_widget.write("[red]Usage: delete <id>")
                return

            target_id = parts[1]
            target = self.find_node_by_id(target_id)
            if not target:
                self.log_widget.write(f"[red]Node with ID '{target_id}' not found.")
                return

            self.log_widget.write(
                f"[yellow]Are you sure you want to delete '{target.name}' (ID: {target.id})?"
                f" Type: 'confirm delete {target.id}' or 'abort delete' to cancel operation."
            )
            self.pending_confirm = ("delete", target)

        elif cmd.startswith("confirm"):
            parts = shlex.split(cmd)
            if len(parts) < 3:
                self.log_widget.write("[red]Usage: confirm delete <id>")
                return

            action = parts[1]
            target_id = parts[2]

            if self.pending_confirm and self.pending_confirm[0] == "delete":
                target = self.pending_confirm[1]
                if target.id != target_id:
                    self.log_widget.write(f"[red]Mismatched confirmation ID. Pending: {target.id}, got: {target_id}")
                    return

                if target.parent:
                    target.parent.children = [c for c in target.parent.children if c.id != target.id]
                    self.log_widget.write(f"[green]Deleted node '{target.name}' (ID: {target.id}) from parent {target.parent.id}")
                else:
                    self.nodes = [n for n in self.nodes if n.id != target.id]
                    self.log_widget.write(f"[green]Deleted root node '{target.name}' (ID: {target.id})")

                self.pending_confirm = None

            else:
                self.log_widget.write("[red]No delete operation pending confirmation.")

        elif cmd.startswith("abort"):
            parts = shlex.split(cmd)
            if len(parts) < 2:
                self.log_widget.write("[red]Usage: abort delete")
                return

            action = parts[1]
            if action == "delete" and self.pending_confirm and self.pending_confirm[0] == "delete":
                self.log_widget.write(f"[cyan]Delete of '{self.pending_confirm[1].name}' aborted.")
                self.pending_confirm = None
            else:
                self.log_widget.write("[yellow]No delete operation to abort.")


        elif cmd.startswith("toggle"):
            parts = shlex.split(cmd)

            if len(parts) < 2:
                self.log_widget.write("[red]Usage: toggle <id>")
                return

            target_id = parts[1]
            target = self.find_node_by_id(target_id)
            if not target:
                self.log_widget.write(f"[red]Node with ID '{target_id}' not found.")
                return

            old_status = target.completed
            toggle_all(target)
            new_status = target.completed

            self.log_widget.write(f"[green]Toggled '{target.name}' and all descendants from {old_status} to {new_status}.")


        elif cmd == "help":
            self.log_widget.write("[white]Entries are identified by segmented IDs. Each internal level has an ID that is one segment longer. (00, 00.00, 00.00.00, etc.)")
            self.log_widget.write("[white]By default, there are 4 levels available: Project, Phase, Task, and Subtask.")
            self.log_widget.write("[white]Every command that requires a specific entry uses its ID.\n")


            self.log_widget.write("[bold cyan]Available Commands:\n")

            self.log_widget.write("[bold]🛠 Structure")
            self.log_widget.write("[bold white]  create <type> <name> [--desc] [--full] [--deadline] [--parent <id>]")
            self.log_widget.write("    Create a new node (Project, Phase, Task, Subtask)")
            self.log_widget.write("[dim]    Example: create Task \"Fix Logic\" --desc \"Bugfix\" --parent 01.02\n")

            self.log_widget.write("[bold white]  delete <id>")
            self.log_widget.write("    Schedule deletion of a node (requires confirm)")
            self.log_widget.write("[dim]    Example: delete 01.01\n")

            self.log_widget.write("[bold white]  confirm delete <id>")
            self.log_widget.write("    Confirm a previously requested deletion\n")

            self.log_widget.write("[bold white]  abort delete")
            self.log_widget.write("    Cancel a pending deletion\n")

            self.log_widget.write("[bold white]  schema <type1> <type2> ...")
            self.log_widget.write("    Change hierarchy schema")
            self.log_widget.write("[dim]    Example: schema Level1 Level2 Level3   Default: Project Phase Task Subtask")
            self.log_widget.write("[white]    Changing the schema with existing data is only possible if the length of the new schema specified is the same as the old one.\n")

            self.log_widget.write("[bold white]  toggle <id>")
            self.log_widget.write("    Toggle a node and all its children between done/undone")
            self.log_widget.write("[dim]    Example: toggle 01.02\n")

            self.log_widget.write("[bold]📄 Display")
            self.log_widget.write("[bold white]  ls           List root nodes")
            self.log_widget.write("[bold white]  tree         Print full tree view (indented format)")
            self.log_widget.write("[bold white]  ascii        ASCII-style tree branches")
            self.log_widget.write("[bold white]  table        Tabular view of all nodes")
            self.log_widget.write("[bold white]  clear        Clear the log\n")

            self.log_widget.write("[bold]💾 File I/O")
            self.log_widget.write("[bold white]  save         Save to 'node_data.json'")
            self.log_widget.write("[bold white]  load         Load from 'node_data.json'")
            self.log_widget.write("[bold white]  sample       Generate a sample node tree\n")

            self.log_widget.write("[bold]🧪 Misc")
            self.log_widget.write("[bold white]  help         Show this help message\n")

            self.log_widget.write("[bold]🚪 Exit")
            self.log_widget.write("[bold white]  q / quit     Exit the application\n")

            self.log_widget.write("Automatic saving and loading is not yet part of the functionality. Use the 'save' and 'load' commands.")
            self.log_widget.write("Use the 'sample' command to create sample data, then view the result with one of the display commands.\n")

        else:
            self.log_widget.write(f"[red]Unknown command: {cmd}")



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

        self.log_widget.write("[bold cyan]Táblázatos nézet:")
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