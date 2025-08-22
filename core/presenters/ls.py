
def ls_handler(ctx):
    if ctx.app.nodes:
        ctx.log.info("Root nodes:")
        for n in ctx.app.nodes:
            ctx.log.info(f"- {n.name} ({n.type}, ID = {n.id})")
    else:
        ctx.log.key("file.no_data")
