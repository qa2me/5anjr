import threading
import logging


class GlobalHotkey:
    def __init__(self, combo="ctrl+q", on_activate=None):
        self.combo = combo
        self._on_activate = on_activate
        self._listener = None
        self._running = False
        self._available = False

    def _check_available(self):
        try:
            import keyboard
            keyboard.press_and_release("shift")
            return True
        except Exception:
            return False

    def start(self):
        if self._running:
            return

        try:
            import keyboard
            keyboard.add_hotkey(self.combo, self._trigger)
            self._running = True
            self._available = True
            logging.info(f"Global hotkey {self.combo} registered")
        except Exception as e:
            logging.warning(f"Could not register global hotkey {self.combo}: {e}")
            self._available = False

    def stop(self):
        if not self._running:
            return
        try:
            import keyboard
            keyboard.remove_hotkey(self.combo)
        except Exception:
            pass
        self._running = False

    def _trigger(self):
        if self._on_activate:
            threading.Thread(target=self._on_activate, daemon=True).start()

    @property
    def is_available(self):
        return self._available
