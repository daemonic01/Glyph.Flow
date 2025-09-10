# ✨ Glyph.Flow

> **Minimalist, keyboard-driven workflow manager in your terminal.**  
> Built with Python + [Textual](https://github.com/Textualize/textual).  
> For makers who live in the CLI, and want order without leaving it.  

---

## ⚡ Why Glyph.Flow?

Because you don’t need *another* bloated task manager.  
You need something **fast, focused, and terminal-native** — a tool that keeps up with your brain, not slows it down.

**Glyph.Flow** lets you map out entire workflows (Projects → Phases → Tasks → Subtasks) and control them with pure keystrokes.  
No mouse. No clutter. Just flow.  

Key ideas:
- **Hierarchical workflows** → Model complex projects, not just checklists.
- **Diff-based undo/redo** → Rare in TUIs, a game-changer for experimentation.
- **Autosave & recovery** → Kill the terminal? Pick up right where you left off.
- **Export anywhere** → JSON, CSV, PDF — your data, your rules.
- **Schema freedom** → Redefine the hierarchy (e.g. `Feature > Epic > Story > Ticket`).
- **Multiple views** → Tree, table, ASCII, logs — whatever fits your brain.  

---

## 🎥 See it in action

[![Demo Video](https://img.shields.io/badge/▶-Watch%20the%20demo-red)](https://github.com/user-attachments/assets/0a706a5a-91e9-4f22-8f0c-a5ba3e3c483a)

---

## 🧩 Features at a glance

- 🔹 **Command Registry** – every command declaratively defined, consistent & extendable.  
- 🔹 **Layered logging system** – INFO, WARN, ERROR, HELP, DEBUG, SUCCESS.  
- 🔹 **Dual log channels** – system/runtime vs presenter/visual.  
- 🔹 **Command history navigation** – arrow keys recall the last 50 commands.  
- 🔹 **Interactive confirmations** – no accidental nukes of your data.  
- 🔹 **Autosave toggle** – configure safety vs control.  
- 🔹 **Configurable themes & header info** – because style matters, even in CLI.  

---

## 🧭 Roadmap

We’re just getting started. Upcoming ideas:

- **Advanced Search** → filters, regex, fuzzy matching, saved queries.  
- **Profiles** → multiple personal/project spaces, custom settings + themes.  
- **Dashboard & Stats** → completion %, summaries, progress visuals.  
- **Enhanced TUI** → dedicated project view, menu system, integrated changelog.  
- **Themes & customization** → dark/light/high-contrast, custom color schemes.  
- **Plugin system** → extend with integrations, custom commands, automations.  

---

## 🚀 Getting Started

### 📦 Requirements
- Python **3.10+** (works on Linux, macOS, and Windows)
- Packages: [`textual`](https://github.com/Textualize/textual), [`rich`](https://github.com/Textualize/rich)

---

### 🔽 Installation

#### 1. Clone the repository and start the app
**Linux / macOS / Windows:**
```bash
git clone https://github.com/<your-username>/Glyph.Flow.git
cd Glyph.Flow
pip install -r requirements.txt
python main.py

```

Then type commands directly in the input field (see examples below).

---

## 💻 Quick Commands

```bash
sample              # generate demo tree
tree                # see hierarchy
table               # tabular view
ascii               # ASCII-style rendering

create Project "My App" --desc "Build a TUI app"  
create Phase "Backend" --parent 01  
create Task "Command Registry" --parent 01.01  

undo                 # revert last change
redo                 # reapply it
export --format pdf  # export to PDF
```

---

## 📜 Latest Changes

### v0.1.0a9 (2025-09-07)
- New config subsystem (easier, cleaner management).
- Two-step context initialization.
- Added `import` command for Glyph.Flow data files (JSON) with 'replace', 'append' and 'merge' modes.
- Customizable `export` command with CSV, PDF, JSON output.
- More command aliases.

*(Full changelog in [changelog](CHANGELOG.md)).*

---

## 🛠 Status

Glyph.Flow is still **alpha software**.
Expect rough edges, but the foundations are here — and it’s evolving fast.

Star ⭐ the repo if you like where it’s heading.
**Feedback & contributions are always welcome.**
