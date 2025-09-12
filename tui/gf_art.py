from __future__ import annotations
from pathlib import Path
from typing import Mapping, Optional

from textual.widgets import Static
from textual.reactive import reactive
from rich_pixels import Pixels
from PIL import Image
from rich.text import Text


class GlyphArt(Static):
    theme_name: str = reactive("")

    def __init__(
        self,
        image_map: Mapping[str, str],
        *,
        default_theme: str,
        art_size: tuple[int, int] = (100, 18),
        id: str = "gf-logo",
    ) -> None:
        super().__init__(id=id)
        self._image_map = dict(image_map)
        self._art_size = art_size
        self._current_path: Optional[Path] = None
        self.theme_name = default_theme

    def on_mount(self) -> None:
        self._apply_theme_image(self.theme_name)

    def watch_theme_name(self, value: str) -> None:
        self._apply_theme_image(value)

    def _resolve_path_for_theme(self, theme: str) -> Optional[Path]:
        raw = self._image_map.get(theme) or self._image_map.get("*") or None
        if not raw:
            return None
        p = Path(raw)
        return p if p.is_file() else None

    def _apply_theme_image(self, theme: str) -> None:
        path = self._resolve_path_for_theme(theme)
        if not path:
            self.update(Text("[glyph art missing]", justify="center"))
            return
        if self._current_path and path.exists() and path.samefile(self._current_path):
            return
        try:
            with Image.open(path) as im:
                im.load()
                pixels = Pixels.from_image(im, resize=self._art_size)
            self._current_path = path
            self.update(pixels)
            self.refresh(layout=True)
        except Exception:
            self.update(Text("[glyph art error]", justify="center"))
