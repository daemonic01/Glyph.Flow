from textual.widgets import Static
from rich_pixels import Pixels
from PIL import Image

class GlyphArt(Static):
    def __init__(self, image_path: str, width: int = None) -> None:
        super().__init__(id="gf-logo")
        with Image.open(image_path) as image:
            self.pixels = list(image.getdata())

            # Standardize text color by a neutral color
            standardized_image = Image.new("RGB", image.size)
            new_color = (255, 191, 0)
            modified_pixels = [new_color if pixel >= (1, 1, 1) else pixel for pixel in self.pixels]
            standardized_image.putdata(modified_pixels)
            

            modified_bg_image = Image.new("RGB", standardized_image.size)
            new_color = (133, 27, 27)
            self.pixels = list(standardized_image.getdata())
            modified_pixels = [new_color if pixel < (1, 1, 1) else pixel for pixel in self.pixels]
            modified_bg_image.putdata(modified_pixels)

            modified_image = Image.new("RGB", modified_bg_image.size)
            new_color = (0, 0, 0)
            self.pixels = list(modified_bg_image.getdata())
            modified_pixels = [new_color if pixel > (133, 27, 27) else pixel for pixel in self.pixels]
            modified_image.putdata(modified_pixels)

            self.pixels = Pixels.from_image(modified_image, resize=(100, 18))
    def render(self) -> Pixels:
        return self.pixels