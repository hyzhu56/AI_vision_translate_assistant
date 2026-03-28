import base64
import io
import logging

from PIL import Image, ImageGrab

logger = logging.getLogger(__name__)


def grab_fullscreen() -> Image.Image:
    """Capture the entire screen and return as PIL Image."""
    logger.debug("Capturing fullscreen screenshot")
    screenshot = ImageGrab.grab()
    logger.debug("Screenshot captured: %dx%d", screenshot.width, screenshot.height)
    return screenshot


def crop_region(image: Image.Image, x1: int, y1: int, x2: int, y2: int) -> Image.Image:
    """Crop a rectangular region from the image.

    Args:
        image: Source image.
        x1, y1: Top-left corner coordinates.
        x2, y2: Bottom-right corner coordinates.
    """
    return image.crop((x1, y1, x2, y2))


def image_to_base64(image: Image.Image) -> str:
    """Convert PIL Image to base64-encoded PNG string (no data URI prefix)."""
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    logger.debug("Image encoded to base64, length=%d", len(b64))
    return b64
