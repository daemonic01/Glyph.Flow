from textual.widgets import Static
from rich_pixels import Pixels
from PIL import Image

class GlyphArt(Static):
    def __init__(self, image_path: str, width: int = None) -> None:
        super().__init__(id="gf-logo")
        with Image.open(image_path) as image:

            self.pixels = Pixels.from_image(image, resize=(100, 18))
    def render(self) -> Pixels:
        return self.pixels