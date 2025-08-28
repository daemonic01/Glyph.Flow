
def clear_handler(ctx):
    """
    Clear the log widgets.

    Args:
        ctx: Application context (must provide ctx.app.output_widget and ctx.nodes).
            
    """
    ctx.app.log_widget.clear()
    ctx.app.output_widget.clear()