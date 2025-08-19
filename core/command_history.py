from collections import deque
from typing import Deque, Optional

class CommandHistory:
    def __init__(self, maxlen: int = 200) -> None:
        self._items: Deque[str] = deque(maxlen=maxlen)
        self._cursor: int = 0

    def add(self, cmd: str) -> None:
        cmd = cmd.strip()
        if not cmd:
            self.reset()
            return
        if not self._items or self._items[-1] != cmd:
            self._items.append(cmd)
        self.reset()

    def reset(self) -> None:
        self._cursor = len(self._items)

    def prev(self) -> Optional[str]:
        if not self._items:
            return None
        if self._cursor > 0:
            self._cursor -= 1
        return self._items[self._cursor]

    def next(self) -> Optional[str]:
        if not self._items:
            return None
        if self._cursor < len(self._items) - 1:
            self._cursor += 1
            return self._items[self._cursor]
        # end: “üres” input
        self._cursor = len(self._items)
        return ""