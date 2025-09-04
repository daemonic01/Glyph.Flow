import json
import os
from pathlib import Path

DEFAULT_CONFIG = {
    "version": "0.1.0a8",
    "paths": {
        "data": "data/node_data.json",
        "help": "assets/help.txt",
        "messages": "loc/en/messages.json",
        "syslog": "logs/app.log"
    },
    "node_properties": {
        "short_desc_length_limit": 100,
        "full_desc_length_limit": 300
    },
    "default_schema": [
        "Project",
        "Phase",
        "Task",
        "Subtask"
    ],
    "custom_schema": [],
    "logging": True,
    "log": {
        "rotate": {
            "max_bytes": 262144,
            "backup_count": 5
        }
    },
    "autosave": True,
    "assume_yes": False,
    "command_history_maxlen": 50,
    "undo_redo_limit": 50
}

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config.json"



def load_config(path: str = CONFIG_PATH):
    """
    Load application configuration from a JSON file.

    Behavior:
        - If file does not exist → creates it with DEFAULT_CONFIG and returns that.
        - If file exists → loads and returns its contents as a dict.
        - If file exists but is invalid JSON → prints warning, returns DEFAULT_CONFIG.

    Args:
        path (str | Path): Path to the JSON config file. Defaults to CONFIG_PATH.

    Returns:
        dict: Loaded configuration.
    """
    if not os.path.exists(path):
        save_config(DEFAULT_CONFIG, path)
        return DEFAULT_CONFIG

    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            print(f"[WARN] Invalid config file at {path}, using defaults.")
            return DEFAULT_CONFIG



def save_config(config: dict, path: str = CONFIG_PATH):
    """
    Save configuration to a JSON file.

    Args:
        config (dict): Configuration dictionary to save.
        path (str | Path): Path of the JSON config file. Defaults to CONFIG_PATH.
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
