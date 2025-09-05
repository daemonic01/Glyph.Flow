from typing import Optional
from core.controllers.command_result import CommandResult


SUPPORTED_KEYS = {
    "autosave": "autosave",
    "assume_yes": "assume_yes",
    "assume-yes": "assume_yes",
    "logging": "logging",
    "log": "logging",
}

TRUE_WORDS = {"on", "true", "yes", "y", "1"}
FALSE_WORDS = {"off", "false", "no", "n", "0"}


def _parse_bool(value: str) -> Optional[bool]:
    """
    Convert a string to a boolean.

    Args:
        value (str): User-provided input (e.g. "on", "off", "true", "false").

    Returns:
        bool | None: True or False if recognized, None otherwise.
    """
    v = (value or "").strip().lower()
    if v in TRUE_WORDS:
        return True
    if v in FALSE_WORDS:
        return False
    return None


def config_handler(ctx, *, setting: Optional[str] = None, value: Optional[str] = None) -> CommandResult:
    """
    Handler for the 'config' command.

    Sets a boolean configuration value in the app's config and persists it
    to disk. Only supports predefined keys.

    Usage:
        config <setting> <on|off>

    Supported keys:
        - autosave
        - assume_yes (alias: assume-yes)
        - logging (alias: log)

    Return codes:
        - "unknown_key"  → setting not supported
        - "invalid_value" → value not recognized as boolean
        - "no_change" → already set to given value
        - "set_success" → updated successfully
        - "error" → saving to file failed
    """

    key_in = setting.strip().lower()
    cfg_key = SUPPORTED_KEYS.get(key_in)
    if not cfg_key:
        return CommandResult(code="unknown_key", params={"setting": setting}, outcome=False)


    b = _parse_bool(value)
    if b is None:
        return CommandResult(code="invalid_value", params={"k": key_in}, outcome=False)



    current = ctx.config.get(cfg_key)


    if current is not None and bool(current) == b:
        return CommandResult(code="no_change", params={"setting": cfg_key, "value": "ON" if b else "OFF"}, outcome=False)

    # Update and persist
    ctx.config.edit(cfg_key, b)
    try:
        ctx.config.save()
    except Exception as e:

        return CommandResult(code="error", params={"error": str(e)}, outcome=False)

    return CommandResult(
        code="set_success",
        params={"setting": cfg_key, "value": "ON" if b else "OFF"},
        payload={"setting": cfg_key, "value": b}, outcome=True
    )
