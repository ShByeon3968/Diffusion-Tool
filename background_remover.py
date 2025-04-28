from rembg import remove
from PIL import Image
import io

class BackgroundRemover:
    def __init__(self):
        pass

    def remove_background(self, input_image: bytes) -> bytes:
        # input_image: PIL.Image
        output_image = remove(input_image)
        return output_image