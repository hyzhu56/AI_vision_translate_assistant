# AI Vision Translate Assistant Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Windows desktop floating tool that captures screen regions via global hotkey, sends them to Kimi 2.5 API for translation/code analysis, and displays streaming Markdown results in a floating panel.

**Architecture:** Multi-threaded PyQt6 app. Main thread runs Qt event loop (UI). Daemon thread listens for Ctrl+CapsLock via pynput. QThread worker handles streaming API calls. All cross-thread communication via Qt signal/slot.

**Tech Stack:** Python, PyQt6, pynput, Pillow, openai, python-dotenv, pytest, pytest-qt

---

## File Map

| File | Responsibility |
|------|---------------|
| `requirements.txt` | Project dependencies |
| `.env.example` | Template for API keys |
| `config.py` | Load and validate .env config |
| `core/__init__.py` | Package marker |
| `core/screenshot.py` | Full-screen capture, crop region, image→base64 |
| `core/api_client.py` | QThread worker: streaming openai API call |
| `core/hotkey_listener.py` | QThread daemon: pynput Ctrl+CapsLock listener |
| `ui/__init__.py` | Package marker |
| `ui/overlay_window.py` | Full-screen overlay with region selection |
| `ui/floating_panel.py` | Result panel: frosted dark style, pin, markdown |
| `ui/tray_icon.py` | System tray icon with exit menu |
| `main.py` | App entry: wire all components, parse --debug |
| `tests/__init__.py` | Package marker |
| `tests/test_config.py` | Config loading tests |
| `tests/test_screenshot.py` | Screenshot + base64 tests |
| `tests/test_api_client.py` | API client mock tests |

---

### Task 1: Project Scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `core/__init__.py`
- Create: `ui/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create requirements.txt**

```
PyQt6>=6.6.0
pynput>=1.7.6
Pillow>=10.0.0
openai>=1.0.0
python-dotenv>=1.0.0
pytest>=7.0.0
pytest-qt>=4.2.0
```

- [ ] **Step 2: Create .env.example**

```
KIMI_API_KEY=sk-your-api-key-here
KIMI_API_BASE=https://api.moonshot.cn/v1
```

- [ ] **Step 3: Create .gitignore**

```
__pycache__/
*.pyc
.env
.venv/
*.egg-info/
dist/
build/
.pytest_cache/
.superpowers/
```

- [ ] **Step 4: Create package __init__.py files**

Create empty files:
- `core/__init__.py`
- `ui/__init__.py`
- `tests/__init__.py`

- [ ] **Step 5: Install dependencies**

Run: `pip install -r requirements.txt`
Expected: All packages install successfully.

- [ ] **Step 6: Commit**

```bash
git add requirements.txt .env.example .gitignore core/__init__.py ui/__init__.py tests/__init__.py
git commit -m "chore: project scaffolding with dependencies and package structure"
```

---

### Task 2: Config Module

**Files:**
- Create: `config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing tests for config**

Create `tests/test_config.py`:

```python
import os
import pytest


def test_load_config_success(tmp_path, monkeypatch):
    """Valid .env file loads both keys correctly."""
    env_file = tmp_path / ".env"
    env_file.write_text("KIMI_API_KEY=sk-test123\nKIMI_API_BASE=https://api.moonshot.cn/v1\n")
    monkeypatch.chdir(tmp_path)

    from config import load_config

    cfg = load_config(str(env_file))
    assert cfg["api_key"] == "sk-test123"
    assert cfg["api_base"] == "https://api.moonshot.cn/v1"


def test_load_config_missing_file(tmp_path, monkeypatch):
    """Missing .env file raises FileNotFoundError."""
    monkeypatch.chdir(tmp_path)

    from config import load_config

    with pytest.raises(FileNotFoundError, match=".env"):
        load_config(str(tmp_path / ".env"))


def test_load_config_empty_key(tmp_path, monkeypatch):
    """Empty KIMI_API_KEY raises ValueError."""
    env_file = tmp_path / ".env"
    env_file.write_text("KIMI_API_KEY=\nKIMI_API_BASE=https://api.moonshot.cn/v1\n")
    monkeypatch.chdir(tmp_path)

    from config import load_config

    with pytest.raises(ValueError, match="KIMI_API_KEY"):
        load_config(str(env_file))


def test_load_config_missing_key(tmp_path, monkeypatch):
    """Missing KIMI_API_KEY raises ValueError."""
    env_file = tmp_path / ".env"
    env_file.write_text("KIMI_API_BASE=https://api.moonshot.cn/v1\n")
    monkeypatch.chdir(tmp_path)

    from config import load_config

    with pytest.raises(ValueError, match="KIMI_API_KEY"):
        load_config(str(env_file))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_config.py -v`
