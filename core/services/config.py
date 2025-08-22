from typing import Optional
from core.controllers.command_result import CommandResult
from core.config_loader import save_config


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
    v = (value or "").strip().lower()
    if v in TRUE_WORDS:
        return True
    if v in FALSE_WORDS:
        return False
    return None


def config_handler(ctx, *, setting: Optional[str] = None, value: Optional[str] = None) -> CommandResult:
    """
    Set a boolean config value: config <setting> <on|off>
    Supported: autosave, assume_yes, logging  (alias: assume-yes, log)

    Returns codes:
      - unknown_key
      - invalid_value
      - set_success
      - no_change
    """


    key_in = setting.strip().lower()
    cfg_key = SUPPORTED_KEYS.get(key_in)
    if not cfg_key:
        return CommandResult(code="unknown_key", params={"setting": setting})


    b = _parse_bool(value)
    if b is None:
        return CommandResult(code="invalid_value", params={"k": key_in})


    cfg = getattr(ctx.app, "config", None)
    if cfg is None:

        cfg = {}
        setattr(ctx.app, "config", cfg)

    current = cfg.get(cfg_key)


    if current is not None and bool(current) == b:
        return CommandResult(code="no_change", params={"setting": cfg_key, "value": "ON" if b else "OFF"})


    cfg[cfg_key] = b
    try:
        save_config(cfg)
    except Exception as e:

        return CommandResult(code="error", params={"error": str(e)})

    return CommandResult(
        code="set_success",
        params={"setting": cfg_key, "value": "ON" if b else "OFF"},
        payload={"setting": cfg_key, "value": b},
    )
