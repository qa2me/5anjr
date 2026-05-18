import subprocess
import threading


class Speaker:
    def __init__(self):
        self._lock = threading.Lock()

    def say(self, text):
        def _speak():
            with self._lock:
                try:
                    subprocess.run(
                        ["spd-say", "-w", text],
                        capture_output=True,
                        timeout=30,
                    )
                except Exception:
                    pass
        threading.Thread(target=_speak, daemon=True).start()

    def say_blocking(self, text):
        with self._lock:
            try:
                subprocess.run(
                    ["spd-say", "-w", text],
                    capture_output=True,
                    timeout=30,
                )
            except Exception:
                pass
