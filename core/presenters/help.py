
def help_handler(ctx):
    """
    Handler for the 'help' command.

    Loads and displays the help text file line by line into the app's
    output widget. The help text is usually stored under the path defined
    in the config (e.g. `assets/help.txt`).

    Args:
        ctx: Application context (must provide ctx.app.output_widget).
    """
    from core.data_io import load_help_text
    for line in load_help_text(ctx):
        ctx.app.output_widget.write(line)