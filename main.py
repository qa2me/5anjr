import sys
import os
import subprocess
import atexit

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from assistant.core import AssistantCore
from assistant.tray import AppIndicator

LOCK_FILE = "/tmp/linux-assistant.lock"
CMD_FILE = "/tmp/linux-assistant.cmd"


def notify(msg):
    subprocess.run(["notify-send", "Linux Assistant", msg], capture_output=True)


def signal_running_instance():
    if not os.path.exists(LOCK_FILE):
        return False
    try:
        with open(LOCK_FILE) as f:
            pid = f.read().strip()
        if pid and os.path.exists(f"/proc/{pid}"):
            with open(CMD_FILE, "w") as f:
                f.write("show")
            return True
    except Exception:
        pass
    return False


def acquire_lock():
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE) as f:
                pid = f.read().strip()
            if pid and os.path.exists(f"/proc/{pid}"):
                return False
        except Exception:
            pass
        try:
            os.remove(LOCK_FILE)
        except Exception:
            pass
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))
    atexit.register(lambda: os.remove(LOCK_FILE) if os.path.exists(LOCK_FILE) else None)
    return True


def main():
    show_on_start = "--show" in sys.argv

    if signal_running_instance():
        return

    if not acquire_lock():
        notify("Assistant is already running")
        return

    assistant = AssistantCore()
    assistant.start()

    hotkey_info = "Ctrl+Q to listen" if assistant.hotkey.is_available \
        else "Ctrl+Q unavailable (needs input group)"

    assistant.timers.on_update(lambda: None)

    if show_on_start:
        notify(f"Running. Say 'hey linux' or press {hotkey_info}")
        assistant.open_listener()

    tray = AppIndicator(
        app_name="linux-assistant",
        on_quit=lambda: (assistant.stop(), sys.exit(0)),
        on_toggle=lambda: assistant.open_listener(),
        hotkey_info=hotkey_info,
        timer_manager=assistant.timers,
    )
    tray.run()


if __name__ == "__main__":
    main()
