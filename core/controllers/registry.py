

COMMANDS = {
    "help": {
        "type": "default",
        "aliases": ["?"],
        "description": "Show available commands or help for a specific command.",
        "usage": "help",
        "handler"
        "binding": "h",
        "require_data": False,
        "mutate": False,
        "mutate_config": False,
        "destructive": False,
        "params": [],
        "handler": "core.presenters.help.help_handler",
        "messages": None
    },
    "quit": {
        "type": "default",
        "aliases": ["q"],
        "description": "Quit Glyph.Flow.",
        "usage": "quit",
        "handler"
        "binding": "q",
        "require_data": False,
        "mutate": False,
        "mutate_config": False,
        "destructive": False,
        "params": [],
        "handler": "core.services.quit.quit_handler",
        "messages": None
    },
    "ls": {
        "type": "default",
        "aliases": ["list, roots"],
        "description": "List root nodes.",
        "usage": "ls",
        "binding": None,
        "require_data": True,
        "mutate": False,
        "mutate_config": False,
        "destructive": False,
        "params": [],
        "handler": "core.presenters.ls.ls_handler",
        "messages": None
    },
    "tree": {
        "type": "default",
        "aliases": [],
        "description": "Show tree view of all nodes.",
        "usage": "tree",
        "binding": None,
        "require_data": True,
        "mutate": False,
        "mutate_config": False,
        "destructive": False,
        "params": [],
        "handler": "core.presenters.tree.tree_handler",
        "messages": None
    },
    "ascii": {
        "type": "default",
        "aliases": ["asc"],
        "description": "Show ascii tree view of all nodes.",
        "usage": "ascii",
        "binding": None,
        "require_data": True,
        "mutate": False,
        "mutate_config": False,
        "destructive": False,
        "params": [],
        "handler": "core.presenters.ascii.ascii_handler",
        "messages": None
    },
    "table": {
        "type": "default",
        "aliases": ["tab"],
        "description": "Show table view of all nodes.",
        "usage": "table",
        "binding": None,
        "require_data": True,
        "mutate": False,
        "mutate_config": False,
        "destructive": False,
        "params": [],
        "handler": "core.presenters.table.table_handler",
        "messages": None
    },


    "clear": {
        "type": "default",
        "aliases": ["clr"],
        "description": "Clear the terminal.",
        "usage": "clear",
        "binding": None,
        "require_data": False,
        "mutate": False,
        "mutate_config": False,
        "destructive": False,
        "params": [],
        "handler": "core.services.clear_terminal.clear_handler",
        "messages": None
    },


    "sample": {
        "type": "default",
        "aliases": ["demo"],
        "description": "Create demo/sample project tree.",
        "usage": "sample",
        "binding": None,
        "require_data": False,
        "mutate": True,
        "mutate_config": False,
        "destructive": False,
        "params": [],
        "handler": "core.handlers.sample.sample_handler",
        "messages": {
            "success":                  "file.sample_tree_created"
        }
    },

    "save": {
        "type": "default",
        "aliases": ["s"],
        "description": "Save all data to file.",
        "usage": "save",
        "binding": None,
        "require_data": False,
        "mutate": False,
        "mutate_config": False,
        "destructive": False,
        "params": [],
        "handler": "core.services.save.save_handler",
        "messages": {
            "manual_save_completed":                  "file.manual_save_completed"
        }
    },


    "create": {
        "type": "default",
        "aliases": ["c"],
        "description": "Create nodes.",
        "usage": "create <type> <name> [--desc \"...\"] [--full \"...\"] [--deadline YYYY-MM-DD] [--parent <id>]",
        "binding": None,
        "require_data": False,
        "mutate": True,
        "mutate_config": False,
        "destructive": False,
        "params": {
            "positionals": ["type", "name"],
            "options": {
                "--desc": "short_desc",
                "--full": "full_desc",
                "--deadline": "deadline",
                "--parent": "parent_id",
            },
            "defaults": {
                "short_desc": None,
                "full_desc": None,
                "deadline": None,
                "parent_id": None,
            },
        },
        "handler": "core.handlers.create.create_handler",
        "messages": {
            "success":                  "node.created_node",
            "parent_not_found_error":   "node.create_parent_not_found",
            "root_type_error":          "node.create_root_node_type_error",
            "tree_level_error":         "node.tree_level_error",
            "past_date_error":          "node.past_date_error",
            "deadline_too_early":       "node.deadline_too_early",
            "short_desc_too_long":      "node.short_desc_too_long",
            "full_desc_too_long":       "node.full_desc_too_long"
        }
    },

    "schema": {
        "type": "default",
        "aliases": ["sch", "schem"],
        "description": "Create or change tree schema.",
        "usage": "schema <level1> <level2> ...",
        "binding": None,
        "require_data": False,
        "mutate": True,
        "mutate_config": True,
        "destructive": False,
        "params": {
            "positionals": ["hierarchy+"],
            "options": {
                "--default": { "to": "use_default", "flag": True }
                },
            "defaults": {
                "hierarchy": [],
                "use_default": False
                }
            },

        "handler": "core.services.schema.schema_handler",
        "messages": {
            "set_success":            "schema.set_success",
            "switch_success":         "schema.switch_success",
            "switch_default_success": "schema.switch_default_success",
            "length_mismatch":        "schema.length_mismatch",
            "error":                  "schema.error"
        }
    },

    "delete": {
        "type": "default",
        "aliases": ["del", "remove", "rm"],
        "description": "Delete a node by ID.",
        "usage": "delete <id>",
        "binding": None,
        "require_data": True,
        "mutate": True,
        "mutate_config": False,
        "destructive": True,
        "params": {
            "positionals": ["id"],
            "options": {},
            "defaults": {}
        },
        "handler": "core.handlers.delete.delete_handler",
        "messages": {
            "not_found":     "node.node_not_found",
            "deleted_root":  "node.delete_root_done",
            "deleted_child": "node.delete_done",
        }
    },
    "edit": {
        "type": "default",
        "aliases": ["e"],
        "description": "Edit a node by ID.",
        "usage": "edit <id> [--name \"...\"] [--desc \"...\"] [--full \"...\"] [--deadline YYYY-MM-DD]",
        "binding": None,
        "require_data": True,
        "mutate": True,
        "mutate_config": False,
        "destructive": False,
        "params": {
            "positionals": ["id"],
            "options": {
            "--name": "name",
            "--desc": "short_desc",
            "--full": "full_desc",
            "--deadline": "deadline"
            },
            "defaults": {
            "name": None,
            "short_desc": None,
            "full_desc": None,
            "deadline": None
            }
        },
        "handler": "core.handlers.edit.edit_handler",
        "messages": {
            "not_found":                "node.node_not_found",
            "edit_done":                "node.edit_done",
            "edit_no_change":           "node.edit_no_change",
            "past_date_error":          "node.past_date_error",
            "deadline_too_early":       "node.deadline_too_early",
            "short_desc_too_long":      "node.short_desc_too_long",
            "full_desc_too_long":       "node.full_desc_too_long"
        }
    },
    "search": {
        "type": "default",
        "aliases": ["find"],
        "description": "Search nodes by name substring (default) or by ID exact/prefix.",
        "usage": "search <substring> | search name <substring> | search id <prefix-or-exact>",
        "binding": None,
        "require_data": False,
        "mutate": False,
        "mutate_config": False,
        "destructive": False,
        "params": {
            "positionals": ["first", "rest*"],
            "options": {},
            "defaults": {
            "first": None,
            "rest": [],
            "mode": "name"
            }
        },
        "handler": "core.handlers.search.search_handler",
        "messages": {
            "no_data":            "file.no_data",
            "search_no_matches":  "node.search_no_matches"
        }
    },
    "toggle": {
        "type": "default",
        "aliases": ["t"],
        "description": "Toggle a node's completion state by ID (recursively).",
        "usage": "toggle <id>",
        "binding": None,
        "require_data": True,
        "mutate": True,
        "mutate_config": False,
        "destructive": False,
        "params": {
            "positionals": ["id"],
            "options": {},
            "defaults": {}
        },
        "handler": "core.handlers.toggle.toggle_handler",
        "messages": {
            "usage":     "usage.toggle",
            "not_found": "node.node_not_found",
            "toggled":   "node.toggled",
        }
    },
    "clearall": {
        "type": "default",
        "aliases": [],
        "description": "Clear memory, data file or both.",
        "usage": "clearall <mem/memory|file/data|both/all>",
        "binding": None,
        "require_data": True,
        "mutate": True,
        "mutate_config": False,
        "destructive": True,
        "params": {},
        "handler": "core.handlers.clearall.clearall_handler",
        "messages": {
            "clear_done":              "clearall.clear_done",
            "file_not_found":           "clearall.file_not_found"
        }
    },
    "config": {
        "type": "default",
        "aliases": ["cfg"],
        "description": "Set a boolean configuration value.",
        "usage": "config <setting> <on|off>",
        "binding": None,
        "require_data": False,
        "mutate": False,
        "mutate_config": True,
        "destructive": False,
        "params": {
            "positionals": ["setting", "value"],
            "options": {},
            "defaults": {
            "setting": None,
            "value": None
            }
        },
        "handler": "core.services.config.config_handler",
        "messages": {
            "unknown_key":   "config.unknown_key",
            "invalid_value": "config.invalid_value",
            "no_change":     "config.no_change",
            "set_success":   "config.set_success",
            "error":         "cmd.config.error"
        }
    },
    "undo": {
        "type": "default",
        "aliases": ["u"],
        "description": "Undo last change.",
        "usage": "undo",
        "binding": "u",
        "require_data": False,
        "mutate": True,
        "mutate_config": False,
        "destructive": False,
        "params": [],
        "handler": "core.services.undo_redo.undo_handler",
        "messages": {"success": "undo_redo.undo_success",
                    "no_change": "undo_redo.undo_no_change"}
    },
    "redo": {
        "type": "default",
        "aliases": ["r"],
        "description": "Redo last undone change.",
        "usage": "redo",
        "binding": "r",
        "require_data": False,
        "mutate": True,
        "mutate_config": False,
        "destructive": False,
        "params": [],
        "handler": "core.services.undo_redo.redo_handler",
        "messages": {"success": "undo_redo.redo_success",
                    "no_change": "undo_redo.redo_no_change"}
    },
    "move": {
        "type": "default",
        "aliases": ["m"],
        "description": "Move a child node below another node.",
        "usage": "move <id> <target_parent_id>",
        "binding": None,
        "require_data": False,
        "mutate": True,
        "mutate_config": False,
        "destructive": False,
        "params": {
            "positionals": ["id", "target_parent_id"]
            },
        "handler": "core.handlers.move.move_handler",
        "messages": { "node_not_found": "move.node_not_found",
                      "move_root_error": "move.move_root_error",
                      "target_parent_not_found": "move.target_parent_not_found",
                      "already_there": "move.already_there",
                      "type_error": "move.type_error",
                      "move_success": "move.success"}
    },

    "export": {
        "type": "default",
        "aliases": ["ex", "exp", "output"],
        "description": "Export nodes to CSV, PDF or JSON.",
        "usage": "export [--format csv|pdf|json] [--path <file>] [--scope all|current|subtree:<id>|filter:<query>] "
                 "[--columns col1,col2,...] [--sort <col:asc|desc>] [--no-completed]",
        "binding": None,
        "require_data": True,
        "mutate": False,
        "mutate_config": False,
        "destructive": False,
        "params": {
            "positionals": [],
            "options": {
                "--format": "format",
                "--path": "path",
                "--scope": "scope",
                "--columns": "columns",
                "--sort": "sort",
                "--no-completed": { "to": "include_completed", "flag": True }
            },
            "defaults": {
                "format": "csv",
                "path": None,
                "scope": "all",
                "columns": None,
                "sort": "",
                "include_completed": True
            }
        },
        "handler": "core.services.export.export_handler",
        "before": None,
        "after": None,
        "messages": {
            "success": "export.success",
            "invalid_format": "export.invalid_format",
            "export_failed": "export.failed"
        }
    },
    "import": {
        "type": "default",
        "aliases": ["imp"],
        "description": "Import JSON (replace|append|merge).",
        "usage": "import --file <path> [--mode replace|append|merge]",
        "binding": None,
        "require_data": False,
        "mutate": True,
        "mutate_config": False,
        "destructive": True,
        "params": {
            "positionals": [],
            "options": {
            "--file": "file",
            "--mode": "mode"
            },
            "defaults": {
            "file": None,
            "mode": "append"
            }
        },
        "handler": "core.services.import.import_handler",
        "messages": {
            "file_missing":   "import.file_missing",
            "parse_error":    "import.parse_error",
            "invalid_mode":   "import.invalid_mode",
            "replaced":       "import.replaced",
            "appended":       "import.appended",
            "merged":         "import.merged"
        }
    },


    
}