from core.node import Node
from core.controllers.command_result import CommandResult


class SampleTreeError(Exception):
    """Raised when sample tree creation fails."""

def sample_handler(ctx) -> CommandResult:
    """Create a predefined sample tree structure for testing and demonstration.

    Returns:
        CommandResult: outcome of the operation with appropriate code and params.
    """
    try:

        # ROOT
        root = Node(name="Glyph.Flow", type="Project")
        root.id = Node.next_free_root_id(ctx.app.nodes)
        ctx.app.nodes.append(root)

        # Level 1
        planning = Node(name="Planning", type="Phase")
        impl     = Node(name="Implementation", type="Phase")
        tests    = Node(name="Test with sample data", type="Phase")

        root.add_child(planning)
        root.add_child(impl)
        root.add_child(tests)

        # level 2
        define  = Node(name="Define structure", type="Task")
        addprog = Node(name="Add progress support", type="Task")

        planning.add_child(define)
        planning.add_child(addprog)

        save_load = Node(name="Write save/load", type="Task")
        impl.add_child(save_load)
        return CommandResult(code="success", outcome=True)
    
    except SampleTreeError as e:
        ctx.log.error(str(e))