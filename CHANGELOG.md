# Changelog – Glyph.Flow

---

## [v0.1.0a4] – 2025-08-19

### ✨ Added
- Introduced layered and leveled logging and internal messaging system
- All commands in `app.py` migrated to use the new logging system (except view outputs)
- Added `CommandHistory` module with arrow-key navigation
- Foundation for upcoming Command Registry system

### 🔧 Improved
- More efficient internal and external log management.
- Minor changes in the backend, preparation for a complete separation from the frontend.

### 🐛 Known Limitations
- No undo/redo system
- No system message buffer/logging
- No localized messaging system.
- Manual command input only – no TUI or keybindings yet
- No export/import feature.

---

## [v0.1.0a3] – 2025-08-16

### ✨ Added
- Added autosave feature and `autosave <on/off>` command.
- Added `config.json` to store settings and basic information.
- Added `content_styler.py` for unified log message formatting (INFO, WARN, ERROR, SUCCESS).  
  Preparing to support localized messaging

### 🔧 Improved
- The first message now displays the version number and the status of the autosave setting.
- All log outputs now use consistent formatting instead of inline Rich markup.

### 🐛 Known Limitations
- No undo/redo system
- No system message buffer/logging
- No localized messaging system.
- Manual command input only – no TUI or keybindings yet
- No export/import feature.

---

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