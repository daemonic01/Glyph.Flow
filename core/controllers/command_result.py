from dataclasses import dataclass

@dataclass
class CommandResult:
    """
    Represents the outcome of a command execution.

    Attributes:
        code (str): A symbolic code identifying the result type
            (e.g. "success", "error", "search_results").
        outcome (bool): Whether the command succeeded (True) or failed (False).
        params (dict[str, Any] | None): Optional parameters used for
            formatting/logging messages (e.g. {"id": "01.02"}).
        payload (dict | None): Optional extra data attached to the result.
            Used for returning structured data (e.g. search matches).
    """
    def __init__(self, *, code: str, outcome: bool, params: dict | None = None, payload: dict | None = None):
        self.code = code
        self.outcome = bool(outcome)
        self.params = params or {}
        self.payload = payload or {}
    