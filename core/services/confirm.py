from dataclasses import dataclass
from typing import Optional

@dataclass
class Pending:
    """
    Represents a paused, confirmation-pending command.
    
    Attributes:
        cmd (Command): The command waiting for confirmation.
        prompt (str): The message shown to the user.
    """
    cmd: "Command"
    prompt: str

class ConfirmService:
    """
    Service for handling destructive command confirmations (y/n prompts).

    Workflow:
        1. A destructive command calls `request()` → prompt is shown and command paused.
        2. The next user input is intercepted by `handle_response()`.
        3. If user confirms (y/yes) → command resumes and executes.
           Otherwise → command is cancelled.
    """

    def __init__(self, ctx):
        """
        Args:
            app: Reference to the GlyphApp (used for accessing nodes, log, etc.).
        """
        self.ctx = ctx
        self.pending: Optional[Pending] = None



    def request(self, cmd: "Command", prompt: str):
        """
        Ask the user for confirmation and pause the command.

        Args:
            cmd (Command): The command requesting confirmation.
            prompt (str): Message to display in the log.
        """
        self.pending = Pending(cmd=cmd, prompt=prompt)
        self.ctx.log.info(prompt)



    def has_pending(self) -> bool:
        """
        Returns:
            bool: True if a confirmation is currently pending, False otherwise.
        """
        return self.pending is not None



    def handle_response(self, raw: str) -> bool:
        """
        Handle the next user input while confirmation is pending.

        Args:
            raw (str): The user input (typically "y"/"yes" or "n"/"no").

        Returns:
            bool:
                - True if this input was handled as part of confirmation.
                - False if no confirmation was pending (input should be processed normally).
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
            self.ctx.log.info("Cancelled.")
            self.pending = None
        return True
