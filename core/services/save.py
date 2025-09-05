from core.controllers.command_result import CommandResult
from core.data_io import save_node_tree


def save_handler(ctx) -> CommandResult:
    """
    Handler for the 'save' command.

    Persists the current in-memory node tree to the configured data file.

    Args:
        ctx: Application context (must provide ctx).

    Returns:
        CommandResult:
            - code="manual_save_completed" with outcome=True on success.
            - code="manual_save_failed" with outcome=False if an error occurs.
    """
    try:
        save_node_tree(ctx)
        return CommandResult(
            code="manual_save_completed",
            outcome=True
        )
    except Exception as e:
        return CommandResult(
            code="manual_save_failed",
            params={"error": str(e)},
            outcome=False
        )
