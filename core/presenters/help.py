
def help_handler(ctx):
    from core.data_io import load_help_text
    for line in load_help_text():
        ctx.app.log_widget.write(line)