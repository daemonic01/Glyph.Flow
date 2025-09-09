import time
from core.node import Node
from core.controllers.command_result import CommandResult


def bigsample_handler(ctx, *, branching: int = 10, depth: int = 4) -> CommandResult:
    """
    Create a large sample tree for performance testing, with timing info.

    Args:
        ctx: Application context (contains .app and its nodes).
        branching (int): number of children per node.
        depth (int): levels deep (root excluded).

    Returns:
        CommandResult: outcome of the operation with code, params, and timing.
    """
    try:
        start = time.perf_counter()

        # Root
        root = Node(name="BigSample", type="Project")
        root.id = Node.next_free_root_id(ctx.app.nodes)
        ctx.app.nodes.append(root)

        # Recursive builder
        def build(parent, level):
            if level >= depth:
                return
            for i in range(branching):
                child = Node(
                    name=f"{parent.name}_{level}_{i}",
                    type="Task" if level == depth - 1 else "Phase"
                )
                parent.add_child(child)
                build(child, level + 1)

        build(root, 0)

        total = count_nodes(root)
        elapsed = time.perf_counter() - start

        ctx.log.info(f"BigSample created with {total} nodes in {elapsed:.4f}s")

        return CommandResult(
            code="success",
            params={"branching": branching, "depth": depth,
                    "nodes": total, "time_sec": round(elapsed, 4)},
            outcome=True,
        )

    except Exception as e:
        ctx.log.error(f"BigSample creation failed: {e}")
        return CommandResult(code="error", params={"error": str(e)}, outcome=False)


def count_nodes(node):
    """Count all nodes in a tree rooted at `node`."""
    total = 1
    for child in node.children:
        total += count_nodes(child)
    return total
