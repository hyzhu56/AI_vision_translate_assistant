import logging

from PIL import Image
from PyQt6.QtCore import QPoint, QRect, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QCursor, QImage, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication, QWidget

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
        self._dpr = QApplication.primaryScreen().devicePixelRatio()
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
        """Convert PIL Image to QPixmap, tagging device pixel ratio for HiDPI screens."""
        rgb = pil_image.convert("RGB")
        data = rgb.tobytes("raw", "RGB")
        qimage = QImage(data, rgb.width, rgb.height, 3 * rgb.width, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimage)
        pixmap.setDevicePixelRatio(self._dpr)
        return pixmap

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