Expected: All 4 tests FAIL with `ModuleNotFoundError` or `ImportError`.

- [ ] **Step 3: Implement config.py**

Create `config.py`:

```python
import os
from pathlib import Path

from dotenv import load_dotenv


def load_config(env_path: str = ".env") -> dict:
    """Load and validate configuration from .env file.

    Returns dict with keys: api_key, api_base.
    Raises FileNotFoundError if .env missing, ValueError if keys invalid.
    """
    env_file = Path(env_path)
    if not env_file.exists():
        raise FileNotFoundError(f".env file not found at: {env_path}")

    load_dotenv(env_file, override=True)

    api_key = os.getenv("KIMI_API_KEY", "").strip()
    api_base = os.getenv("KIMI_API_BASE", "https://api.moonshot.cn/v1").strip()

    if not api_key:
        raise ValueError("KIMI_API_KEY is missing or empty in .env file")

    return {
        "api_key": api_key,
        "api_base": api_base,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_config.py -v`
Expected: All 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add config.py tests/test_config.py
git commit -m "feat: config module with .env loading and validation"
```

---

### Task 3: Screenshot Module

**Files:**
- Create: `core/screenshot.py`
- Create: `tests/test_screenshot.py`

- [ ] **Step 1: Write failing tests for screenshot**

Create `tests/test_screenshot.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_screenshot.py -v`
Expected: All 4 tests FAIL with `ImportError`.

- [ ] **Step 3: Implement core/screenshot.py**

Create `core/screenshot.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_screenshot.py -v`
Expected: All 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add core/screenshot.py tests/test_screenshot.py
git commit -m "feat: screenshot module with crop and base64 conversion"
```

---

### Task 4: API Client Module

**Files:**
- Create: `core/api_client.py`
- Create: `tests/test_api_client.py`

- [ ] **Step 1: Write failing tests for API client**

Create `tests/test_api_client.py`:

```python
from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtCore import QCoreApplication

from core.api_client import ApiWorker

SYSTEM_PROMPT = (
    "你是一个智能视觉助手。请分析用户提供的图片。"
    "如果图片主体是普通英文文本，请提供信达雅的中文翻译。"
    "如果图片主体是编程代码，请提供深度的代码解析"
    "（包含编程逻辑、语法解析、关键函数分析）。"
    "使用 Markdown 格式输出。"
)


@pytest.fixture(autouse=True)
def qapp():
    """Ensure QCoreApplication exists for signal/slot tests."""
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    yield app


def _make_mock_chunk(content: str):
    """Create a mock streaming chunk with the given content."""
    choice = MagicMock()
    choice.delta.content = content
    chunk = MagicMock()
    chunk.choices = [choice]
    return chunk


def _make_mock_empty_chunk():
    """Create a mock streaming chunk with None content (final chunk)."""
    choice = MagicMock()
    choice.delta.content = None
    chunk = MagicMock()
    chunk.choices = [choice]
    return chunk


@patch("core.api_client.OpenAI")
def test_stream_chunks_emitted(mock_openai_cls):
    """Each chunk's content is emitted via stream_chunk signal."""
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = iter([
        _make_mock_chunk("Hello"),
        _make_mock_chunk(" World"),
        _make_mock_empty_chunk(),
    ])

    worker = ApiWorker("fake-key", "https://api.example.com/v1", "dGVzdA==")
    received = []
    worker.stream_chunk.connect(lambda text: received.append(text))

    worker.run()

    assert received == ["Hello", " World"]


@patch("core.api_client.OpenAI")
def test_stream_done_emitted(mock_openai_cls):
    """stream_done signal fires after all chunks are consumed."""
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = iter([
        _make_mock_chunk("Hi"),
        _make_mock_empty_chunk(),
    ])

    worker = ApiWorker("fake-key", "https://api.example.com/v1", "dGVzdA==")
    done_called = []
    worker.stream_done.connect(lambda: done_called.append(True))

    worker.run()

    assert done_called == [True]


@patch("core.api_client.OpenAI")
def test_stream_error_on_exception(mock_openai_cls):
    """Network errors are caught and emitted via stream_error signal."""
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.side_effect = Exception("Connection refused")

    worker = ApiWorker("fake-key", "https://api.example.com/v1", "dGVzdA==")
    errors = []
    worker.stream_error.connect(lambda msg: errors.append(msg))

    worker.run()

    assert len(errors) == 1
    assert "Connection refused" in errors[0]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_api_client.py -v`
