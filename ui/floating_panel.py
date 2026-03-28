import logging

from PyQt6.QtCore import QPoint, QRect, Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QApplication,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from core.api_client import ApiWorker

logger = logging.getLogger(__name__)

PANEL_WIDTH = 420
PANEL_HEIGHT = 400
FONT_SIZE_MIN = 10
FONT_SIZE_MAX = 22
FONT_SIZE_DEFAULT = 13
_HANDLE_SIZE = 20

_BTN_STYLE = """
    QPushButton {{
        background: transparent;
        border: none;
        font-size: {size}px;
        color: #666666;
    }}
    QPushButton:hover {{ color: #aaaaaa; }}
"""


class _ResizeHandle(QWidget):
    """Transparent corner widget — resize cursor + drag-to-resize."""

    def __init__(self, parent: "FloatingPanel", corner: str):
        super().__init__(parent)
        self._corner = corner
        self._drag_start: QPoint | None = None
        self._start_geo: QRect | None = None
        self.setFixedSize(_HANDLE_SIZE, _HANDLE_SIZE)
        self.setStyleSheet("background: transparent;")
        self.setCursor(
            Qt.CursorShape.SizeFDiagCursor
            if corner == "br"
            else Qt.CursorShape.SizeBDiagCursor
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.globalPosition().toPoint()
            self._start_geo = self.window().geometry()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_start is not None:
            delta = event.globalPosition().toPoint() - self._drag_start
            geo = self._start_geo
            if self._corner == "br":
                self.window().resize(
                    max(280, geo.width() + delta.x()),
                    max(200, geo.height() + delta.y()),
                )
            else:  # bl
                new_w = max(280, geo.width() - delta.x())
                new_h = max(200, geo.height() + delta.y())
                self.window().setGeometry(geo.right() - new_w + 1, geo.y(), new_w, new_h)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_start = None
        self._start_geo = None
        super().mouseReleaseEvent(event)


class FloatingPanel(QWidget):
    """Floating result panel — always on top, multi-turn conversation, resizable."""

    panel_closing = pyqtSignal(object)  # emits self when user clicks ✕

    def __init__(self, config_store: dict):
        super().__init__()
        self._config_store = config_store
        self._pinned = False
        self._font_size = FONT_SIZE_DEFAULT
        self._drag_pos: QPoint | None = None
        self._messages: list[dict] = []
        self._streaming_buffer: str = ""
        self._current_worker: ApiWorker | None = None

        self._setup_window()
        self._setup_ui()
        self._setup_shadow()
        self._setup_resize_handles()

    # ── Window setup ──────────────────────────────────────────────────────────

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(PANEL_WIDTH, PANEL_HEIGHT)
        self.setMinimumSize(280, 200)

    # ── UI ────────────────────────────────────────────────────────────────────

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

        cl = QVBoxLayout(self._container)
        cl.setContentsMargins(16, 12, 16, 12)
        cl.setSpacing(8)

        # Top bar
        top_bar = QHBoxLayout()
        self._title_label = QLabel(self._config_store.get("panel_title", "AI 助手"))
        self._title_label.setStyleSheet("color: #888888; font-size: 12px;")
        top_bar.addWidget(self._title_label)
        top_bar.addStretch()

        font_btn_style = (
            "QPushButton { background:transparent; border:none; color:#666666;"
            " font-size:11px; padding:0px 3px; }"
            "QPushButton:hover { color:#aaaaaa; }"
        )
        self._font_dec_btn = QPushButton("A−")
        self._font_dec_btn.setFixedSize(28, 28)
        self._font_dec_btn.setStyleSheet(font_btn_style)
        self._font_dec_btn.setToolTip("减小字体")
        self._font_dec_btn.clicked.connect(self._decrease_font)
        top_bar.addWidget(self._font_dec_btn)

        self._font_inc_btn = QPushButton("A+")
        self._font_inc_btn.setFixedSize(28, 28)
        self._font_inc_btn.setStyleSheet(font_btn_style)
        self._font_inc_btn.setToolTip("增大字体")
        self._font_inc_btn.clicked.connect(self._increase_font)
        top_bar.addWidget(self._font_inc_btn)

        self._pin_btn = QPushButton("📌")
        self._pin_btn.setFixedSize(28, 28)
        self._pin_btn.setStyleSheet(_BTN_STYLE.format(size=14))
        self._pin_btn.setToolTip("固定面板（防止失焦隐藏）")
        self._pin_btn.clicked.connect(self._toggle_pin)
        top_bar.addWidget(self._pin_btn)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet(_BTN_STYLE.format(size=14))
        close_btn.clicked.connect(lambda: self.panel_closing.emit(self))
        top_bar.addWidget(close_btn)
        cl.addLayout(top_bar)

        # Content browser
        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(False)
        self._apply_browser_style()
        cl.addWidget(self._browser)

        # Follow-up input
        self._input_line = QLineEdit()
        self._input_line.setPlaceholderText("继续追问...")
        self._input_line.setStyleSheet("""
            QLineEdit {
                background: rgba(255,255,255,8);
                border: 1px solid rgba(255,255,255,20);
                border-radius: 6px;
                color: #d0d0d0;
                padding: 5px 10px;
                font-size: 12px;
            }
            QLineEdit:focus { border: 1px solid rgba(91,143,249,150); }
            QLineEdit:disabled { color: #444444; }
        """)
        self._input_line.returnPressed.connect(self._on_follow_up)
        cl.addWidget(self._input_line)

        # Bottom bar
        bottom = QHBoxLayout()
        bottom.setContentsMargins(0, 0, 0, 0)
        bottom.addStretch()
        powered = QLabel("Kimi k2.5")
        powered.setStyleSheet("color: #444444; font-size: 10px;")
        bottom.addWidget(powered)
        cl.addLayout(bottom)

    def _setup_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 4)
        self._container.setGraphicsEffect(shadow)

    def _setup_resize_handles(self):
        self._bl_handle = _ResizeHandle(self, "bl")
        self._br_handle = _ResizeHandle(self, "br")
        self._reposition_handles()

    def _reposition_handles(self):
        s = _HANDLE_SIZE
        self._bl_handle.move(0, self.height() - s)
        self._br_handle.move(self.width() - s, self.height() - s)
        self._bl_handle.raise_()
        self._br_handle.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "_bl_handle"):
            self._reposition_handles()

    # ── Font size ─────────────────────────────────────────────────────────────

    def _apply_browser_style(self):
        self._browser.setStyleSheet(f"""
            QTextBrowser {{
                background-color: transparent;
                border: none;
                color: #d0d0d0;
                font-size: {self._font_size}px;
                selection-background-color: rgba(255,255,255,30);
            }}
        """)

    def _increase_font(self):
        if self._font_size < FONT_SIZE_MAX:
            self._font_size += 1
            self._apply_browser_style()
            self._rebuild_display()

    def _decrease_font(self):
        if self._font_size > FONT_SIZE_MIN:
            self._font_size -= 1
            self._apply_browser_style()
            self._rebuild_display()

    # ── Pin ───────────────────────────────────────────────────────────────────

    def _toggle_pin(self):
        self._pinned = not self._pinned
        if self._pinned:
            self._pin_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255,255,255,15);
                    border: none; border-radius: 4px;
                    font-size: 14px; color: #aaaaaa;
                }
            """)
            self._pin_btn.setToolTip("取消固定（失焦自动隐藏）")
            logger.debug("Panel pinned")
        else:
            self._pin_btn.setStyleSheet(_BTN_STYLE.format(size=14))
            self._pin_btn.setToolTip("固定面板（防止失焦隐藏）")
            logger.debug("Panel unpinned")

    # ── Drag ──────────────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and event.pos().y() < 50:
            self._drag_pos = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    # ── Conversation engine ───────────────────────────────────────────────────

    def start_session(self, image_base64: str):
        """Start a new conversation with an image. Called by main.py after crop."""
        self._messages = [
            {"role": "system", "content": self._config_store["system_prompt"]},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_base64}"},
                    }
                ],
            },
        ]
        self._browser.clear()
        self._run_worker()

    def _run_worker(self):
        """Create and start an ApiWorker for the current _messages list."""
        self._input_line.setEnabled(False)
        self._streaming_buffer = ""
        worker = ApiWorker(self._config_store, list(self._messages))
        worker.stream_chunk.connect(self._on_chunk)
        worker.stream_done.connect(self._on_stream_done)
        worker.stream_error.connect(self._on_stream_error)
        worker.start()
        self._current_worker = worker

    def _on_chunk(self, text: str):
        """Append raw text during streaming for performance."""
        self._streaming_buffer += text
        cursor = self._browser.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self._browser.setTextCursor(cursor)
        self._browser.insertPlainText(text)
        self._browser.verticalScrollBar().setValue(
            self._browser.verticalScrollBar().maximum()
        )

    def _on_stream_done(self):
        """Store assistant reply in history; re-render full Markdown."""
        self._messages.append(
            {"role": "assistant", "content": self._streaming_buffer}
        )
        self._streaming_buffer = ""
        self._rebuild_display()
        self._input_line.setEnabled(True)
        self._current_worker = None

    def _on_stream_error(self, message: str):
        """Append red error text without clearing existing content."""
        self._streaming_buffer = ""
        cursor = self._browser.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self._browser.setTextCursor(cursor)
        self._browser.insertHtml(
            f'<p style="color:#ff6b6b;font-size:{self._font_size}px;">'
            f"⚠ 请求失败: {message}</p>"
        )
        self._input_line.setEnabled(True)
        self._current_worker = None
        logger.error("Stream error: %s", message)

    def _rebuild_display(self):
        """Re-render the entire conversation as clean Markdown."""
        parts: list[str] = []
        for msg in self._messages:
            role = msg["role"]
            content = msg["content"]
            if role == "assistant":
                parts.append(str(content))
            elif role == "user" and isinstance(content, str):
                # text follow-up (not the initial image message)
                parts.append(f"**你：** {content}")
        full_text = "\n\n---\n\n".join(parts)
        self._browser.setMarkdown(full_text)
        self._browser.verticalScrollBar().setValue(
            self._browser.verticalScrollBar().maximum()
        )

    def _on_follow_up(self):
        """Handle user pressing Enter in the follow-up input."""
        text = self._input_line.text().strip()
        if not text:
            return
        self._input_line.clear()
        # Show question immediately before API responds
        cursor = self._browser.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self._browser.setTextCursor(cursor)
        self._browser.insertPlainText(f"\n\n你：{text}\n\n")
        self._browser.verticalScrollBar().setValue(
            self._browser.verticalScrollBar().maximum()
        )
        self._messages.append({"role": "user", "content": text})
        self._run_worker()

    def cleanup(self):
        """Stop any in-flight worker before this panel is destroyed."""
        if self._current_worker is not None:
            self._current_worker.quit()
            self._current_worker.wait(500)
            self._current_worker = None

    # ── Public API ────────────────────────────────────────────────────────────

    def show_near_region(self, region: QRect):
        """Update title, position the panel near the selected region, and show."""
        self._title_label.setText(
            self._config_store.get("panel_title", "AI 助手")
        )
        screen = QApplication.primaryScreen().geometry()
        margin = 10
        w, h = self.width(), self.height()
        x, y = region.right() + margin, region.top()
        if x + w > screen.right():
            x, y = region.left(), region.bottom() + margin
        if y + h > screen.bottom():
            x = screen.right() - w - margin
            y = screen.bottom() - h - margin
        x = max(screen.left(), min(x, screen.right() - w))
        y = max(screen.top(), min(y, screen.bottom() - h))
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()

    def clear_content(self):
        self._messages = []
        self._streaming_buffer = ""
        self._browser.clear()

    def focusOutEvent(self, event):
        if not self._pinned:
            self.hide()
        super().focusOutEvent(event)
