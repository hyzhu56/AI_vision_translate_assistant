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
