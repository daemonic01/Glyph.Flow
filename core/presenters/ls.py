
def ls_handler(ctx):
    """
    Handler for the 'ls' command.

    Lists all root-level nodes in the current tree.  
    Each node is displayed with its name, type, and ID.

    Behavior:
        - If root nodes exist → prints them via `ctx.presenter`.
        - If no data is loaded → logs a "no_data" message via `ctx.log`.

    Args:
        ctx: Application context (must provide ctx.app.nodes, ctx.presenter, ctx.log).
    """
    if ctx.app.nodes:
        ctx.app.output_widget.write("[bold white]\nRoot nodes:")
        for n in ctx.app.nodes:
            ctx.app.output_widget.write(f"[#FDC483]- {n.name} ({n.type}, ID = {n.id})")

            if ctx.config.get("test_mode") == True:
                from core.controllers.command_result import CommandResult
                return CommandResult(code="success", outcome=True)
    else:
        ctx.log.key("file.no_data")