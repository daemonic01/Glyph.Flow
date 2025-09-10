
from collections import deque

def clear_handler(ctx):
    """
    Clear the log widgets.

    Args:
        ctx: Application context (must provide ctx.app.output_widget and ctx.nodes).
            
    """
    ctx.app.log_widget.clear()
    ctx.app.log_widget._buffer = []
    ctx.app.output_widget.clear()
    ctx.app.output_widget._buffer = []

    if ctx.config.get("test_mode") == True:
        from core.controllers.command_result import CommandResult
        return CommandResult(code="success", outcome=True)