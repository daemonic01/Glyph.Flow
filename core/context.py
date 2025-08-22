from core.log import log
from core.config_loader import load_config

class Context:
    def __init__(self, *, app):
        self.app = app
        self.log = log
        self.msg = app.message_catalog
        self.schema = app.schema
        self.config = app.config

    @property
    def nodes(self):
        return self.app.nodes
    
    @property
    def confirm(self): return self.app.confirm

    def set_nodes(self, new_nodes):
        self.app.nodes = new_nodes

    
