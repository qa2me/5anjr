# Linux Assistant

A hands-free voice assistant for Linux that lives in your system tray and responds to the wake word **"hey linux"**. Click the desktop icon or press **Ctrl+Q** to open the listening window at any time.

No cloud services, no subscriptions, no data leaving your machine. Everything runs offline.

---

## Features

- **Wake word activation** — Say "hey linux" and the assistant wakes up
- **Global hotkey** — Press **Ctrl+Q** from anywhere to open the listener
- **Desktop icon** — Click the desktop launcher to open the listening window
- **Visual listening indicator** — Pulsing blue glow overlay shows when the assistant is active
- **Text or voice** — Type your command or speak it (voice fills the text field, you press Enter)
- **Set timers** — "Set a timer for 10 minutes" — timers appear in the tray menu with live countdown
- **Open applications** — "Open firefox", "Launch terminal", "Start code"
- **Check the time** — "What time is it?" or "What's the date today?"
- **Volume control** — "Volume 50", "Volume up", "Volume down"
- **System tray icon** — Shows timer countdowns, runs quietly in the background
- **Autostart** — Launches automatically on login
- **Fully offline** — Speech recognition and synthesis never touch the internet
- **systemd timers** — Timers survive app restarts, visible via `systemctl --user list-timers`

---

## Requirements

- Python 3.10+
- Linux desktop (GNOME, Zorin, or any GTK-based environment)
- PulseAudio or PipeWire
- A microphone

---

## Quick Start

```bash
git clone https://github.com/qa2me/5anjr.git
cd 5anjr
chmod +x install.sh
./install.sh
```

Or run it directly without installing:

```bash
python3 main.py
```

---

## How to Use

### Wake word & hotkey

The assistant is always listening for **"hey linux"**. When it hears it, you'll hear **"Yes?"** and the listening window appears with a pulsing blue glow.

You can also press **Ctrl+Q** from anywhere on your desktop to trigger the same listening window.

### Listener window

The listener window shows:
- A pulsing blue glow animation (like Siri)
- A text field where you can type your command
- Speech recognition runs simultaneously — voice fills the text automatically

To submit: press **Enter**. To cancel: press **Escape** or click the **X** button.

### Commands

| You say | It does |
|---------|---------|
| `Set a timer for 5 minutes` | Starts a 5-minute countdown (appears in tray menu) |
| `Set a timer for 1 hour 30 minutes` | Multi-unit timers work too |
| `Open firefox` | Launches Firefox |
| `Launch terminal` | Opens gnome-terminal |
| `Start code` | Opens VS Code |
| `Open discord` | Opens Discord |
| `What time is it?` | Tells the current time |
| `What's the date today?` | Tells the date |
| `Volume 50` | Sets volume to 50% |
| `Volume up` | Increases volume by 10% |
| `Stop listening` | Puts the assistant to sleep |

When a timer finishes, you get both a desktop notification and a voice alert.

### Known applications

The assistant knows common apps by name: firefox, chrome, brave, terminal, calculator, files, code/vscode, settings, discord, spotify, vlc, steam, thunderbird, and more. For anything else, it searches your `.desktop` files automatically.

---

## Project Structure

```
5anjr/
├── main.py                  # Entry point with single-instance locking
├── install.sh               # One-command installer
├── requirements.txt         # Python dependencies
├── linux-assistant.desktop  # Desktop entry and autostart
├── README.md
├── assets/
│   └── icon.svg             # Custom logo (microphone + sound waves)
└── assistant/
    ├── core.py              # Main loop: wake, hotkey, cmd file monitor
    ├── wake_word.py         # Vosk-based wake word detection
    ├── stt.py               # Speech-to-text using Vosk
    ├── tts.py               # Speech output via speech-dispatcher
    ├── commands.py          # Command parser and action handlers
    ├── timer.py             # systemd-backed timers with live countdown
    ├── hotkey.py            # Global Ctrl+Q listener
    ├── listener_window.py   # GTK overlay with glow animation + text input
    └── tray.py              # GTK system tray indicator with timer display
```

### How it works

1. **Wake word detection** (`wake_word.py`) — Streams audio from your mic through Vosk. When "hey linux" appears in the partial or final result, the wake callback fires.

2. **Global hotkey** (`hotkey.py`) — Uses the `keyboard` library to register **Ctrl+Q** system-wide. Pressing it triggers the same listen flow. Requires the `input` group.

3. **Listener window** (`listener_window.py`) — A floating GTK popup with a Cairo-drawn pulsing glow animation, a text entry field, and a background voice recognition thread. Voice fills the entry, you press Enter to submit.

