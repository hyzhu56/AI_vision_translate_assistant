import logging

from PyQt6.QtCore import QPoint, QRect, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QApplication,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizeGrip,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)

PANEL_WIDTH = 420
PANEL_HEIGHT = 360
FONT_SIZE_MIN = 10
FONT_SIZE_MAX = 22
FONT_SIZE_DEFAULT = 13

_BTN_STYLE = """
    QPushButton {{
        background: transparent;
        border: none;
        font-size: {size}px;
        color: #666666;
    }}
    QPushButton:hover {{ color: #aaaaaa; }}
"""


class FloatingPanel(QWidget):
    """Floating result panel with frosted dark style, pin toggle, and Markdown rendering."""

    def __init__(self):
        super().__init__()
        self._pinned = False
        self._content_text = ""
        self._font_size = FONT_SIZE_DEFAULT
        self._drag_pos: QPoint | None = None

        self._setup_window()
        self._setup_ui()
        self._setup_shadow()

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(PANEL_WIDTH, PANEL_HEIGHT)
        self.setMinimumSize(280, 200)

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

        # ── Top bar ──────────────────────────────────────────────────────────
        top_bar = QHBoxLayout()

        title = QLabel("AI 助手")
        title.setStyleSheet("color: #888888; font-size: 12px;")
        top_bar.addWidget(title)
        top_bar.addStretch()

        # Font size buttons
        font_btn_style = """
            QPushButton {
                background: transparent;
                border: none;
                color: #666666;
                font-size: 11px;
                padding: 0px 3px;
            }
            QPushButton:hover { color: #aaaaaa; }
        """
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
        self._pin_btn.clicked.connect(self._toggle_pin)
        top_bar.addWidget(self._pin_btn)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet(_BTN_STYLE.format(size=14))
        close_btn.clicked.connect(self.hide)
        top_bar.addWidget(close_btn)

        container_layout.addLayout(top_bar)

        # ── Content area ─────────────────────────────────────────────────────
        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(False)
        self._apply_browser_style()
        container_layout.addWidget(self._browser)

        # ── Bottom bar ───────────────────────────────────────────────────────
        bottom = QHBoxLayout()
        bottom.setContentsMargins(0, 0, 0, 0)
        bottom.addStretch()
        powered = QLabel("Kimi k2.5")
        powered.setStyleSheet("color: #444444; font-size: 10px;")
        bottom.addWidget(powered)

        grip = QSizeGrip(self)
        grip.setStyleSheet("QSizeGrip { background: transparent; }")
        bottom.addWidget(grip)

        container_layout.addLayout(bottom)

    def _setup_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 4)
        self._container.setGraphicsEffect(shadow)

    # ── Font size ─────────────────────────────────────────────────────────────

    def _apply_browser_style(self):
        self._browser.setStyleSheet(f"""
            QTextBrowser {{
                background-color: transparent;
                border: none;
                color: #d0d0d0;
                font-size: {self._font_size}px;
                selection-background-color: rgba(255, 255, 255, 30);
            }}
        """)

    def _increase_font(self):
        if self._font_size < FONT_SIZE_MAX:
            self._font_size += 1
            self._apply_browser_style()
            if self._content_text:
                self._browser.setMarkdown(self._content_text)

    def _decrease_font(self):
        if self._font_size > FONT_SIZE_MIN:
            self._font_size -= 1
            self._apply_browser_style()
            if self._content_text:
                self._browser.setMarkdown(self._content_text)

    # ── Pin toggle ────────────────────────────────────────────────────────────

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
            self._pin_btn.setStyleSheet(_BTN_STYLE.format(size=14))
            logger.debug("Panel unpinned")
        self.show()

    # ── Drag to move ──────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and event.pos().y() < 50:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
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

    # ── Public API ────────────────────────────────────────────────────────────

    def show_near_region(self, region: QRect):
        """Position the panel near the selected region and show it."""
        screen = QApplication.primaryScreen().geometry()
        margin = 10
        w = self.width()
        h = self.height()

        # Try right of selection
        x = region.right() + margin
        y = region.top()

        # If goes off right edge, try below selection
        if x + w > screen.right():
            x = region.left()
            y = region.bottom() + margin

        # If goes off bottom, fall back to bottom-right corner
        if y + h > screen.bottom():
            x = screen.right() - w - margin
            y = screen.bottom() - h - margin

        # Clamp to screen bounds
        x = max(screen.left(), min(x, screen.right() - w))
        y = max(screen.top(), min(y, screen.bottom() - h))

        self.move(x, y)
        self.show()
        self.raise_()

    def append_chunk(self, text: str):
        """Append streaming text and re-render Markdown."""
        self._content_text += text
        self._browser.setMarkdown(self._content_text)
        scrollbar = self._browser.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def show_error(self, message: str):
        """Display error message in red."""
        self._content_text = ""
        self._browser.setHtml(
            f'<p style="color: #ff6b6b; font-size: {self._font_size}px;">⚠ 请求失败: {message}</p>'
        )

    def clear_content(self):
        """Clear all content for a new request."""
        self._content_text = ""
        self._browser.clear()

    def focusOutEvent(self, event):
        if not self._pinned:
            self.hide()
        super().focusOutEvent(event)
