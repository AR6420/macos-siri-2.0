#!/bin/bash
# Voice Assistant - Quick Start Script
# Run this to start the Voice Assistant app

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_PATH="$SCRIPT_DIR/swift-app/build/Release/VoiceAssistant.app"

# Banner
echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║        Voice Assistant - Starting...                  ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Check if app is built
if [ ! -d "$APP_PATH" ]; then
    echo -e "${RED}✗ App not found at $APP_PATH${NC}"
    echo ""
    echo "Please run the installer first:"
    echo "  ${BLUE}./install.sh${NC}"
    echo ""
    exit 1
fi

# Check for API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${YELLOW}⚠ ANTHROPIC_API_KEY not set${NC}"
    echo ""
    echo "You'll need a Claude API key to use the AI features."
    echo ""
    echo "Options:"
    echo "  1. Set it now (temporary, for this session):"
    echo "     ${BLUE}export ANTHROPIC_API_KEY=\"your-key-here\"${NC}"
    echo ""
    echo "  2. Add to your shell profile (permanent):"
    echo "     ${BLUE}echo 'export ANTHROPIC_API_KEY=\"your-key-here\"' >> ~/.zshrc${NC}"
    echo ""
    echo "  3. Configure it in the app preferences after launching"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

# Start Python service in background
echo -e "${BLUE}▶ Starting Python service...${NC}"
cd "$SCRIPT_DIR/python-service"

# Kill any existing instances
pkill -f "voice-assistant" 2>/dev/null || true

# Start service in background
poetry run python -m voice_assistant.main > /tmp/voice-assistant.log 2>&1 &
PYTHON_PID=$!

echo -e "${GREEN}✓ Python service started (PID: $PYTHON_PID)${NC}"
echo "  Logs: /tmp/voice-assistant.log"

# Wait a moment for service to initialize
sleep 2

# Launch the macOS app
echo -e "${BLUE}▶ Launching Voice Assistant app...${NC}"
cd "$SCRIPT_DIR"
open "$APP_PATH"

echo -e "${GREEN}✓ App launched!${NC}"
echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║                                                        ║"
echo "║            Voice Assistant is Running! 🎉             ║"
echo "║                                                        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "📋 What's Happening:"
echo ""
echo "  ✓ Python service running in background"
echo "  ✓ Voice Assistant app launched"
echo "  ✓ Check menu bar for status icon"
echo ""
echo "🎤 Voice Commands:"
echo "  • Say \"Hey Claude\" or press Cmd+Shift+Space"
echo "  • Try: \"Hey Claude, what time is it?\""
echo "  • Try: \"Hey Claude, open Safari\""
echo ""
echo "✨ Inline AI:"
echo "  • Select any text in any app"
echo "  • Click the orange button that appears"
echo "  • Choose from 10 AI operations"
echo ""
echo "🔧 Managing the App:"
echo ""
echo "  View logs:"
echo "    ${BLUE}tail -f /tmp/voice-assistant.log${NC}"
echo ""
echo "  Stop the app:"
echo "    ${BLUE}pkill -f voice-assistant${NC}"
echo "    Then quit from menu bar"
echo ""
echo "  Restart:"
echo "    ${BLUE}./run.sh${NC}"
echo ""
echo "💡 First Time Setup:"
echo ""
echo "  1. Grant Microphone permission when prompted"
echo "  2. Grant Accessibility permission when prompted"
echo "  3. Configure API key in Preferences (menu bar → Preferences)"
echo ""
echo "📚 Need Help?"
echo "  • Troubleshooting: ${BLUE}cat docs/TROUBLESHOOTING.md${NC}"
echo "  • Features: ${BLUE}cat INLINE_AI_FEATURE.md${NC}"
echo "  • Quick guide: ${BLUE}cat QUICKSTART.md${NC}"
echo ""
echo "Enjoy! 🚀"
echo ""
