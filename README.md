# Glyph.Flow

**Glyph.Flow** is a minimalist, keyboard-driven TUI workflow manager built with Python and [Textual](https://github.com/Textualize/textual).  
It allows you to define hierarchical structures such as projects, phases, tasks, and subtasks, and manage them directly from the terminal.

This is an early prototype (v0.1.0a2), mainly focused on backend data modeling and command parsing.

---

## 🔧 Features

- Universal tree structure based on a flexible `Node` class
- Unique hierarchical segmented ID generation for all nodes
- Type-checked schema (e.g. Project > Phase > Task > Subtask)
- JSON-based save/load of full node trees
- TUI-based test interface using `Textual`
- Command-based interaction for early testing: `create`, `edit`, `delete`, `search`, `clearall`, `load`, `save`, etc.
- Rich output: tree view, table view, ASCII rendering
- Interactive confirmation for destructive operations (`delete`, `clearall`)
- Help text loaded from external file for easier maintenance

---

## 📂 File Structure
- `node.py` – Core Node class with hierarchy and progress logic
- `schema.py` – Enforces expected child types
- `data_io.py` – Load/save trees and generate sample data
- `parser.py` – Command-line argument parsers for various commands
- `app.py` – Textual-based TUI frontend for testing

---

## 🧭 Roadmap Highlights
- Planned for future versions:
  - Advanced `search` filters (by type, regex, etc.)
  - Detailed TUI interface with main menu, project view, settings, and changelog
  - Undo support
  - Enhanced error handling
  - TUI Features, Dashboard and statistics

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
python app.py
```

Use the input field to enter commands (see below).

---

### 💻 Commands

#### Core
- `help`                          – Print all available commands with examples (loaded from external file)
- `sample`                        – Generate a demo tree
- `ls`                            – List root nodes
- `tree`                          – Print indented tree view
- `ascii`                         – Print ASCII-style hierarchy
- `table`                         – Show nodes in table format
- `save`                          – Save tree to `node_data.json`
- `load`                          – Load tree from `node_data.json`
- `schema`                        – Set a new node hierarchy (e.g. `schema Level1 Level2 Level3 Level4`)

#### Node Management
- `create`                        – Create node (e.g. `create Task "Refactor Logic" --desc "Cleanup" --full "Split backend and UI" --parent 01.01`)
- `edit`                          – Edit an existing node (e.g. `edit 01.02 --name "New Name" --desc "Short" --full "Detailed" --deadline 2025-08-15`)
- `delete`                        – Schedule deletion (e.g. `delete 01.01.01`)
- `confirm delete <id>`           – Confirm a pending delete
- `abort delete`                  – Cancel pending delete

#### Search & Filters
- `search <substring>`            – Search by name (case-insensitive)
- `search name <substring>`       – Explicit name search
- `search id <prefix>`             – Search by exact or prefix ID

#### Bulk Operations
- `toggle <id>`                   – Toggle a node and all its children between done/undone
- `clearall mem`                  – Clear all in-memory nodes (requires confirmation)
- `clearall file`                 – Delete saved data file (requires confirmation)
- `clearall both`                 – Clear memory and delete file (requires confirmation)
- `abort clearall`                – Cancel pending `clearall`

---

### 💡 Usage examples
- `sample` → `ls` → `table` / `tree` / `ascii`
- `create Project "New Project"` → `ls` → `create Phase "Planning"`
- `sample` → `table` → `delete 01.01` → `confirm delete 01.01` → `table`
- `sample` → `table` → `toggle 01.01` → `table`
- `search plan` → list all nodes with “plan” in the name
- `clearall both` → remove all data after confirmation

---

## 📜 Version History

### v0.1.0a2 – 2025-08-13
- Added `edit`, `search`, and `clearall` commands
- External help text loading
- Improved command parsing and confirmation system

### v0.1.0a1 – 2025-08-11
- Initial release with core `Node` system, `schema`, `create`, `delete`, `toggle`, and view commands