4. **Command dispatch** (`commands.py`) — Text is matched against patterns using keyword matching and regex. Priority order: stop > timer > open app > time > volume.

5. **Timers** (`timer.py`) — Creates transient systemd timer units via `systemd-run --user --on-active`. Each timer shows a `notify-send` notification when set, displays a live countdown in the tray menu, and fires `notify-send` + `spd-say` when done. Timers survive app restarts.

6. **Voice output** (`tts.py`) — Uses `spd-say` (speech-dispatcher) for text-to-speech.

7. **System tray** (`tray.py`) — Ayatana AppIndicator with dynamic menu that updates every 2 seconds to show active timer countdowns.

---

## Installation Details

The installer (`install.sh`) does the following:

1. Adds your user to the `input` group for global hotkey support
2. Installs system packages: `python3-pyaudio`, `python3-gi`, `espeak-ng`, `speech-dispatcher`, `portaudio19-dev`
3. Installs Python packages: `vosk`, `pyaudio`, `SpeechRecognition`, `pyttsx3`, `keyboard`
4. Downloads the Vosk speech model (~40MB) to `~/.local/share/vosk/`
5. Copies the assistant files to `~/.linux-assistant/`
6. Creates a systemd-like autostart entry in `~/.config/autostart/`
7. Adds an application menu entry in `~/.local/share/applications/`

### Manual dependency install (Ubuntu/Debian)

```bash
sudo apt install python3-pyaudio python3-gi python3-gi-cairo espeak-ng \
  portaudio19-dev speech-dispatcher speech-dispatcher-espeak-ng

sudo usermod -a -G input $USER

pip3 install --break-system-packages vosk pyaudio speechrecognition pyttsx3 keyboard
```

---

## Custom Commands (Plugins)

You can add your own voice commands without touching the core code. Create a `.py` file in `assistant/plugins/` and it loads automatically.

### Quick start — keyword matching

Create `assistant/plugins/my_commands.py`:

```python
PATTERNS = ["hello", "hi", "hey"]

def handle(text, speaker, timers):
    speaker.say("Hello! This is my custom command.")
    return True
```

- `PATTERNS` — list of keywords that trigger your handler
- `handle(text, speaker, timers)` — called when a keyword matches. Return `True` if handled.

### Advanced — decorator API

For regex matching and more control, use `setup(api)`:

```python
def setup(api):
    @api.on_keywords(["good morning", "good evening"])
    def greet(text, speaker, timers):
        speaker.say("Good day to you!")
        return True

    @api.on_regex(r"repeat\s+(.+)")
    def echo(text, speaker, timers, match):
        speaker.say(match.group(1))
        return True

    @api.on_keywords(["screenshot"])
    def screenshot(text, speaker, timers):
        import subprocess
        subprocess.Popen(["gnome-screenshot", "-i"])
        speaker.say("Opening screenshot tool")
        return True
```

### API reference

| Decorator | Arguments | Callback receives |
|-----------|-----------|-------------------|
| `@api.on_keywords(list)` | List of keyword strings | `(text, speaker, timers)` |
| `@api.on_regex(pattern)` | Regex pattern string | `(text, speaker, timers, match)` |

The `speaker` object has `.say(text)` (non-blocking) and `.say_blocking(text)` methods.  
The `timers` object has `.set_timer(seconds, label)` and `.cancel_timer(id)` methods.

See `assistant/plugins/example.py` and `assistant/plugins/custom_advanced.py` for working examples.

### Adding applications

Edit the `known_apps` dictionary in `assistant/commands.py`:

```python
known_apps = {
    "myapp": "myapp",
    "custom editor": "my-editor",
}
```

### Changing the wake word

Change the keyphrase argument to `WakeWordDetector` in `assistant/core.py`:

```python
self.wake_detector = WakeWordDetector(MODEL_PATH, keyphrase="computer")
```

---

## Troubleshooting

| Problem | Likely fix |
|---------|-----------|
| No sound output | Check `speech-dispatcher` is running: `spd-say "test"` |
| Wake word not detected | Check your mic with `arecord` or `pavucontrol` |
| Microphone not working | Check PulseAudio: `pactl info` and `pavucontrol` |
| Ctrl+Q hotkey not working | Add user to `input` group: `sudo usermod -a -G input $USER` then log out and back in |
| "ModuleNotFoundError" | Run `pip3 install --break-system-packages -r requirements.txt` |
| AppIndicator not showing | Install `ayatana-appindicator3` or `libappindicator` |

---

## License

MIT
