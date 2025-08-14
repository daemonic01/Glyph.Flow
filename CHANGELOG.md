# Changelog – Glyph.Flow

---

## [v0.1.0a2] – 2025-08-14

### ✨ Added
- `edit` command to modify existing nodes (name, short/full description, deadline) via flags.
- `search` command with::
  - `search <substring>` / `search name <substring>` → case-insensitive name search.
  - `search id <prefix>` → ID-based search (exact or prefix match).
  - Results displayed in a compact Rich table.
- `clearall` command with confirmation:
  - `clearall mem` → clear in-memory nodes.
  - `clearall file` → delete saved data file.
  - `clearall both` → clear memory and delete file.
- Expanded `confirm` and `abort` command to confirm or cancel clearall operations.

### 🔧 Improved
- Help text now loaded from external file for easier editing.
- Unified argument parsing for new commands.

### 🐛 Known Limitations
- No undo/redo system
- No system message buffer/logging
- Manual command input only – no TUI or keybindings yet

---

## [v0.1.0a1] – 2025-08-11

### ✨ Added
- Core `Node` class with:
  - Hierarchical ID generation (root and child IDs)
  - Support for parent/child trees
  - Progress tracking logic
- `NodeSchema` to enforce allowed type hierarchies
- `parser.py` to support `create` commands with optional flags
- `data_io.py` to save/load JSON trees and provide sample data
- TUI app (`NodeTestApp`) with the following commands:
  - `sample`, `ls`, `tree`, `ascii`, `table`
  - `create`, `delete`, `confirm delete`, `abort delete`
  - `toggle` command with improved logic to preserve manually set states
  - `save`, `load`, `schema`
- Colored output and structured tree display
- Table-based node rendering via `rich.table`
- Help command with usage examples
- Warning messages when executing view commands on empty data

### 🔧 Improved
- Root ID counter now adjusts automatically after loading data
- Refactored `toggle_all` to avoid overriding manually changed child states
- Minor UX improvements in command feedback and error messages

### 🐛 Known Limitations
- No `edit`, `move` or `find` support yet
- No undo/redo system
- No system message buffer/logging
- Manual command input only – no TUI or keybindings yet

---

## [Unreleased]

### 🚧 Planned
- Full migration into standalone Textual app (beyond console testing)
- Detailed TUI interface with main menu, project view, settings, and changelog
- Enhanced editing and moving of nodes
- Stats and progress overview
- Undo system
- Logging recent commands / state changes