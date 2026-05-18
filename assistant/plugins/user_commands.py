"""
Loads custom commands from user_commands.json.
Commands are added via the Command Editor GUI (no coding needed).
"""

import json
import os
import subprocess

COMMANDS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "user_commands.json")


def load_commands():
    if not os.path.exists(COMMANDS_FILE):
        return []
    try:
        with open(COMMANDS_FILE) as f:
            return json.load(f)
    except Exception:
        return []


def save_commands(commands):
    with open(COMMANDS_FILE, "w") as f:
        json.dump(commands, f, indent=2)


def setup(api):
    commands = load_commands()
    for cmd in commands:
        keywords = cmd.get("keywords", [])
        actions = cmd.get("actions", [])

        if not keywords:
            continue

        @api.on_keywords(keywords)
        def handler(text, speaker, timers, _actions=actions):
            for action in _actions:
                _run_action(action, speaker)
            return True


def _run_action(action, speaker):
    atype = action.get("type", "")
    value = action.get("value", "")

    try:
        if atype == "app":
            subprocess.Popen([value], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        elif atype == "url":
            subprocess.Popen(
                ["xdg-open", value],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )

        elif atype == "speak":
            speaker.say(value)

        elif atype == "shell":
            subprocess.Popen(
                ["sh", "-c", value],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )

        elif atype == "app+url":
            app, url = value, action.get("url", "")
            subprocess.Popen([app], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if url:
                subprocess.Popen(
                    ["xdg-open", url],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )

    except Exception:
        pass
