# Glyph.Flow

**Glyph.Flow** is a minimalist, keyboard-driven TUI workflow manager built with Python and [Textual](https://github.com/Textualize/textual).  
It allows you to define hierarchical structures such as projects, phases, tasks, and subtasks, and manage them directly from the terminal.

This is an early prototype (v0.1.0a1), mainly focused on backend data modeling and command parsing.

---

## 🔧 Features

- Universal tree structure based on a flexible `Node` class
- Unique hierarchical segmented ID generation for all nodes
- Type-checked schema (e.g. Project > Phase > Task > Subtask)
- JSON-based save/load of full node trees
- TUI-based test interface using `Textual`
- Command-based interaction for early testing: `create`, `delete`, `load`, `save`, etc.
- Rich output: tree view, table view, ASCII rendering
- Interactive confirmation for destructive operations



## 📂 File Structure
- node.py – Core Node class with hierarchy and progress logic
- node_schema.py – Enforces expected child types
- node_io.py – Load/save trees and generate sample data
- create_parser.py – Command-line argument parser for create
- backend_tester.py – Textual-based TUI frontend for testing

---

## 🧭 Roadmap Highlights
- Planned for future versions:
- toggle, edit, move, find commands
- TUI Features, Dashboard and statistics
- Undo support
- Enhanced error handling
- System log window

---

## 🛠 Status
This is an early preview. Not production ready yet.
For now, it serves as a foundation for future versions of Glyph.Flow.

---

## 🚀 Getting Started

### 📦 Requirements

- Python 3.10+
- `textual`, `rich`

Install dependencies:

```bash
pip install textual rich
python backend_tester.py
```

Use the input field to enter commands (see below).

- help                           # Print all available commands with examples
- sample                         # Generate a demo tree
- tree                           # Print indented tree view
- ascii                          # Print ASCII-style hierarchy
- table                          # Show nodes in table format
- save                           # Save tree to node_data.json
- load                           # Load tree from node_data.json
- ls                             # List root nodes
- create                         # Create node (e.g. create Task "Refactor Logic" --desc "Cleanup" --full "Split backend and UI" --parent 01.01)
- delete                         # Schedule deletion (e.g. delete 01.01.01)
- confirm                        # Confirm it (e.g. delete 01.01.01)
- abort delete                   # Cancel pending delete
- schema                         # Set a new node naming and/or hierarchy (e.g. schema Level1 Level2 Level3 Level4) (default=Project Phase Task Subtask)

Usage examples:
- sample → ls → table/tree/ascii
- create Project "name" → ls  → create Phase "name" → save
- sample → table → delete 01.01 → confirm delete 01.01 → table
- sample → table → toggle 01.01 → table
