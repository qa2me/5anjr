import os
import time
import threading
from gi.repository import GLib
from .wake_word import WakeWordDetector
from .stt import SpeechRecognizer
from .tts import Speaker
from .commands import CommandHandler
from .timer import TimerManager
from .hotkey import GlobalHotkey
from .listener_window import ListenerWindow
from .plugin_manager import register_plugins


MODEL_PATH = os.path.expanduser(
    "~/.local/share/vosk/vosk-model-small-en-us-0.15"
)
CMD_FILE = "/tmp/linux-assistant.cmd"


class AssistantCore:
    def __init__(self):
        self.speaker = Speaker()
        self.timers = TimerManager(self.speaker)
        self.cmd_handler = CommandHandler(self.speaker, self.timers, self)
        self.recognizer = SpeechRecognizer(MODEL_PATH)
        self.wake_detector = WakeWordDetector(MODEL_PATH)
        self.wake_detector.on_wake(self._on_wake_word)
        self.hotkey = GlobalHotkey(combo="ctrl+q", on_activate=self._on_hotkey)
        self._listener = None
        self._listener_cooldown = 0
        self._active = True
        self._init_plugins()

    def _init_plugins(self):
        api = register_plugins(self.speaker, self.timers, self)
        self.cmd_handler.set_plugin_api(api)

    def open_listener(self):
        GLib.idle_add(self._open_listener)

    def _open_listener(self):
        if not self._active:
            return

        if self._listener:
            return

        if time.time() - self._listener_cooldown < 1.5:
            return

        self.speaker.say("Yes?")

        def on_done(text):
            self._listener = None
            self._listener_cooldown = time.time()
            if text:
                self.cmd_handler.stop_flag = False
                self.cmd_handler.handle(text)
                if self.cmd_handler.stop_flag:
                    self._active = False
                    self.speaker.say("Say hey linux to wake me up again")
                    self._active = True

        self._listener = ListenerWindow(
            self.speaker, self.recognizer, on_done,
            on_edit_commands=self._open_command_editor,
        )
        self._listener.present()

    def _open_command_editor(self):
        from .command_editor import open_editor
        open_editor()

    def _listen_and_handle(self):
        if not self._active:
            return
        self.open_listener()

    def _on_wake_word(self):
        self._listen_and_handle()

    def _on_hotkey(self):
        self._listen_and_handle()

    def _monitor_cmd(self):
        while self._active:
            try:
                if os.path.exists(CMD_FILE):
                    with open(CMD_FILE) as f:
                        cmd = f.read().strip()
                    try:
                        os.remove(CMD_FILE)
                    except Exception:
                        pass
                    if cmd == "show":
                        self.open_listener()
            except Exception:
                pass
            time.sleep(0.5)

    def start(self):
        self.speaker.say("Hello, I am your Linux assistant")
        self.wake_detector.start()
        self.hotkey.start()
        threading.Thread(target=self._monitor_cmd, daemon=True).start()

    def stop(self):
        self.wake_detector.stop()
        self.hotkey.stop()
