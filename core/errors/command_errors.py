

class CommandError(Exception):
    """Base error for command pipeline."""
    phase: str  # "INIT" | "BEFORE" | "EXECUTION" | "AFTER" | "TELL"
    def __init__(self, message: str = "", *, phase: str = "EXECUTION", code: str | None = None, params: dict | None = None):
        super().__init__(message)
        self.code = code
        self.params = params or {}
        self.phase = phase


# INIT (parser/factory/registry)
class UnknownCommandError(CommandError):
    def __init__(self, name: str):
        super().__init__(f"Unknown command: {name}", phase="INIT")

class ParseError(CommandError):
    def __init__(self, message: str):
        super().__init__(message, phase="INIT")

class ValidationError(CommandError):
    def __init__(self, message: str):
        super().__init__(message, phase="INIT")


# BEFORE / EXECUTION / AFTER / TELL
class BeforeEventError(CommandError):
    def __init__(self, message: str):
        super().__init__(message, phase="BEFORE")

class ExecutionError(CommandError):
    def __init__(self, message: str):
        super().__init__(message, phase="EXECUTION")

class AfterEventError(CommandError):
    def __init__(self, message: str):
        super().__init__(message, phase="AFTER")

class TellError(CommandError):
    def __init__(self, message: str):
        super().__init__(message, phase="TELL")
