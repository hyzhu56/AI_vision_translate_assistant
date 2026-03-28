import logging
import sys
from collections.abc import Callable
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

logger = logging.getLogger(__name__)


def _get_icon_path() -> Path:
    """Resolve app_icon.ico regardless of runtime context.

    PyInstaller --onefile: data files land in sys._MEIPASS (temp extract dir).
    Normal Python run:     ico lives two levels up from this file (project root).
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "app_icon.ico"
    return Path(__file__).parent.parent / "app_icon.ico"


def load_app_icon() -> QIcon:
    """Load app_icon.ico; fall back to programmatic icon if file is absent."""
    icon_path = _get_icon_path()
    if icon_path.exists():
        return QIcon(str(icon_path))
    # Fallback: simple painted circle (no external resource needed)
    pixmap = QPixmap(16, 16)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor("#5B8FF9"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(1, 1, 14, 14)
    painter.end()
    return QIcon(pixmap)


def create_tray_icon(
    app: QApplication,
    on_settings: Callable[[], None],
) -> QSystemTrayIcon:
    """Create system tray icon with Settings and Quit menu items."""
    icon = load_app_icon()
    tray = QSystemTrayIcon(icon, app)

    menu = QMenu()

    settings_action = QAction("⚙️ 设置", menu)
    settings_action.triggered.connect(on_settings)
    menu.addAction(settings_action)

    menu.addSeparator()

    exit_action = QAction("退出", menu)
    exit_action.triggered.connect(app.quit)
    menu.addAction(exit_action)

    tray.setContextMenu(menu)
    tray.setToolTip("AI Vision Translate Assistant")
    tray.show()

    logger.debug("System tray icon created")
    return tray
