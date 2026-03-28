import logging

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

logger = logging.getLogger(__name__)


def _make_icon() -> QIcon:
    """Create a simple 16x16 tray icon using QPainter (no external assets needed)."""
    pixmap = QPixmap(16, 16)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    # Draw a filled blue circle
    painter.setBrush(QColor("#5B8FF9"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(1, 1, 14, 14)
    painter.end()
    return QIcon(pixmap)


def create_tray_icon(app: QApplication) -> QSystemTrayIcon:
    """Create and configure the system tray icon with exit menu."""
    icon = _make_icon()

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
