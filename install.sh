#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="$HOME/.linux-assistant"
DESKTOP_FILE="$HOME/.config/autostart/linux-assistant.desktop"

echo "Installing Linux Voice Assistant..."

# Install system dependencies
echo "Installing system dependencies..."
sudo apt update
sudo apt install -y \
    python3-pip \
    python3-pyaudio \
    python3-gi \
    python3-gi-cairo \
    espeak-ng \
    portaudio19-dev \
    libportaudio2 \
    speech-dispatcher \
    speech-dispatcher-espeak-ng

# Add user to input group for global hotkeys
echo "Adding user to input group for global hotkey support..."
sudo usermod -a -G input "$USER"

# Install Python dependencies
echo "Installing Python packages..."
pip3 install --break-system-packages \
    vosk \
    pyaudio \
    speechrecognition \
    pyttsx3 \
    keyboard

# Create install directory
mkdir -p "$INSTALL_DIR"
cp -r "$PROJECT_DIR/assistant" "$PROJECT_DIR/main.py" "$INSTALL_DIR/"

# Download Vosk model if not present
MODEL_DIR="$HOME/.local/share/vosk/vosk-model-small-en-us-0.15"
if [ ! -d "$MODEL_DIR" ]; then
    echo "Downloading speech recognition model (~40MB)..."
    mkdir -p "$HOME/.local/share/vosk"
    wget -O /tmp/vosk-model.zip \
        "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
    unzip -o /tmp/vosk-model.zip -d "$HOME/.local/share/vosk/"
    rm /tmp/vosk-model.zip
fi

# Create launcher script
LAUNCHER="$INSTALL_DIR/run.sh"
cat > "$LAUNCHER" << 'SCRIPT'
#!/usr/bin/env bash
cd "$HOME/.linux-assistant"
python3 main.py
SCRIPT
chmod +x "$LAUNCHER"

# Create desktop entry for autostart
mkdir -p "$HOME/.config/autostart"
cat > "$DESKTOP_FILE" << DESKTOP
[Desktop Entry]
Type=Application
Name=Linux Assistant
Comment=Voice assistant with wake word "hey linux"
Exec=$LAUNCHER
Icon=audio-input-microphone
Terminal=false
Categories=Utility;Accessibility;
X-GNOME-Autostart-enabled=true
DESKTOP

# Create application menu entry
MENU_FILE="$HOME/.local/share/applications/linux-assistant.desktop"
mkdir -p "$HOME/.local/share/applications"
cp "$DESKTOP_FILE" "$MENU_FILE"
sed -i '/X-GNOME-Autostart/d' "$MENU_FILE"

echo ""
echo "Installation complete!"
echo ""
echo "To start the assistant now, run:"
echo "  $LAUNCHER"
echo ""
echo "It will also start automatically on next login."
echo "Say 'hey linux' followed by your command."