Expected: All 3 tests FAIL with `ImportError`.

- [ ] **Step 3: Implement core/api_client.py**

Create `core/api_client.py`:

```python
import logging

from openai import OpenAI
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "你是一个智能视觉助手。请分析用户提供的图片。"
    "如果图片主体是普通英文文本，请提供信达雅的中文翻译。"
    "如果图片主体是编程代码，请提供深度的代码解析"
    "（包含编程逻辑、语法解析、关键函数分析）。"
    "使用 Markdown 格式输出。"
)


class ApiWorker(QThread):
    """Worker thread that calls Kimi API with streaming and emits results."""

    stream_chunk = pyqtSignal(str)
    stream_done = pyqtSignal()
    stream_error = pyqtSignal(str)

    def __init__(self, api_key: str, api_base: str, image_base64: str):
        super().__init__()
        self._api_key = api_key
        self._api_base = api_base
        self._image_base64 = image_base64

    def run(self):
        try:
            client = OpenAI(api_key=self._api_key, base_url=self._api_base)
            logger.debug("Starting streaming API request")

            response = client.chat.completions.create(
                model="kimi-latest",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{self._image_base64}"
                                },
                            }
                        ],
                    },
                ],
                stream=True,
                timeout=15,
            )

            chunk_count = 0
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    text = chunk.choices[0].delta.content
                    self.stream_chunk.emit(text)
                    chunk_count += 1

            logger.debug("Stream complete, received %d chunks", chunk_count)
            self.stream_done.emit()

        except Exception as e:
            logger.error("API request failed: %s", e)
            self.stream_error.emit(str(e))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_api_client.py -v`
Expected: All 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add core/api_client.py tests/test_api_client.py
git commit -m "feat: API client with streaming and signal-based output"
```

---

### Task 5: Hotkey Listener

**Files:**
- Create: `core/hotkey_listener.py`

- [ ] **Step 1: Implement core/hotkey_listener.py**

Note: pynput hotkey listening is inherently tied to OS input events and cannot be meaningfully unit-tested in a headless environment. We verify it manually in Task 9.

Create `core/hotkey_listener.py`:

```python
import logging

from pynput import keyboard
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


class HotkeyThread(QThread):
    """Daemon thread that listens for Ctrl+CapsLock global hotkey."""

    triggered = pyqtSignal()

    def run(self):
        logger.debug("Hotkey listener started, waiting for Ctrl+CapsLock")

        ctrl_pressed = False

        def on_press(key):
            nonlocal ctrl_pressed
            if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
                ctrl_pressed = True
            elif key == keyboard.Key.caps_lock and ctrl_pressed:
                logger.debug("Hotkey Ctrl+CapsLock detected")
                self.triggered.emit()

        def on_release(key):
            nonlocal ctrl_pressed
            if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
                ctrl_pressed = False

        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()
```

- [ ] **Step 2: Commit**

```bash
git add core/hotkey_listener.py
git commit -m "feat: global hotkey listener for Ctrl+CapsLock via pynput"
```

---

### Task 6: Overlay Window

**Files:**
- Create: `ui/overlay_window.py`

- [ ] **Step 1: Implement ui/overlay_window.py**

Create `ui/overlay_window.py`:

```python
import logging

from PIL import Image
from PyQt6.QtCore import QPoint, QRect, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QCursor, QImage, QPainter, QPixmap
from PyQt6.QtWidgets import QWidget

logger = logging.getLogger(__name__)


