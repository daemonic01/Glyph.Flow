from pathlib import Path
import json
import os
from typing import List
from .node import Node
from core.config_loader import load_config
from core.log import log




BASE_DIR = Path(__file__).resolve().parent.parent
config = load_config()
DATA_PATH = BASE_DIR / config["paths"]["data"]


def save_node_tree(root_nodes: List[Node], filename: str = str(DATA_PATH)):
    """Save the given list of root nodes to a JSON file.

    Args:
        root_nodes (List[Node]): List of root-level Node objects to save.
        filename (str): Path to the JSON file where data will be written.
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump([node.to_dict() for node in root_nodes], f, indent=2, ensure_ascii=False)
    


def load_node_tree(filename: str = str(DATA_PATH)) -> List[Node]:
    """Load a node tree from a JSON file.

    Args:
        filename (str): Path to the JSON file to read.

    Returns:
        List[Node]: List of root-level Node objects loaded from file.
    """
    try:
        if not os.path.exists(filename):
            with open(filename, "w", encoding="utf-8") as f:
                json.dump([], f)
            return []
        
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            nodes = [Node.from_dict(entry) for entry in data]

            Node.relabel_missing_ids(nodes)

            return nodes
    except:
        log.key("file.load_error", filename=filename)



def delete_data_file(filename: str = str(DATA_PATH)) -> bool:
    """Delete the node data file if it exists. Returns True if deleted."""
    if os.path.exists(filename):
        os.remove(filename)
        return True
    return False



HELP_PATH = BASE_DIR / config["paths"]["help"]

def load_help_text() -> list[str]:
    """Load data.txt for help command."""
    with open(HELP_PATH, "r", encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f]