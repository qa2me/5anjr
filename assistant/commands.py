import re
import subprocess
import os
from datetime import datetime


class CommandHandler:
    def __init__(self, speaker, timer_manager, app_context):
        self.speaker = speaker
        self.timers = timer_manager
        self.app_context = app_context
        self.plugin_api = None
        self.stop_flag = False

    def set_plugin_api(self, api):
        self.plugin_api = api

    def handle(self, text):
        text = text.lower().strip()
        if not text:
            return

        if self.plugin_api:
            if self.plugin_api.run_keyword_handlers(text):
                return
            if self.plugin_api.run_regex_handlers(text):
                return

        if self._match_stop(text):
            return

        if self._match_timer(text):
            return

        if self._match_open(text):
            return

        if self._match_time(text):
            return

        if self._match_volume(text):
            return

        self.speaker.say("I didn't understand that command")

    def _match_stop(self, text):
        if any(word in text for word in ["stop listening", "go to sleep", "shut up", "quit", "exit"]):
            self.speaker.say("Goodbye")
            self.stop_flag = True
            return True
        return False

    def _parse_duration(self, text):
        patterns = [
            (r"(\d+)\s*(hour|hours|hr|hrs)", 3600),
            (r"(\d+)\s*(minute|minutes|min|mins)", 60),
            (r"(\d+)\s*(second|seconds|sec|secs)", 1),
        ]
        total = 0
        words = text
        for pattern, multiplier in patterns:
            matches = re.findall(pattern, words)
            for num_str, _ in matches:
                total += int(num_str) * multiplier
        return total if total > 0 else None

    def _match_timer(self, text):
        if not any(w in text for w in ["timer", "countdown", "remind"]):
            return False

        duration = self._parse_duration(text)
        if duration is None:
            self.speaker.say("How long should I set the timer for?")
            return True

        label = None
        label_match = re.search(r"(?:called|named|for)\s+(.+)", text)
        if label_match:
            label = label_match.group(1).strip()

        timer_id = self.timers.set_timer(duration, label)

        if duration >= 3600:
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            remaining = duration % 60
            parts = []
            if hours:
                parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
            if minutes:
                parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
            if remaining:
                parts.append(f"{remaining} second{'s' if remaining != 1 else ''}")
            duration_str = " ".join(parts)
        elif duration >= 60:
            minutes = duration // 60
            seconds = duration % 60
            parts = [f"{minutes} minute{'s' if minutes != 1 else ''}"]
            if seconds:
                parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
            duration_str = " ".join(parts)
        else:
            duration_str = f"{duration} second{'s' if duration != 1 else ''}"

        self.speaker.say(f"Timer set for {duration_str}")
        return True

    def _match_open(self, text):
        if not any(w in text for w in ["open", "launch", "start", "run"]):
            return False

        app_name = text
        for prefix in ["open", "launch", "start", "run", "please"]:
            app_name = app_name.replace(prefix, "", 1)
        app_name = app_name.strip()

        known_apps = {
            "firefox": "firefox",
            "browser": "firefox",
            "chrome": "google-chrome",
            "brave": "brave-browser",
            "terminal": "gnome-terminal",
            "console": "gnome-terminal",
            "shell": "gnome-terminal",
            "calculator": "gnome-calculator",
            "cal": "gnome-calculator",
            "files": "nautilus",
            "file manager": "nautilus",
            "explorer": "nautilus",
            "code": "code",
            "vscode": "code",
            "vs code": "code",
            "settings": "gnome-control-center",
            "system settings": "gnome-control-center",
            "text editor": "gedit",
            "editor": "gedit",
            "gedit": "gedit",
            "discord": "discord",
            "spotify": "spotify",
            "vlc": "vlc",
            "media player": "vlc",
            "steam": "steam",
            "thunderbird": "thunderbird",
            "mail": "thunderbird",
        }

        app_cmd = known_apps.get(app_name)
        if app_cmd:
            try:
                subprocess.Popen(
                    [app_cmd],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                self.speaker.say(f"Opening {app_name}")
            except FileNotFoundError:
                self._try_xdg_open(app_name)
            return True

        self._try_xdg_open(app_name)
        return True

    def _try_xdg_open(self, app_name):
        try:
            result = subprocess.run(
                ["xdg-open", f"{app_name}.desktop"],
                capture_output=True,
                timeout=5,
            )
            if result.returncode == 0:
                self.speaker.say(f"Opening {app_name}")
                return
        except Exception:
            pass

        try:
            result = subprocess.run(
                ["gtk-launch", app_name],
                capture_output=True,
                timeout=5,
            )
            if result.returncode == 0:
                self.speaker.say(f"Opening {app_name}")
                return
        except Exception:
            pass

        try:
            desktop_files = []
            for root, dirs, files in os.walk("/usr/share/applications"):
                for f in files:
                    if app_name.lower() in f.lower() and f.endswith(".desktop"):
                        desktop_files.append(os.path.join(root, f))
            if desktop_files:
                subprocess.Popen(
                    ["gtk-launch", os.path.splitext(os.path.basename(desktop_files[0]))[0]],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                self.speaker.say(f"Opening {app_name}")
                return
        except Exception:
            pass

        self.speaker.say(f"Could not find application {app_name}")

    def _match_time(self, text):
        if not any(w in text for w in ["time", "clock", "date", "today"]):
            return False

        now = datetime.now()
        time_str = now.strftime("%I:%M %p").lstrip("0")
        if "date" in text or "today" in text:
            date_str = now.strftime("%B %d, %Y")
            self.speaker.say(f"The time is {time_str} and today is {date_str}")
        else:
            self.speaker.say(f"The time is {time_str}")
        return True

    def _match_volume(self, text):
        if "volume" not in text:
            return False

        vol_match = re.search(r"(\d+)", text)
        if vol_match:
            level = min(int(vol_match.group(1)), 100)
            try:
                subprocess.run(
                    ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{level}%"],
                    capture_output=True,
                )
                self.speaker.say(f"Volume set to {level} percent")
            except Exception:
                self.speaker.say("Could not change volume")
        else:
            if "up" in text or "increase" in text:
                try:
                    subprocess.run(
                        ["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+10%"],
                        capture_output=True,
                    )
                    self.speaker.say("Volume increased")
                except Exception:
                    pass
            elif "down" in text or "decrease" in text or "lower" in text:
                try:
                    subprocess.run(
                        ["pactl", "set-sink-volume", "@DEFAULT_SINK@", "-10%"],
                        capture_output=True,
                    )
                    self.speaker.say("Volume decreased")
                except Exception:
                    pass
        return True
