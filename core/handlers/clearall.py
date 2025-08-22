from core.data_io import delete_data_file
from core.controllers.command_result import CommandResult


def clearall_handler(ctx):
    try:
        deleted = delete_data_file()
        ctx.app.nodes.clear()
        if deleted:
            return CommandResult("clear_done")
    except Exception as e:

        return CommandResult(code="file_not_found")