from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class CommandResult:
    code: str               # pl. "success", "created_root", "created_child", "not_found", "invalid_usage"...
    params: Dict[str, Any] = None
    payload: Optional[Dict] = None