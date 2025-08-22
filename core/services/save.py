from core.controllers.command_result import CommandResult
from core.data_io import save_node_tree

def save_handler(ctx):
    save_node_tree(ctx.app.nodes)
    return CommandResult("manual_save_completed")