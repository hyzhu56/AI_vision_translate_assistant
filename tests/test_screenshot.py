import base64
import io

from PIL import Image

from core.screenshot import crop_region, image_to_base64


def _make_test_image(width=200, height=100):
    """Create a solid red test image."""
    return Image.new("RGB", (width, height), color=(255, 0, 0))


def test_crop_region_returns_correct_size():
    """Cropped image matches requested dimensions."""
    img = _make_test_image(800, 600)
    cropped = crop_region(img, 10, 20, 110, 120)
    assert cropped.size == (100, 100)


def test_crop_region_preserves_content():
    """Cropped region contains pixels from the original image."""
    img = _make_test_image(200, 200)
    cropped = crop_region(img, 0, 0, 50, 50)
    pixel = cropped.getpixel((0, 0))
    assert pixel == (255, 0, 0)


def test_image_to_base64_returns_valid_string():
    """Base64 output is a non-empty string."""
    img = _make_test_image()
    b64 = image_to_base64(img)
    assert isinstance(b64, str)
    assert len(b64) > 0


def test_image_to_base64_roundtrip():
    """Base64 string decodes back to a valid PNG image."""
    img = _make_test_image(50, 50)
    b64 = image_to_base64(img)
    decoded_bytes = base64.b64decode(b64)
    recovered = Image.open(io.BytesIO(decoded_bytes))
    assert recovered.size == (50, 50)
