from pathlib import Path
import json
import os
from typing import List
from .node import Node





BASE_DIR = Path(__file__).resolve().parent.parent



def save_node_tree(ctx):
    """Save the given list of root nodes to a JSON file.

    Args:
        root_nodes (List[Node]): List of root-level Node objects to save.
        filename (str): Path to the JSON file where data will be written.
    """
    DATA_PATH = BASE_DIR / ctx.config.get("paths.data")

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump([node.to_dict() for node in ctx.app.nodes], f, indent=2, ensure_ascii=False)
    


def load_node_tree(ctx) -> List[Node]:
    """Load a node tree from a JSON file.

    Args:
        filename (str): Path to the JSON file to read.

    Returns:
        List[Node]: List of root-level Node objects loaded from file.
    """
    DATA_PATH = BASE_DIR / ctx.config.get("paths.data")

    try:
        if not os.path.exists(DATA_PATH):
            if not os.path.exists(DATA_PATH.parent):
                os.mkdir("data")
            with open(DATA_PATH, "w", encoding="utf-8") as f:
                json.dump([], f)
            return []
        
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            nodes = [Node.from_dict(entry) for entry in data]

            Node.relabel_missing_ids(nodes)

            return nodes
    except:
        ctx.log.key("file.load_error", filename=DATA_PATH)



def delete_data_file(ctx):
    """Delete the node data file if it exists. Returns True if deleted."""
    DATA_PATH = BASE_DIR / ctx.config.get("paths.data")
    
    if os.path.exists(DATA_PATH):
        os.remove(DATA_PATH)
        return True
    return False





def load_help_text(ctx) -> list[str]:
    """Load data.txt for help command."""

    HELP_PATH = BASE_DIR / ctx.config.get("paths.help")

    with open(HELP_PATH, "r", encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f]