"""
Opens CLion + https://codeforces.com when you say "open codeforces".
"""

import subprocess


def setup(api):
    @api.on_keywords(["open codeforces", "launch codeforces", "start codeforces"])
    def open_codeforces(text, speaker, timers):
        try:
            subprocess.Popen(["clion"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            pass

        subprocess.Popen(
            ["xdg-open", "https://codeforces.com"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )

        speaker.say("Opening Codeforces")
        return True
