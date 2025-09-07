from core.data_io import delete_data_file
from core.controllers.command_result import CommandResult


def clearall_handler(ctx):
    """
    Handler for the 'clearall' command.

    Behavior:
        - Deletes the underlying data file (if it exists).
        - Clears the in-memory node tree.
        - Returns a CommandResult indicating success or failure.

    Args:
        ctx: Application context (contains .app and its nodes).

    Returns:
        CommandResult: 
            - code="clear_done" if the file was deleted successfully.
            - code="file_not_found" if deletion failed or file missing.
    """
    try:
        deleted = delete_data_file(ctx)
    except Exception as e:
        try:
            ctx.log.error(f"clearall: failed to delete data file: {e}")
        except Exception:
            pass
        return CommandResult(code="error_deleting_file", outcome=False, params={"error": str(e)})

    try:
        ctx.app.nodes.clear()
    except Exception as e:
        try:
            ctx.log.error(f"clearall: failed to clear in-memory nodes: {e}")
        except Exception:
            pass
        return CommandResult(code="error_clearing_memory", outcome=False, params={"error": str(e)})

    if deleted:
        return CommandResult(code="clear_done", outcome=True)
    else:
        return CommandResult(code="file_not_found", outcome=False)