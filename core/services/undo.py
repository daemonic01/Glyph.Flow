from core.controllers.command_result import CommandResult

def undo_handler(ctx, **kwargs) -> CommandResult:
    ctx.log.debug(f"UNDO before: undo={len(ctx.undo_redo.undo_stack)} redo={len(ctx.undo_redo.redo_stack)}")
    ok = ctx.undo_redo.undo(ctx)
    ctx.log.debug(f"UNDO  after: undo={len(ctx.undo_redo.undo_stack)} redo={len(ctx.undo_redo.redo_stack)}")
    if ok:
        try:
            if hasattr(ctx.presenter, "refresh"): ctx.presenter.refresh()
            if hasattr(ctx.app, "refresh"): ctx.app.refresh()
        except Exception: pass
    return CommandResult(code="success" if ok else "no_change", outcome=ok)

def redo_handler(ctx, **kwargs) -> CommandResult:
    ctx.log.debug(f"REDO before: undo={len(ctx.undo_redo.undo_stack)} redo={len(ctx.undo_redo.redo_stack)}")
    ok = ctx.undo_redo.redo(ctx)
    ctx.log.debug(f"REDO  after: undo={len(ctx.undo_redo.undo_stack)} redo={len(ctx.undo_redo.redo_stack)}")
    if ok:
        try:
            if hasattr(ctx.presenter, "refresh"): ctx.presenter.refresh()
            if hasattr(ctx.app, "refresh"): ctx.app.refresh()
        except Exception: pass
    return CommandResult(code="success" if ok else "no_change", outcome=ok)