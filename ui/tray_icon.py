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
