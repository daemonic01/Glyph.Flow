from enum import Enum, auto
from typing import Optional, Any

from core.controllers.command_result import CommandResult
from core.errors.command_errors import (
    CommandError, ExecutionError, TellError
)

class CommandState(Enum):
    """
    Represents the lifecycle state of a Command.
    A Command transitions through INIT → EXECUTION → TELL → DONE,
    or into one of the error/failed states.
    """

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
    """
    Encapsulates the full lifecycle of a user command.

    - Created via `command_factory.summon()`.
    - Executes a registered handler with given parameters.
    - Handles confirmation for destructive commands.
    - Logs results and errors via the `log` system.
    - Performs autosave if configured and the command mutates data.
    """

    def __init__(self, ctx, name, raw, spec, params, handler, mutate, mutate_config, destructive):
        """
        Args:
            ctx: Application context (services, log, config, nodes, etc.)
            name: Name of the command (e.g. "create")
            raw: Raw input string from the user
            spec: Command spec dict from registry
            params: Parsed parameters (dict) passed to handler
            handler: Callable handler for this command
            mutate: Whether command mutates data (for autosave)
            destructive: Whether command is destructive (requires confirm)
        """

        self.ctx = ctx
        self.name = name
        self.raw = raw
        self.spec = spec
        self.params = params or {}
        self.handler = handler
        self.state = CommandState.INIT
        self.mutate = mutate
        self.mutate_config = mutate_config
        self.destructive = destructive
        self.paused = False
        self._confirmed = False

    def _tell(self, result: Any, error: Optional[Exception] = None) -> None:
        """
        Handle reporting/logging of the command outcome.

        Args:
            result: Handler return value (CommandResult)
            error: Exception to report (optional)

        Behavior:
            - If error: log appropriate error key or fallback.
            - If result is CommandResult: log messages based on result code.
            - Special case: render search results in table format.
        """

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


    def execute(self) -> Any:
        """
        Run the command lifecycle:
        - confirm if destructive
        - execute handler
        - tell/log result
        - perform autosave if needed

        Returns:
            CommandResult or None
        """

        if self.destructive and not self.ctx.config["assume_yes"] and not self._confirmed:
            self.ctx.confirm.request(self, prompt=f"Execute '{self.name}'? This cannot be undone. (y/n)")
            self.paused = True
            return

        # [EXECUTION]
        self.state = CommandState.EXECUTION
        try:
            result = self.handler(self.ctx, **self.params)

        except CommandError as e:
            self.state = _PHASE_ERR["EXECUTION"]; self._tell(None, e); return None
        except Exception as e:
            self.state = _PHASE_ERR["EXECUTION"]; self._tell(None, ExecutionError(str(e))); return None

        

        # [TELL]
        self.state = CommandState.TELL
        try:
            self._tell(result, None)
        except CommandError as e:
            self.state = _PHASE_ERR["TELL"]; self._tell(None, e); return None
        except Exception as e:
            self.state = _PHASE_ERR["TELL"]; self._tell(None, TellError(str(e))); return None

        

        # [AUTOSAVE] (do it centrally if command mutates)
        success = isinstance(result, CommandResult) and bool(getattr(result, "outcome", False))

        if success and self.mutate and self.ctx.config["autosave"]:
            from core.data_io import save_node_tree
            try:
                save_node_tree(self.ctx.nodes)
                self.ctx.log.key("system.autosave_done")
            except Exception as e:
                self.ctx.log.key("system.autosave_failed", error=e)

        if success and self.mutate_config:
            from core.config_loader import save_config
            try:
                save_config(self.ctx.config)
                self.ctx.log.key("system.config_save_done")
            except Exception as e:
                self.ctx.log.key("system.config_save_failed", error=e)


        # record diff if provided by handler
        if success and self.mutate:
            diff = None
            if hasattr(result, "payload") and isinstance(result.payload, dict):
                diff = result.payload.get("diff")

            if diff is not None:
                try:
                    self.ctx.undo_redo.record(diff)
                except Exception as e:
                    self.ctx.log.key(f"unexpected_error\n{e}")

        self.state = CommandState.DONE if success else CommandState.FAILED
        return result