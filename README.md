
https://github.com/user-attachments/assets/0a706a5a-91e9-4f22-8f0c-a5ba3e3c483a


# Glyph.Flow

**Glyph.Flow** is a minimalist, keyboard-driven TUI workflow manager built with Python and [Textual](https://github.com/Textualize/textual).  
It allows you to define hierarchical structures such as projects, phases, tasks, and subtasks, and manage them directly from the terminal.

This is an early prototype (v0.1.0a8), mainly focused on backend data modeling and command parsing.

---

## 🔧 Features

- Layered logging system with message catalog (`log.key`, `log.help`)
- Unified system messages with INFO/WARNING/ERROR/SUCCESS/DEBUG/HELP levels
- Command history navigation (Up/Down arrows)
- Universal tree structure based on a flexible `Node` class
- Unique hierarchical segmented ID generation for all nodes
- Type-checked schema (e.g. Project > Phase > Task > Subtask)
- JSON-based save/load of full node trees
- TUI-based test interface using `Textual`
- Command-based interaction for early testing: `create`, `edit`, `delete`, `search`, `clearall`, `save`, `move`, etc.
- Rich output: tree view, table view, ASCII rendering
- Interactive confirmation for destructive operations (`delete`, `clearall`)
- Help text loaded from external file for easier maintenance
- Layered and leveled logging and internal messaging system with buffer prepared for lcalization.
- Retrievable command history of the last 50 unique commands (Arrow keys in the input field.)
- All commands are declaratively defined in a command registry system.
- Dual-log system: 'log' for system/runtime messages and 'presenter' for visual command outputs.
- Live updated configuration information in the header.
- Memory friendly undo/redo feature.

---

## 📂 File Structure
- `node.py` – Core Node class with hierarchy and progress logic
- `schema.py` – Enforces expected child types
- `data_io.py` – Load/save trees and generate sample data
- `message_styler.py` - Advanved internal message system.
- `log.py` - Log system that handles internal messages and external logging.
- `command_history.py` - Retrieveable command history of the last 50 unique commands.
- `config_loader.py` - Utility functions that handle external config.
- `context.py` - Real time global available data for operations.
- `/controllers` - Command registry system.
- `/handlers, /presenters, /services` - Clear handler function system for the command registry.
- `app.py` – Textual-based TUI frontend for testing

---

## 🧭 Roadmap Highlights
- Planned for future versions:
  - Improved scheme system
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
- `schema`                        – Set a new node hierarchy (e.g. `schema Level1 Level2 Level3 Level4`)
- `undo`                          - Reverts the last mutative change (create, edit, delete, toggle, move).          * NEW *
- `redo`                          - Reapplies the last reverted mutative change.                                    * NEW *

#### Node Management
- `create`                        – Create node (e.g. `create Task "Refactor Logic" --desc "Cleanup" --full "Split backend and UI" --parent 01.01`)
- `edit`                          – Edit an existing node (e.g. `edit 01.02 --name "New Name" --desc "Short" --full "Detailed" --deadline 2025-08-15`)
- `delete`                        – Schedule deletion (e.g. `delete 01.01.01`)
- `confirm delete <id>`           – Confirm a pending delete
- `toggle <id>`                   – Toggle a node and all its children between done/undone
- `move <id> <target_id>`         - Move a node below another node (level sensitive). Root can't be moved.          * NEW *

#### Search & Filters
- `search <substring>`            – Search by name (case-insensitive)
- `search name <substring>`       – Explicit name search
- `search id <prefix>`             – Search by exact or prefix ID

#### Bulk Operations
- `clearall`                      – Clear all in-memory nodes (requires confirmation)
- `save`                          - Save project tree manually.


#### Config Operations
- `config <setting> <on/off>`     - Turn auto-save / confirmation requests / logging on and off.
- `autosave <on/off>`             - Turn auto-save on and off.

---

### 💡 Usage examples

#### Create display and toggle

```bash
sample
ls
tree
ascii
table
```

```bash
create Project "TUI APP" --deadline "2030-12-12" --desc "Make a task manager TUI app in Textual." --full "Make a completely useless Textual app for task management."
table
toggle 01
table
```

#### Delete
```bash
create Project "TUI APP" --deadline "2030-12-12" --desc "Make a task manager TUI app in Textual." --full "Make a completely useless Textual app for task management."
ls
delete 01
ls
```

#### Edit and move:
```bash
create Project "TUI APP" --deadline "2030-12-12" --desc "Make a task manager TUI app in Textual." --full "Make a completely useless Textual app for task management."
create Phase "CORE Implementation" --deadline "2030-10-10" --desc "Implement core functionality of the app." --parent 01
create Phase "TUI Implementation" --deadline "2030-10-10" --desc "Implement TUI frontend for the app." --parent 01
create Task "Config Handler" --deadline "2030-09-09" --desc "Make a config handler script for the app." --parent 01.01
create Task "Commadn Rgistry" --deadline "2030-08-08" --desc "Make a command registry for handling commands." --parent 01.01
edit 01.01.02 --name "Command Registry"
create Task "Main Menu" --deadline "2030-08-08" --desc "Make a main menu panel for the app." --parent 01.01
move 01.01.03 01.02

```

#### Undo & Redo:
```bash
create Project "TUI APP" --deadline "2030-12-12" --desc "Make a task manager TUI app in Textual." --full "Make a completely useless Textual app for task management."
create Phase "CORE Implementation" --deadline "2030-10-10" --desc "Implement core functionality of the app." --parent 01
create Phase "TUI Implementation" --deadline "2030-10-10" --desc "Implement TUI frontend for the app." --parent 01
create Task "Config Handler" --deadline "2030-09-09" --desc "Make a config handler script for the app." --parent 01.01
create Task "Commadn Rgistry" --deadline "2030-08-08" --desc "Make a command registry for handling commands." --parent 01.01
undo
create Task "Command Registry" --deadline "2030-08-08" --desc "Make a command registry for handling commands." --parent 01.01
```

```bash
create Project "TUI APP" --deadline "2030-12-12" --desc "Make a task manager TUI app in Textual." --full "Make a completely useless Textual app for task management."
edit 01 --name "Tui App"
undo
table
redo
table
```

---

## 📜 Version History

### v0.1.0a8 - 2025-09-02:
- Added `move` command to relocate nodes (level sensitive).
- Introduced **memory friendly undo/redo feature** for easier project management.

### v0.1.0a7 - 2025-08-28
- Fixed the error on startup without a data file.

### v0.1.0a6 - 2025-08-28
- Implemented **dual-log system**:
  - `log` for system/runtime messages.
  - `presenter` for visual command outputs.
  Both are independently configurable and reflow-aware.
- Introduced **GlyphRichLog** with buffer + dynamic rewrap on resize.
- Added **animated panel adjustment** (`action_adjust`) to toggle log/output panel widths.
- Added a new header with live configuration info and a pixelart logo generated by an image with `rich-pixels`.

### v0.1.0a5 - 2025-08-22
- Introduced the new **Command Registry** system: all commands are now declaratively defined in `registry.py`.
- Added `command_factory.py` to parse raw input into a `Command` object with params, handlers and messages.
- Refactored every command using the registry, with full support for positionals, options and defaults.
- Added support for command-specific usage messages resolved through the registry.
- Added 'config' command to switch settings (autosave, confirmation requests and logging).

### v0.1.0a4 – 2025-08-19
- Introduced layered and leveled logging and internal messaging system with buffer prepared for lcalization.
- All commands in `app.py` migrated to use the new logging system (except view outputs)
- Added `CommandHistory` module with arrow-key navigation
- Foundation for upcoming Command Registry system

### v0.1.0a3 – 2025-08-16
- Added autosave feature and `autosave` command.
- Added `config.json` to store settings and basic information.
- Added `content_styler.py` for unified log message formatting (INFO, WARN, ERROR, SUCCESS).  
  Preparing to support localized messaging

### v0.1.0a2 – 2025-08-14
- Added `edit`, `search`, and `clearall` commands
- External help text loading
- Improved command parsing and confirmation system

### v0.1.0a1 – 2025-08-11
- Initial release with core `Node` system, `schema`, `create`, `delete`, `toggle`, and view commands
