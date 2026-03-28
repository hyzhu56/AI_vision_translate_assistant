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
