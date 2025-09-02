from core.controllers.command_result import CommandResult

def undo_handler(ctx, **kwargs) -> CommandResult:
    """
    Handle the 'undo' command.

    Pops the most recent Diff from the undo stack, applies its
    backward actions to revert the last change, and pushes it
    onto the redo stack. Also triggers UI refresh if supported.

    Args:
        ctx (Context): Shared application context.
        **kwargs: Unused extra parameters (ignored).

    Returns:
        CommandResult:
            - code="success", outcome=True if an undo was performed.
            - code="no_change", outcome=False if nothing to undo.
    """
    ok = ctx.undo_redo.undo(ctx)
    if ok:
        try:
            if hasattr(ctx.presenter, "refresh"): ctx.presenter.refresh()
            if hasattr(ctx.app, "refresh"): ctx.app.refresh()
        except Exception: pass
    return CommandResult(code="success" if ok else "no_change", outcome=ok)



def redo_handler(ctx, **kwargs) -> CommandResult:
    """
    Handle the 'redo' command.

    Pops the most recent Diff from the redo stack, applies its
    forward actions to reapply a previously undone change, and
    pushes it back onto the undo stack. Also triggers UI refresh
    if supported.

    Args:
        ctx (Context): Shared application context.
        **kwargs: Unused extra parameters (ignored).

    Returns:
        CommandResult:
            - code="success", outcome=True if a redo was performed.
            - code="no_change", outcome=False if nothing to redo.
    """
    ok = ctx.undo_redo.redo(ctx)
    if ok:
        try:
            if hasattr(ctx.presenter, "refresh"): ctx.presenter.refresh()
            if hasattr(ctx.app, "refresh"): ctx.app.refresh()
        except Exception: pass
    return CommandResult(code="success" if ok else "no_change", outcome=ok)