class OverlayWindow(QWidget):
    """Full-screen overlay for region selection.

    Displays the screenshot with a dark overlay. User drags to select a region.
    The selected region shows the original screenshot (no overlay).
    Emits region_selected(QRect) on mouse release, then closes.
    """

    region_selected = pyqtSignal(QRect)

    def __init__(self, screenshot: Image.Image):
        super().__init__()
        self._screenshot = screenshot
        self._pixmap = self._pil_to_pixmap(screenshot)
        self._origin = QPoint()
        self._current = QPoint()
        self._selecting = False

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        self.showFullScreen()

    def _pil_to_pixmap(self, pil_image: Image.Image) -> QPixmap:
        """Convert PIL Image to QPixmap."""
        rgb = pil_image.convert("RGB")
        data = rgb.tobytes("raw", "RGB")
        qimage = QImage(data, rgb.width, rgb.height, 3 * rgb.width, QImage.Format.Format_RGB888)
        return QPixmap.fromImage(qimage)

    def paintEvent(self, event):
        painter = QPainter(self)
        # Draw the screenshot as background
        painter.drawPixmap(0, 0, self._pixmap)
        # Draw semi-transparent overlay on entire screen
        painter.fillRect(self.rect(), QColor(0, 0, 0, 128))

        if self._selecting:
            # Clear the overlay in the selected region to show original screenshot
            selection = QRect(self._origin, self._current).normalized()
            painter.setClipRect(selection)
            painter.drawPixmap(0, 0, self._pixmap)
            painter.setClipping(False)
            # Draw border around selection
            painter.setPen(QColor(255, 255, 255, 200))
            painter.drawRect(selection)

        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._origin = event.pos()
            self._current = event.pos()
            self._selecting = True

    def mouseMoveEvent(self, event):
        if self._selecting:
            self._current = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._selecting:
            self._selecting = False
            selection = QRect(self._origin, event.pos()).normalized()
            if selection.width() > 5 and selection.height() > 5:
                logger.debug(
                    "Region selected: (%d,%d)-(%d,%d)",
                    selection.x(), selection.y(),
                    selection.right(), selection.bottom(),
                )
                self.region_selected.emit(selection)
            self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            logger.debug("Overlay cancelled by Esc")
            self.close()
```

- [ ] **Step 2: Commit**

```bash
git add ui/overlay_window.py
git commit -m "feat: full-screen overlay window with region selection"
```

---

### Task 7: Floating Panel

**Files:**
- Create: `ui/floating_panel.py`

- [ ] **Step 1: Implement ui/floating_panel.py**

Create `ui/floating_panel.py`:

```python
import logging

from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
    QApplication,
)

logger = logging.getLogger(__name__)

PANEL_WIDTH = 420
PANEL_HEIGHT = 360


