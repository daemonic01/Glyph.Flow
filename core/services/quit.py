
def quit_handler(ctx):
    """
    Handler for the 'quit' command.

    Performs a graceful shutdown of the application:
      - Closes the logging system (ctx.log).
      - Closes the presenter logger (ctx.presenter).
      - Exits the Textual application (ctx.app.exit()).

    Args:
        ctx: Application context (provides log, app, presenter).
    """
    ctx.log.close()
    ctx.app.presenter.close()
    ctx.app.exit()