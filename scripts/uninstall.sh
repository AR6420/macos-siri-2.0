#!/bin/bash
# Uninstaller for Voice Assistant
# Removes app, data, and configuration files

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="VoiceAssistant"
IDENTIFIER="com.voiceassistant.app"

echo "================================================"
echo "Voice Assistant Uninstaller"
echo "================================================"
echo ""
echo "This will remove Voice Assistant and all its data from your Mac."
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "⚠️  Warning: This script should NOT be run with sudo"
    echo "   Please run as normal user: ./uninstall.sh"
    exit 1
fi

# Confirm uninstallation
read -p "Are you sure you want to uninstall Voice Assistant? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstallation cancelled."
    exit 0
fi

echo ""
echo "🗑️  Starting uninstallation..."
echo ""

# 1. Quit running application
echo "1. Stopping Voice Assistant..."
if pgrep -x "$APP_NAME" > /dev/null; then
    echo "   Quitting running instance..."
    killall "$APP_NAME" 2>/dev/null || true
    sleep 2

    # Force quit if still running
    if pgrep -x "$APP_NAME" > /dev/null; then
        echo "   Force quitting..."
        killall -9 "$APP_NAME" 2>/dev/null || true
        sleep 1
    fi
    echo "   ✓ Application stopped"
else
    echo "   ✓ Application not running"
fi

# 2. Remove application
echo ""
echo "2. Removing application..."
if [ -d "/Applications/$APP_NAME.app" ]; then
    echo "   Removing /Applications/$APP_NAME.app"
    rm -rf "/Applications/$APP_NAME.app"
    echo "   ✓ Application removed"
else
    echo "   ℹ️  Application not found in /Applications"
fi

# 3. Remove Launch Agent (if exists)
echo ""
echo "3. Removing launch agent..."
LAUNCH_AGENT="$HOME/Library/LaunchAgents/$IDENTIFIER.plist"
if [ -f "$LAUNCH_AGENT" ]; then
    echo "   Unloading launch agent..."
    launchctl unload "$LAUNCH_AGENT" 2>/dev/null || true
    echo "   Removing $LAUNCH_AGENT"
    rm -f "$LAUNCH_AGENT"
    echo "   ✓ Launch agent removed"
else
    echo "   ℹ️  Launch agent not found"
fi

# 4. Remove application data
echo ""
echo "4. Removing application data..."
DATA_DIR="$HOME/Library/Application Support/VoiceAssistant"
if [ -d "$DATA_DIR" ]; then
    echo "   Removing $DATA_DIR"
    rm -rf "$DATA_DIR"
    echo "   ✓ Application data removed"
else
    echo "   ℹ️  Application data not found"
fi

# 5. Remove configuration files
echo ""
echo "5. Removing configuration files..."
CONFIG_DIR="$HOME/.voice-assistant"
if [ -d "$CONFIG_DIR" ]; then
    echo "   This directory contains:"
    du -sh "$CONFIG_DIR" 2>/dev/null || true
    echo ""
    read -p "   Remove ~/.voice-assistant (includes whisper.cpp models)? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "   Removing $CONFIG_DIR"
        rm -rf "$CONFIG_DIR"
        echo "   ✓ Configuration removed"
    else
        echo "   ℹ️  Keeping configuration files (can be removed manually)"
    fi
else
    echo "   ℹ️  Configuration directory not found"
fi

# 6. Remove log files
echo ""
echo "6. Removing log files..."
LOG_DIR="/tmp/voice-assistant"
if [ -d "$LOG_DIR" ]; then
    echo "   Removing $LOG_DIR"
    rm -rf "$LOG_DIR"
    echo "   ✓ Logs removed"
else
    echo "   ℹ️  Log directory not found"
fi

# 7. Remove user logs
USER_LOGS="$HOME/Library/Logs/VoiceAssistant"
if [ -d "$USER_LOGS" ]; then
    echo "   Removing $USER_LOGS"
    rm -rf "$USER_LOGS"
    echo "   ✓ User logs removed"
else
    echo "   ℹ️  User logs not found"
fi

# 8. Remove preferences
echo ""
echo "7. Removing preferences..."
PREFS="$HOME/Library/Preferences/$IDENTIFIER.plist"
if [ -f "$PREFS" ]; then
    echo "   Removing $PREFS"
    rm -f "$PREFS"
    echo "   ✓ Preferences removed"
else
    echo "   ℹ️  Preferences not found"
fi

# 9. Remove Keychain items
echo ""
echo "8. Removing Keychain items..."
echo "   Note: You may be prompted for your password to remove stored API keys"
security delete-generic-password -s "VoiceAssistant" 2>/dev/null && echo "   ✓ Keychain items removed" || echo "   ℹ️  No keychain items found"

# 10. Remove cache files
echo ""
echo "9. Removing cache files..."
CACHE_DIR="$HOME/Library/Caches/$IDENTIFIER"
if [ -d "$CACHE_DIR" ]; then
    echo "   Removing $CACHE_DIR"
    rm -rf "$CACHE_DIR"
    echo "   ✓ Cache removed"
else
    echo "   ℹ️  Cache not found"
fi

# 11. Remove receipts (if installed via pkg)
echo ""
echo "10. Removing installation receipts..."
if [ -f "/var/db/receipts/$IDENTIFIER.plist" ]; then
    echo "   Removing package receipt (requires sudo)..."
    sudo rm -f "/var/db/receipts/$IDENTIFIER.plist"
    sudo rm -f "/var/db/receipts/$IDENTIFIER.bom"
    echo "   ✓ Receipts removed"
else
    echo "   ℹ️  No installation receipts found"
fi

# Summary
echo ""
echo "================================================"
echo "✅ Uninstallation Complete!"
echo "================================================"
echo ""
echo "Voice Assistant has been removed from your Mac."
echo ""
echo "The following were removed:"
echo "  ✓ Application (/Applications/$APP_NAME.app)"
echo "  ✓ Application data"
echo "  ✓ Preferences"
echo "  ✓ Log files"
echo "  ✓ Cache files"
echo "  ✓ Keychain items"
echo ""

# Check what remains
REMAINS=()
[ -d "$CONFIG_DIR" ] && REMAINS+=("  • Configuration files: $CONFIG_DIR")
[ -d "$HOME/Library/Application Support/VoiceAssistant" ] && REMAINS+=("  • App data: ~/Library/Application Support/VoiceAssistant")

if [ ${#REMAINS[@]} -gt 0 ]; then
    echo "Items that were kept (you can remove manually if desired):"
    printf '%s\n' "${REMAINS[@]}"
    echo ""
fi

echo "Thank you for trying Voice Assistant!"
echo ""
echo "To reinstall, download from:"
echo "  https://github.com/yourusername/macos-voice-assistant/releases"
echo ""

# Optional: Open feedback form
read -p "Would you like to provide feedback about why you're uninstalling? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    open "https://github.com/yourusername/macos-voice-assistant/discussions/categories/feedback"
fi

exit 0
