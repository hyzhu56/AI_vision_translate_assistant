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
