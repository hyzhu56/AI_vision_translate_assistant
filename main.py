import argparse
import logging
import sys
from collections import deque

from PyQt6.QtCore import QRect
from PyQt6.QtWidgets import QApplication

from config import load_config, load_settings
from core.hotkey_listener import HotkeyThread
from core.screenshot import crop_region, grab_fullscreen, image_to_base64
from ui.floating_panel import FloatingPanel
from ui.overlay_window import OverlayWindow
from ui.settings_window import SettingsWindow
from ui.tray_icon import create_tray_icon, load_app_icon


class PanelManager:
    """FIFO pool of at most MAX FloatingPanel instances."""

    MAX = 2

    def __init__(self):
        self._panels: deque[FloatingPanel] = deque()

    def acquire(self, config_store: dict) -> FloatingPanel:
        """Return a new panel, evicting the oldest one if at capacity."""
        if len(self._panels) >= self.MAX:
            oldest = self._panels.popleft()
            oldest.cleanup()
            try:
                oldest.panel_closing.disconnect()
            except (TypeError, RuntimeError):
                pass
            oldest.hide()
            oldest.deleteLater()
        panel = FloatingPanel(config_store)
        panel.panel_closing.connect(self._on_closing)
        self._panels.append(panel)
        return panel

    def _on_closing(self, panel: FloatingPanel):
        """Called when the user clicks ✕ on a panel."""
        if panel in self._panels:
            self._panels.remove(panel)
        panel.cleanup()
        panel.hide()
        panel.deleteLater()


def main():
    parser = argparse.ArgumentParser(description="AI Vision Translate Assistant")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger(__name__)

    need_setup = False
    try:
        env_cfg = load_config()
    except (FileNotFoundError, ValueError) as e:
        logger.warning("Configuration not ready: %s — launching with defaults", e)
        env_cfg = {
            "api_key": "",
            "api_base": "https://api.moonshot.cn/v1",
            "model": "kimi-k2.5",
        }
        need_setup = True

    settings = load_settings()
    config_store: dict = {**env_cfg, **settings}

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(load_app_icon())  # taskbar / Alt+Tab icon

    manager = PanelManager()

    def open_settings():
        win = SettingsWindow(config_store)
        win.exec()

    tray = create_tray_icon(app, on_settings=open_settings)

    # First launch without .env: open settings so the user can enter API key
    if need_setup:
        open_settings()

    state: dict = {"screenshot": None, "overlay": None}

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

        dpr = QApplication.primaryScreen().devicePixelRatio()
        cropped = crop_region(
            screenshot,
            int(region.x() * dpr), int(region.y() * dpr),
            int(region.right() * dpr), int(region.bottom() * dpr),
        )
        b64 = image_to_base64(cropped)

        panel = manager.acquire(config_store)
        panel.show_near_region(region)
        panel.start_session(b64)

    hotkey_thread = HotkeyThread()
    hotkey_thread.triggered.connect(on_hotkey_triggered)
    hotkey_thread.start()
    logger.info("AI Vision Translate Assistant started. Press Ctrl+CapsLock to activate.")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
