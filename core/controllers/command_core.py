from enum import Enum, auto
from typing import Optional, Any

from core.controllers.command_result import CommandResult
from core.errors.command_errors import (
    CommandError, ExecutionError, TellError
)

class CommandState(Enum):

    INIT = auto()
    EXECUTION = auto()
    TELL = auto()
    DONE = auto()

    INIT_ERROR = auto()
    EXECUTION_ERROR = auto()
    TELL_ERROR = auto()
    FAILED = auto()

_PHASE_ERR = {
    "INIT": CommandState.INIT_ERROR,
    "EXECUTION": CommandState.EXECUTION_ERROR,
    "TELL": CommandState.TELL_ERROR,
}

class Command:
    def __init__(self, ctx, name, raw, spec, params, handler, mutate, destructive):
        self.ctx = ctx
        self.name = name
        self.raw = raw
        self.spec = spec
        self.params = params or {}
        self.handler = handler
        self.state = CommandState.INIT
        self.mutate = mutate
        self.destructive = destructive
        self.paused = False
        self._confirmed = False

    def _tell(self, result: Any, error: Optional[Exception] = None) -> None:
        msgs = (self.spec.get("messages") or {})
        if error:
            self.ctx.log.debug(error)
            code = getattr(error, "code", None)
            params = getattr(error, "params", {}) or {"error": str(error)}
            key = (msgs.get(code) if code else None) or msgs.get("error") or "system.unexpected_error"
            self.ctx.log.key(key, **params)
            

        if isinstance(result, CommandResult):
            key = msgs.get(result.code)
            if key:
                self.ctx.log.key(key, **(result.params or {}))

            if result.code == "search_results":
                try:
                    payload = result.payload or {}
                    matches = payload.get("matches") or []
                    if matches:
                        from core.presenters.search_table import render_search_results
                        render_search_results(self.ctx, matches)
                        return
                except Exception as _:
                    pass
        
        if "success" in msgs:
            pass


    def execute(self) -> Any:
        if self.destructive and not self.ctx.config["assume_yes"] and not self._confirmed:
            self.ctx.confirm.request(self, prompt=f"Execute '{self.name}'? This cannot be undone. (y/n)")
            self.paused = True
            return

        # EXECUTION
        self.state = CommandState.EXECUTION
        try:
            result = self.handler(self.ctx, **self.params)

        except CommandError as e:
            self.state = _PHASE_ERR["EXECUTION"]; self._tell(None, e); return None
        except Exception as e:
            self.state = _PHASE_ERR["EXECUTION"]; self._tell(None, ExecutionError(str(e))); return None

        

        # TELL
        self.state = CommandState.TELL
        try:
            self._tell(result, None)
        except CommandError as e:
            self.state = _PHASE_ERR["TELL"]; self._tell(None, e); return None
        except Exception as e:
            self.state = _PHASE_ERR["TELL"]; self._tell(None, TellError(str(e))); return None

        

        # AUTOSAVE (do it centrally if command mutates)
        if self.mutate and self.ctx.config["autosave"]:
            from core.data_io import save_node_tree
            from core.config_loader import save_config
            try:
                save_node_tree(self.ctx.nodes)
                save_config(self.ctx.config)
                self.ctx.log.key("system.autosave_done")
            except Exception as e:
                self.ctx.log.key("system.autosave_failed", error=e)

        self.state = CommandState.DONE
        return result