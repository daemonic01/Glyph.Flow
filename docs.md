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


### `schema <type1> <type2> ...`

Changes the hierarchy structure. You may redefine the levels (e.g. `Goal > Step > Action`).  
You can only change the schema **if its depth matches the currently loaded tree**.

**Default schema:**

```bash
schema Project Phase Task Subtask
```

---

### `move <id> <target_parent_id>`

Move a node below another node (level sensitive). Root can't be moved.

**Example:**

```bash
move 01.01.01 01.03
```

---

### `toggle <id>`

Toggles the selected node and all its children between `done` and `not done`.

**Example:**

```bash
toggle 01.02
```

---

### `undo`

Reverts the last mutative change (create, edit, delete, toggle, move).

**Example:**

```bash
create Project "name"
table
undo
table
```

---

### `redo`

Reapplies the last reverted mutative change.

**Example:**

```bash
create Project "name"
undo
table
redo
table
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

### `sample`

Generates a pre-filled sample tree to experiment with.

### `bigsample`

Generate a pre-filled big (11111 node) test sample node tree.

---

## 🧹 Bulk Operations

### `clearall`

Clears all project nodes. Requires confirmation.

### `import [--file ...] [--mode ...]`

Imports project tree from a JSON file with three modes. Requires confirmation.
Flags:
- `--file`: File path. e.g. D:/datatoimport/data.json
- `--mode`: The method of attachment.
Modes:
      - `append`: Simply appends the new data to the existing data.
      - `replace`: Replaces the entire data set with the new data.
      - `merge`: Replaces identical nodes based on ID, creates new nodes in case of new ID.

### `export [--format ...] [--path ...] [--scope ...] [--columns ...] [--sort ...] [--no-completed]`

Exports project tree to CSV, PDF or JSON file.
Flags:
- `--format csv|pdf|json`: File format. Can be 'csv', 'pdf' or 'json'.
- `--path <filepath>`: File path. e.g. D:/exportpath/
- `--scope all|current|subtree:<id>|filter<query>:`: The range of nodes to be exported. (default: all; current isn't working yet)
      With filter you can search by ID, name, type, short and full description. It searches in all of them (keyword filter).
      E.g. --scope filter:Task (exports only Task type nodes)
- `--columns <col1>, <col2>`: 
- `--sort <col:asc/desc>`: Sorting option for exported nodes. e.g. --sort name:desc
- `--no-completed`: Export everything but finished nodes.

---

## 🧪 Miscellaneous

### `help`

Displays this help message.

### `test <all|files|config|cmd>`

Test file integrity, config file, command functionality or both. It creates report files in tests/reports.

---

## ⚙️ Config

### config <setting> <on/off>

Turn auto-save / confirmation requests / logging on and off.

---

## 🚪 Exit

### `q` or `quit`

Quits the application.

---


## ⚠️ Notes

- **Automatic saving is already implemented.**
  Running the "save" command is no longer necessary after making changes if autosave is enabled (default).

- You can use `sample` to generate a sample tree, then explore it using any of the display commands like `tree`, `table`, or `ascii`.

- The command interface is case-sensitive. Always use exact ID references when required.
