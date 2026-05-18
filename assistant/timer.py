import subprocess
import time
import threading


class TimerManager:
    def __init__(self, speaker):
        self.speaker = speaker
        self.timers = []
        self._lock = threading.Lock()
        self._counter = 0
        self._on_timer_update = None

    def on_update(self, callback):
        self._on_timer_update = callback

    def set_timer(self, duration_seconds, label=None):
        self._counter += 1
        timer_id = self._counter
        label = label or f"Timer #{timer_id}"
        unit_name = f"la-timer-{timer_id}"
        start_time = time.time()

        msg = f"{label} finished!"

        shell_cmd = (
            f"/usr/bin/notify-send 'Timer' '{msg}' && "
            f"/usr/bin/spd-say -w '{msg}'"
        )

        try:
            result = subprocess.run(
                [
                    "systemd-run", "--user",
                    "--on-active", f"{int(duration_seconds)}s",
                    "--unit", unit_name,
                    "--collect",
                    "/usr/bin/sh", "-c", shell_cmd,
                ],
                capture_output=True, timeout=10,
            )
            success = result.returncode == 0
        except Exception:
            success = False

        subprocess.run(
            ["notify-send", "Timer", f"{label}: {self._format_duration(duration_seconds)}"],
            capture_output=True,
        )

        if not success:
            self.speaker.say("Could not create system timer")

        with self._lock:
            self.timers.append({
                "id": timer_id,
                "label": label,
                "unit": unit_name,
                "duration": duration_seconds,
                "start_time": start_time,
                "systemd": success,
            })

        if self._on_timer_update:
            self._on_timer_update()

        return timer_id

    def _format_duration(self, seconds):
        seconds = int(seconds)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        parts = []
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        if secs:
            parts.append(f"{secs}s")
        return " ".join(parts) if parts else "0s"

    def list_timers(self):
        result = subprocess.run(
            ["systemctl", "--user", "list-timers"],
            capture_output=True, text=True, timeout=10,
        )
        active_units = []
        for line in result.stdout.splitlines():
            if "la-timer-" in line:
                parts = line.split()
                for p in parts:
                    if p.startswith("la-timer-"):
                        active_units.append(p.replace(".timer", ""))

        now = time.time()
        with self._lock:
            active = []
            for t in self.timers:
                if t["unit"] in active_units:
                    elapsed = now - t["start_time"]
                    remaining = max(0, t["duration"] - elapsed)
                    active.append({**t, "remaining": remaining})
            return active

    def get_summary(self):
        timers = self.list_timers()
        if not timers:
            return None
        lines = []
        for t in timers:
            remaining = self._format_duration(t["remaining"])
            lines.append(f"{t['label']}: {remaining}")
        return "\n".join(lines)

    def cancel_timer(self, timer_id):
        with self._lock:
            for t in self.timers:
                if t["id"] == timer_id:
                    try:
                        subprocess.run(
                            ["systemctl", "--user", "stop", f"{t['unit']}.timer"],
                            capture_output=True, timeout=10,
                        )
                        subprocess.run(
                            ["systemctl", "--user", "stop", f"{t['unit']}.service"],
                            capture_output=True, timeout=10,
                        )
                    except Exception:
                        pass
                    self.timers.remove(t)
                    if self._on_timer_update:
                        self._on_timer_update()
                    return True
        return False
