# Glyph.Flow — Command Line Documentation

Glyph.Flow is a minimalist terminal-based workflow manager.  
This document provides an overview of the available commands, concepts, and usage patterns for the application.

---

## 📌 ID Structure

All entries in Glyph.Flow are identified using **segmented IDs** that reflect their position in the hierarchy.  
Each level in the structure increases the depth of the ID:

- Root node: `01`
- First child: `01.01`
- Second-level child: `01.01.01`
- etc.

By default, the system allows **4 levels**:

- `Project > Phase > Task > Subtask`

Every command that refers to a specific entry uses these IDs.

---

## 🛠 Structure Commands

### `create <type> <name> [--desc ...] [--full ...] [--deadline ...] [--parent <id>]`

Create a new node in the tree.

- `<type>`: One of the schema types (e.g. Project, Phase, etc.)
- `<name>`: Name of the node
- Optional flags:
  - `--desc`: Short description
  - `--full`: Full description
  - `--deadline`: Deadline in `YYYY-MM-DD` format
  - `--parent <id>`: The parent node’s ID

**Example:**

```bash
create Task "Fix Logic" --desc "Bugfix" --parent 01.02
```

---

### `edit <id> [--name ...] [--desc ...] [--full ...] [--deadline ...]`

Edit an existing node's attributes.

- `<id>`: ID of the node to edit
- Optional flags:
  - `--name`: Change the node name
  - `--desc`: Change the short description
  - `--full`: Change the full description
  - `--deadline`: Set a new deadline

**Example:**

```bash
edit 01.02 --name "New Name" --desc "Short" --full "Detailed" --deadline 2025-08-15
```

---

### `delete <id>`

Schedules a node for deletion. Requires confirmation.

**Example:**

```bash
delete 01.01
```

---

### `confirm delete <id>`

Confirms and executes the deletion of the node.

---

### `abort delete`

Cancels a pending deletion operation.

---

### `schema <type1> <type2> ...`

Changes the hierarchy structure. You may redefine the levels (e.g. `Goal > Step > Action`).  
You can only change the schema **if its depth matches the currently loaded tree**.

**Default schema:**

```bash
schema Project Phase Task Subtask
```

---

### `toggle <id>`

Toggles the selected node and all its children between `done` and `not done`.

**Example:**

```bash
toggle 01.02
```

---

## 🔍 Search Commands

### `search <substring>`

Search nodes by name (case-insensitive).

### `search name <substring>`

Explicitly search nodes by name.

### `search id <prefix>`

Search by exact ID or by prefix (returns matching descendants).

**Example:**

```bash
search plan
search id 01.02
```

---

## 📄 Display Commands

### `ls`

Lists all root-level nodes.

### `tree`

Displays the full node tree with indentation to represent levels.

### `ascii`

Displays the node tree using ASCII-style branches.

### `table`

Shows all nodes and their details in a tabular format.

### `clear`

Clears the console log area.

---

## 💾 File I/O Commands

### `save`

Saves the current node tree to `node_data.json`  
(Default location: `glyphflow/data/node_data.json`)

### `load`

Loads the node tree from `node_data.json`

### `sample`

Generates a pre-filled sample tree to experiment with.

---

## 🧹 Bulk Operations

### `clearall mem`

Clears all in-memory nodes. Requires confirmation.

### `clearall file`

Deletes the saved data file. Requires confirmation.

### `clearall both`

Clears memory and deletes the saved data file. Requires confirmation.

### `abort clearall`

Cancels a pending clearall operation.

---

## 🧪 Miscellaneous

### `help`

Displays this help message.

---

## 🚪 Exit

### `q` or `quit`

Quits the application.

---

## ⚠️ Notes

- **Automatic saving/loading is not yet implemented.**  
  Use `save` and `load` manually when needed.

- You can use `sample` to generate a sample tree, then explore it using any of the display commands like `tree`, `table`, or `ascii`.

- The command interface is case-sensitive. Always use exact ID references when required.
