#!/bin/bash
# Voice Assistant - Uninstaller
# Removes all Voice Assistant files and data

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║                                                        ║"
echo "║         Voice Assistant - Uninstaller                 ║"
echo "║                                                        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

echo -e "${YELLOW}⚠️  This will remove Voice Assistant and all its data.${NC}"
echo ""
echo "The following will be deleted:"
echo "  • Application bundle"
echo "  • Python dependencies (in this directory)"
echo "  • Whisper.cpp models (~/.voice-assistant/)"
echo "  • Configuration files (~/Library/Application Support/VoiceAssistant)"
echo "  • Preferences"
echo "  • Log files (/tmp/voice-assistant/)"
echo ""
echo -e "${RED}This action cannot be undone!${NC}"
echo ""

read -p "Are you sure you want to uninstall? (yes/no) " -r
echo

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Uninstall cancelled."
    exit 0
fi

echo ""
echo -e "${BLUE}▶ Uninstalling Voice Assistant...${NC}"
echo ""

# Stop running processes
echo "Stopping Voice Assistant processes..."
pkill -f "voice-assistant" 2>/dev/null || true
pkill -f "VoiceAssistant" 2>/dev/null || true
echo -e "${GREEN}✓ Processes stopped${NC}"

# Remove application bundle
if [ -d "swift-app/build/Release/VoiceAssistant.app" ]; then
    echo "Removing application bundle..."
    rm -rf swift-app/build/
    echo -e "${GREEN}✓ App bundle removed${NC}"
fi

# Remove installed app (if copied to Applications)
if [ -d "/Applications/VoiceAssistant.app" ]; then
    echo "Removing from Applications folder..."
    rm -rf "/Applications/VoiceAssistant.app"
    echo -e "${GREEN}✓ Removed from Applications${NC}"
fi

# Remove Whisper.cpp
if [ -d "$HOME/.voice-assistant" ]; then
    echo "Removing Whisper.cpp and models..."
    rm -rf "$HOME/.voice-assistant"
    echo -e "${GREEN}✓ Whisper.cpp removed${NC}"
fi

# Remove application support files
if [ -d "$HOME/Library/Application Support/VoiceAssistant" ]; then
    echo "Removing application data..."
    rm -rf "$HOME/Library/Application Support/VoiceAssistant"
    echo -e "${GREEN}✓ Application data removed${NC}"
fi

# Remove preferences
if [ -f "$HOME/Library/Preferences/com.voiceassistant.plist" ]; then
    echo "Removing preferences..."
    rm -f "$HOME/Library/Preferences/com.voiceassistant.plist"
    echo -e "${GREEN}✓ Preferences removed${NC}"
fi

# Remove logs
if [ -d "/tmp/voice-assistant" ]; then
    echo "Removing log files..."
    rm -rf /tmp/voice-assistant
    echo -e "${GREEN}✓ Log files removed${NC}"
fi

if [ -f "/tmp/voice-assistant.log" ]; then
    rm -f /tmp/voice-assistant.log
fi

# Remove Python virtual environment (if using venv)
if [ -d "python-service/.venv" ]; then
    echo "Removing Python virtual environment..."
    rm -rf python-service/.venv
    echo -e "${GREEN}✓ Virtual environment removed${NC}"
fi

# Ask about Poetry cache
echo ""
read -p "Also remove Poetry dependencies? (recommended if uninstalling completely) (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd python-service
    poetry env remove --all 2>/dev/null || true
    cd ..
    echo -e "${GREEN}✓ Poetry environments removed${NC}"
fi

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║                                                        ║"
echo "║        ✓ Uninstall Complete                           ║"
echo "║                                                        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "Voice Assistant has been removed from your system."
echo ""
echo "The following were NOT removed (manual cleanup if needed):"
echo "  • Homebrew and system packages (python, cmake, etc.)"
echo "  • Poetry itself"
echo "  • Source code in this directory"
echo ""
echo "To remove the source code:"
echo "  ${BLUE}cd .. && rm -rf macos-siri-2.0${NC}"
echo ""
echo "Thank you for trying Voice Assistant! 👋"
echo ""
