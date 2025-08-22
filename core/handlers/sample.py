from core.node import Node
from core.controllers.command_result import CommandResult


class SampleTreeError(Exception):
    """Raised when sample tree creation fails."""

def sample_handler(ctx) -> CommandResult:
    """Create a predefined sample tree structure for testing and demonstration.

    Returns:
        List[Node]: A list containing a single root project with nested phases, tasks, and subtasks.
    """
    try:
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

        ctx.config["custom_schema"] = ctx.config["default_schema"]
        ctx.nodes.append(project)
        return CommandResult("success")
    
    except SampleTreeError as e:
        ctx.log.error(str(e))