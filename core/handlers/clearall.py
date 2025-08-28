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
        deleted = delete_data_file()
        ctx.app.nodes.clear()
        if deleted:
            return CommandResult("clear_done", outcome=True)
    except Exception as e:

        return CommandResult(code="file_not_found", outcome=False)