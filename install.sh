#!/bin/bash
# Voice Assistant - One-Command Installer
# Run this script on macOS to install everything needed

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}✓ $1${NC}"
}

log_step() {
    echo -e "\n${BLUE}▶ $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

log_error() {
    echo -e "${RED}✗ $1${NC}"
}

check_macos() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        log_error "This script must be run on macOS"
        exit 1
    fi
    log_info "Running on macOS"
}

# Banner
echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║                                                        ║"
echo "║           Voice Assistant - Installer                 ║"
echo "║                                                        ║"
echo "║     AI-powered voice assistant for macOS              ║"
echo "║                                                        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Check macOS
check_macos

# Get project directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Step 1: Install Homebrew if needed
log_step "Step 1/6: Checking Homebrew..."
if ! command -v brew &> /dev/null; then
    echo "Homebrew not found. Installing..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    log_info "Homebrew installed"
else
    log_info "Homebrew already installed"
fi

# Step 2: Install system dependencies
log_step "Step 2/6: Installing system dependencies..."
echo "This may take a few minutes..."

DEPS_TO_INSTALL=""

# Check and queue each dependency
if ! command -v python3 &> /dev/null; then
    DEPS_TO_INSTALL="$DEPS_TO_INSTALL python@3.11"
fi

if ! command -v cmake &> /dev/null; then
    DEPS_TO_INSTALL="$DEPS_TO_INSTALL cmake"
fi

if ! command -v create-dmg &> /dev/null; then
    DEPS_TO_INSTALL="$DEPS_TO_INSTALL create-dmg"
fi

# Install queued dependencies
if [ -n "$DEPS_TO_INSTALL" ]; then
    echo "Installing:$DEPS_TO_INSTALL"
    brew install $DEPS_TO_INSTALL
    log_info "Dependencies installed"
else
    log_info "All dependencies already installed"
fi

# Check for Xcode Command Line Tools
if ! xcode-select -p &> /dev/null; then
    log_warn "Xcode Command Line Tools not found"
    echo "Installing Xcode Command Line Tools..."
    xcode-select --install
    echo ""
    echo "⏸  Please wait for Xcode Command Line Tools installation to complete,"
    echo "   then run this script again."
    exit 0
else
    log_info "Xcode Command Line Tools installed"
fi

# Step 3: Install Poetry
log_step "Step 3/6: Installing Poetry (Python dependency manager)..."
if ! command -v poetry &> /dev/null; then
    curl -sSL https://install.python-poetry.org | python3 -

    # Add to PATH for current session
    export PATH="$HOME/.local/bin:$PATH"

    log_info "Poetry installed"
else
    log_info "Poetry already installed"
fi

# Step 4: Install Python dependencies
log_step "Step 4/6: Installing Python dependencies..."
cd python-service
poetry install --no-root
log_info "Python dependencies installed"
cd ..

# Step 5: Setup Whisper.cpp
log_step "Step 5/6: Setting up Whisper.cpp (speech-to-text engine)..."
WHISPER_DIR="$HOME/.voice-assistant/whisper.cpp"

if [ -d "$WHISPER_DIR" ]; then
    log_info "Whisper.cpp already installed at $WHISPER_DIR"
else
    echo "This will download ~150MB and may take 5-10 minutes..."
    echo ""

    mkdir -p "$HOME/.voice-assistant"
    cd "$HOME/.voice-assistant"

    # Clone whisper.cpp
    echo "Cloning whisper.cpp..."
    git clone https://github.com/ggml-org/whisper.cpp.git
    cd whisper.cpp

    # Download model
    echo "Downloading Whisper small.en model..."
    bash ./models/download-ggml-model.sh small.en

    # Build with Core ML and Metal acceleration
    echo "Building with Apple Silicon optimizations..."
    cmake -B build -DWHISPER_COREML=1 -DWHISPER_METAL=1
    cmake --build build -j --config Release

    log_info "Whisper.cpp installed and built"
    cd "$SCRIPT_DIR"
fi

# Step 6: Build the macOS app
log_step "Step 6/6: Building Voice Assistant app..."
cd swift-app

# Check if already built
if [ -d "build/Release/VoiceAssistant.app" ]; then
    read -p "App already built. Rebuild? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Using existing build"
        cd ..
        echo ""
        log_step "Installation complete! 🎉"
        echo ""
        echo "Next steps:"
        echo "  1. Configure your Claude API key:"
        echo "     ${BLUE}export ANTHROPIC_API_KEY=\"your-key-here\"${NC}"
        echo ""
        echo "  2. Run the app:"
        echo "     ${BLUE}./run.sh${NC}"
        echo ""
        echo "Documentation: README.md, QUICKSTART.md"
        echo ""
        exit 0
    fi
    rm -rf build
fi

echo "Building app for Apple Silicon..."
xcodebuild \
    -scheme VoiceAssistant \
    -configuration Release \
    -destination "platform=macOS,arch=arm64" \
    -derivedDataPath build \
    CODE_SIGN_IDENTITY="" \
    CODE_SIGNING_REQUIRED=NO \
    CODE_SIGNING_ALLOWED=NO

if [ -d "build/Release/VoiceAssistant.app" ]; then
    log_info "App built successfully"
else
    log_error "Build failed"
    exit 1
fi

cd ..

# Success!
echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║                                                        ║"
echo "║          ✓ Installation Complete! 🎉                  ║"
echo "║                                                        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "📋 Next Steps:"
echo ""
echo "  1️⃣  Configure your Claude API key:"
echo "     ${BLUE}export ANTHROPIC_API_KEY=\"your-key-here\"${NC}"
echo ""
echo "     Get your key at: https://console.anthropic.com/"
echo ""
echo "  2️⃣  Run the app:"
echo "     ${BLUE}./run.sh${NC}"
echo ""
echo "  3️⃣  Grant permissions when prompted:"
echo "     • Microphone (for voice commands)"
echo "     • Accessibility (for inline AI)"
echo ""
echo "📚 Documentation:"
echo "  • Quick start: ${BLUE}cat QUICKSTART.md${NC}"
echo "  • Full guide: ${BLUE}cat README.md${NC}"
echo "  • Troubleshooting: ${BLUE}cat docs/TROUBLESHOOTING.md${NC}"
echo ""
echo "💡 Usage:"
echo "  • Say \"Hey Claude\" to activate voice assistant"
echo "  • Select text and click orange button for AI operations"
echo "  • Check menu bar for status"
echo ""
echo "Estimated cost: ~\$1-5/month with Claude Haiku 4.5"
echo ""