class FloatingPanel(QWidget):
    """Floating result panel with frosted dark style, pin toggle, and Markdown rendering."""

    def __init__(self):
        super().__init__()
        self._pinned = False
        self._content_text = ""

        self._setup_window()
        self._setup_ui()
        self._setup_shadow()

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(PANEL_WIDTH, PANEL_HEIGHT)

    def _setup_ui(self):
        self._container = QWidget(self)
        self._container.setObjectName("container")
        self._container.setStyleSheet("""
            #container {
                background-color: rgba(20, 20, 20, 242);
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 20);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._container)

        container_layout = QVBoxLayout(self._container)
        container_layout.setContentsMargins(16, 12, 16, 12)
        container_layout.setSpacing(8)

        # Top bar
        top_bar = QHBoxLayout()
        title = QLabel("AI 助手")
        title.setStyleSheet("color: #888888; font-size: 12px;")
        top_bar.addWidget(title)
        top_bar.addStretch()

        self._pin_btn = QPushButton("📌")
        self._pin_btn.setFixedSize(28, 28)
        self._pin_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 14px;
                color: #666666;
            }
            QPushButton:hover {
                color: #aaaaaa;
            }
        """)
        self._pin_btn.clicked.connect(self._toggle_pin)
        top_bar.addWidget(self._pin_btn)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 14px;
                color: #666666;
            }
            QPushButton:hover {
                color: #aaaaaa;
            }
        """)
        close_btn.clicked.connect(self.hide)
        top_bar.addWidget(close_btn)

        container_layout.addLayout(top_bar)

        # Content area
        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(False)
        self._browser.setStyleSheet("""
            QTextBrowser {
                background-color: transparent;
                border: none;
                color: #d0d0d0;
                font-size: 13px;
                selection-background-color: rgba(255, 255, 255, 30);
            }
        """)
        container_layout.addWidget(self._browser)

        # Bottom bar
        bottom = QHBoxLayout()
        bottom.addStretch()
        powered = QLabel("Kimi 2.5")
        powered.setStyleSheet("color: #444444; font-size: 10px;")
        bottom.addWidget(powered)
        container_layout.addLayout(bottom)

    def _setup_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 4)
        self._container.setGraphicsEffect(shadow)

    def _toggle_pin(self):
        self._pinned = not self._pinned
        if self._pinned:
            self.setWindowFlags(
                self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint
            )
            self._pin_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255,255,255,15);
                    border: none;
                    border-radius: 4px;
                    font-size: 14px;
                    color: #aaaaaa;
                }
            """)
            logger.debug("Panel pinned")
        else:
            self.setWindowFlags(
                self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint
            )
            self._pin_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    font-size: 14px;
                    color: #666666;
                }
                QPushButton:hover { color: #aaaaaa; }
            """)
            logger.debug("Panel unpinned")
        self.show()

    def show_near_region(self, region: QRect):
        """Position the panel near the selected region and show it."""
        screen = QApplication.primaryScreen().geometry()
        margin = 10

        # Try right of selection
        x = region.right() + margin
        y = region.top()

        # If goes off right edge, try below selection
        if x + PANEL_WIDTH > screen.right():
            x = region.left()
            y = region.bottom() + margin

        # If goes off bottom, fall back to bottom-right corner
        if y + PANEL_HEIGHT > screen.bottom():
            x = screen.right() - PANEL_WIDTH - margin
            y = screen.bottom() - PANEL_HEIGHT - margin

        # Clamp to screen bounds
        x = max(screen.left(), min(x, screen.right() - PANEL_WIDTH))
        y = max(screen.top(), min(y, screen.bottom() - PANEL_HEIGHT))

        self.move(x, y)
        self.show()
        self.raise_()

    def append_chunk(self, text: str):
        """Append streaming text and re-render Markdown."""
        self._content_text += text
        self._browser.setMarkdown(self._content_text)
        # Scroll to bottom
        scrollbar = self._browser.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def show_error(self, message: str):
        """Display error message in red."""
        self._content_text = ""
        self._browser.setHtml(
            f'<p style="color: #ff6b6b; font-size: 13px;">⚠ 请求失败: {message}</p>'
        )

    def clear_content(self):
        """Clear all content for a new request."""
        self._content_text = ""
        self._browser.clear()

    def focusOutEvent(self, event):
        if not self._pinned:
            self.hide()
        super().focusOutEvent(event)
```

- [ ] **Step 2: Commit**

```bash
git add ui/floating_panel.py
git commit -m "feat: floating panel with frosted dark style, pin, and markdown rendering"
```

---

### Task 8: System Tray Icon

**Files:**
- Create: `ui/tray_icon.py`

- [ ] **Step 1: Implement ui/tray_icon.py**

Create `ui/tray_icon.py`:

```python
import base64
import logging

from PyQt6.QtGui import QAction, QIcon, QPixmap
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

logger = logging.getLogger(__name__)

# 16x16 blue circle PNG icon (base64-encoded)
_ICON_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAA"
    "X0lEQVR4nGNgoBAwMjAwMPz//58BF2ZiIEPTIGsYiDYAl2Yi"
    "NTMQowkfGHgDGEYHIsMoSMOoF4wORAYGBgYAHpQKFfnbpDQA"
    "AAAASUVORK5CYII="
)


def create_tray_icon(app: QApplication) -> QSystemTrayIcon:
    """Create and configure the system tray icon with exit menu."""
    # Load icon from embedded base64
    icon_data = base64.b64decode(_ICON_B64)
    pixmap = QPixmap()
    pixmap.loadFromData(icon_data)
    icon = QIcon(pixmap)

    tray = QSystemTrayIcon(icon, app)

    menu = QMenu()
    exit_action = QAction("退出", menu)
    exit_action.triggered.connect(app.quit)
    menu.addAction(exit_action)

    tray.setContextMenu(menu)
    tray.setToolTip("AI Vision Translate Assistant")
    tray.show()

    logger.debug("System tray icon created")
    return tray
```

- [ ] **Step 2: Commit**

```bash
git add ui/tray_icon.py
git commit -m "feat: system tray icon with exit menu"
```

---

### Task 9: Main Entry Point — Wire Everything Together

**Files:**
- Create: `main.py`

- [ ] **Step 1: Implement main.py**

Create `main.py`:

```python
import argparse
import logging
import sys

from PyQt6.QtCore import QRect
from PyQt6.QtWidgets import QApplication
from PIL import Image

from config import load_config
from core.api_client import ApiWorker
from core.hotkey_listener import HotkeyThread
from core.screenshot import crop_region, grab_fullscreen, image_to_base64
from ui.floating_panel import FloatingPanel
from ui.overlay_window import OverlayWindow
from ui.tray_icon import create_tray_icon


def main():
    parser = argparse.ArgumentParser(description="AI Vision Translate Assistant")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger(__name__)

    # Load config
    try:
        config = load_config()
    except (FileNotFoundError, ValueError) as e:
        logger.error("Configuration error: %s", e)
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Components
    panel = FloatingPanel()
    tray = create_tray_icon(app)

    # State
    state = {"screenshot": None, "overlay": None, "worker": None}

    def on_hotkey_triggered():
        logger.info("Hotkey triggered")
        screenshot = grab_fullscreen()
        state["screenshot"] = screenshot
        overlay = OverlayWindow(screenshot)
        overlay.region_selected.connect(on_region_selected)
        state["overlay"] = overlay

    def on_region_selected(region: QRect):
        logger.info(
            "Region selected: (%d,%d)-(%d,%d)",
            region.x(), region.y(), region.right(), region.bottom(),
        )
        screenshot = state["screenshot"]
        if screenshot is None:
            return

        cropped = crop_region(
            screenshot, region.x(), region.y(), region.right(), region.bottom()
        )
        b64 = image_to_base64(cropped)

        panel.clear_content()
        panel.show_near_region(region)

        worker = ApiWorker(config["api_key"], config["api_base"], b64)
        worker.stream_chunk.connect(panel.append_chunk)
        worker.stream_done.connect(lambda: logger.info("Stream complete"))
        worker.stream_error.connect(panel.show_error)
        worker.start()
        state["worker"] = worker

    # Hotkey thread
    hotkey_thread = HotkeyThread()
    hotkey_thread.triggered.connect(on_hotkey_triggered)
    hotkey_thread.start()
    logger.info("AI Vision Translate Assistant started. Press Ctrl+CapsLock to activate.")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify app launches without errors**

Run: `python main.py --debug`
Expected: App starts, tray icon appears, console shows "AI Vision Translate Assistant started." log message. Press `Ctrl+CapsLock` to verify overlay appears. Press `Esc` to close overlay without error. Close via tray icon → 退出.

- [ ] **Step 3: Commit**

```bash
git add main.py
git commit -m "feat: main entry point wiring all components together"
```

---

### Task 10: End-to-End Manual Testing & Bug Fixes

**Files:**
- Modify: any files as needed based on testing findings

- [ ] **Step 1: Create .env with real API key**

Create `.env` in project root:
```
KIMI_API_KEY=sk-your-real-key
KIMI_API_BASE=https://api.moonshot.cn/v1
```

- [ ] **Step 2: Test full flow — English text**

Run: `python main.py --debug`

1. Press `Ctrl+CapsLock` → overlay should appear with dark mask and crosshair cursor
2. Drag to select a region containing English text
3. Release mouse → overlay closes, floating panel appears near selection
4. Panel should stream Markdown-rendered Chinese translation
5. Click outside the panel → panel hides (not pinned)

- [ ] **Step 3: Test full flow — Code screenshot**

1. Open any code editor with visible code
2. Press `Ctrl+CapsLock` → select the code region
3. Panel should stream code analysis in Markdown

- [ ] **Step 4: Test pin behavior**

1. Trigger a new capture and wait for result
2. Click the pin 📌 button → button style changes
3. Click elsewhere on screen → panel stays visible (pinned)
4. Click pin again → unpinned
5. Click elsewhere → panel hides

- [ ] **Step 5: Test Esc cancel**

1. Press `Ctrl+CapsLock` → overlay appears
2. Press `Esc` → overlay closes, no panel appears, no API call in logs

- [ ] **Step 6: Test error handling**

1. Set an invalid API key in `.env` (e.g., `KIMI_API_KEY=sk-invalid`)
2. Run `python main.py --debug`
3. Trigger capture → panel should show red error message

- [ ] **Step 7: Run all automated tests**

Run: `pytest tests/ -v`
Expected: All tests PASS.

- [ ] **Step 8: Fix any bugs found, commit**

```bash
git add -A
git commit -m "fix: bug fixes from end-to-end testing"
```

(Skip this commit if no bugs were found.)

---

### Task 11: Final Cleanup & CLAUDE.md Update

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update CLAUDE.md with actual commands**

Update `CLAUDE.md` to reflect the final project state — correct run/test commands and project structure.

- [ ] **Step 2: Run full test suite one final time**

Run: `pytest tests/ -v`
Expected: All tests PASS.

- [ ] **Step 3: Final commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with final project structure"
```
