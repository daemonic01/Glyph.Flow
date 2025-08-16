import json
import os
from pathlib import Path

DEFAULT_CONFIG = {
    "version": "0.1.0a3",
    "paths": {
        "data": "data/node_data.json",
        "help": "assets/help.txt"
    },
    "autosave": False
}

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config.json"

def load_config(path: str = CONFIG_PATH):
    """Load configuration from JSON file, or create default if missing."""
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
    """Save configuration to JSON file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
