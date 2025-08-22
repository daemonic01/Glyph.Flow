from dataclasses import dataclass
from typing import Optional
from core.log import log

@dataclass
class Pending:
    cmd: "Command"
    prompt: str

class ConfirmService:
    def __init__(self, app):
        self.app = app
        self.pending: Optional[Pending] = None

    def request(self, cmd: "Command", prompt: str):
        """Ask for approval and pause the command."""
        self.pending = Pending(cmd=cmd, prompt=prompt)
        log.info(prompt)

    def has_pending(self) -> bool:
        return self.pending is not None

    def handle_response(self, raw: str) -> bool:
        """
        Handles the next input if confirm is in progress.
        Returns: True = we have processed this input (y/n), False = not in confirm mode.
        """
        if not self.pending:
            return False

        ans = (raw or "").strip().lower()
        if ans in ("y", "yes"):
            cmd = self.pending.cmd

            cmd._confirmed = True
            cmd.paused = False
            self.pending = None

            cmd.execute()
        else:
            # minden más = cancel
            log.info("Cancelled.")
            self.pending = None
        return True
