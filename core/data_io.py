from pathlib import Path
import json
import os
from typing import List
from .node import Node

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "node_data.json"


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
    if not os.path.exists(filename):
        return []
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
        nodes = [Node.from_dict(entry) for entry in data]

        if nodes:
            max_root_id = max(int(n.id) for n in nodes if n.parent is None)
            Node._root_counter = max_root_id + 1
        else:
            Node._root_counter = 1

        return nodes



def create_sample_tree() -> List[Node]:
    """Create a predefined sample tree structure for testing and demonstration.

    Returns:
        List[Node]: A list containing a single root project with nested phases, tasks, and subtasks.
    """
    project = Node(name="Glyph.Flow", type="Project", short_desc="TUI workflow manager")

    
    phase1 = Node(name="Planning", type="Phase", short_desc="Design and requirements")
    project.add_child(phase1)

    task1 = Node(name="Define structure", type="Task", short_desc="Decide on Node model")
    phase1.add_child(task1)

    subtask1 = Node(name="Add progress support", type="Subtask", short_desc="Progress calculation logic")
    task1.add_child(subtask1) 

    phase2 = Node(name="Implementation", type="Phase", short_desc="Code the core system")
    project.add_child(phase2)

    task2 = Node(name="Write save/load", type="Task", short_desc="Create JSON I/O")
    phase2.add_child(task2)

    subtask2 = Node(name="Test with sample data", type="Subtask", short_desc="Load from file and inspect")
    task2.add_child(subtask2)

    return [project]

