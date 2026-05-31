#!/bin/bash
# A small script provided by Stephen KN4AM, for creating a linux desktop icon automatically
# run this once from your spotter folder, after moving spotter to the location where you plan to use it

INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
DESKTOP_FILE="$HOME/.local/share/applications/js8spotter.desktop"
DESKTOP_SHORTCUT="$HOME/Desktop/js8spotter.desktop"

mkdir -p "$HOME/.local/share/applications"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=JS8Spotter
Comment=Companion Program for JS8Call
Exec=python3 $INSTALL_DIR/js8spotter.py
Path=$INSTALL_DIR
Icon=$INSTALL_DIR/js8spotter.png
Terminal=false
Categories=HamRadio;Science;
StartupNotify=true
StartupWMClass=Js8spotter
EOF

chmod +x "$DESKTOP_FILE"
echo "Installed: $DESKTOP_FILE"

if [ -d "$HOME/Desktop" ]; then
    cp "$DESKTOP_FILE" "$DESKTOP_SHORTCUT"
    chmod +x "$DESKTOP_SHORTCUT"
    echo "Shortcut:  $DESKTOP_SHORTCUT"
fi

update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

echo "Done. You can now launch JS8Spotter from the application menu or Desktop icon."

