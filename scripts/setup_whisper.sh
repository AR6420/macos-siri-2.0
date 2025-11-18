#!/bin/bash
# Setup script for whisper.cpp with Core ML acceleration
# Target: macOS Tahoe 26.1 on Apple Silicon

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
INSTALL_DIR="$HOME/.voice-assistant"
WHISPER_DIR="$INSTALL_DIR/whisper.cpp"

echo "================================================"
echo "Voice Assistant - Whisper.cpp Setup"
echo "================================================"
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ Error: This script must be run on macOS"
    exit 1
fi

# Check for Apple Silicon
ARCH=$(uname -m)
if [[ "$ARCH" != "arm64" ]]; then
    echo "⚠️  Warning: Not running on Apple Silicon. Core ML acceleration may not work."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create installation directory
echo "📁 Creating installation directory..."
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Clone whisper.cpp if not already present
if [ -d "$WHISPER_DIR" ]; then
    echo "📦 whisper.cpp already exists, pulling latest changes..."
    cd "$WHISPER_DIR"
    git pull
else
    echo "📦 Cloning whisper.cpp..."
    git clone https://github.com/ggml-org/whisper.cpp.git
    cd "$WHISPER_DIR"
fi

# Install dependencies
echo ""
echo "📦 Installing dependencies..."

# Check for Homebrew
if ! command -v brew &> /dev/null; then
    echo "❌ Error: Homebrew is required but not installed."
    echo "Install it from: https://brew.sh"
    exit 1
fi

# Install CMake if not present
if ! command -v cmake &> /dev/null; then
    echo "Installing CMake..."
    brew install cmake
else
    echo "✓ CMake already installed"
fi

# Install Python dependencies for Core ML conversion
echo ""
echo "🐍 Installing Python dependencies for Core ML..."
pip3 install --upgrade pip
pip3 install ane_transformers openai-whisper coremltools

# Download models
echo ""
echo "⬇️  Downloading Whisper models..."
MODEL_DIR="$WHISPER_DIR/models"

# Function to download and convert model
download_and_convert_model() {
    local model_name=$1
    echo ""
    echo "Processing model: $model_name"

    # Download GGML model
    if [ ! -f "$MODEL_DIR/ggml-$model_name.bin" ]; then
        echo "  Downloading GGML model..."
        bash "$WHISPER_DIR/models/download-ggml-model.sh" "$model_name"
    else
        echo "  ✓ GGML model already exists"
    fi

    # Generate Core ML model
    if [ ! -d "$MODEL_DIR/ggml-$model_name-encoder.mlmodelc" ]; then
        echo "  Generating Core ML model (this may take several minutes)..."
        bash "$WHISPER_DIR/models/generate-coreml-model.sh" "$model_name"
    else
        echo "  ✓ Core ML model already exists"
    fi
}

# Download recommended models
download_and_convert_model "base.en"
download_and_convert_model "small.en"

# Optional: Download medium model (commented out by default due to size)
# read -p "Download medium.en model? (larger, more accurate) (y/n) " -n 1 -r
# echo
# if [[ $REPLY =~ ^[Yy]$ ]]; then
#     download_and_convert_model "medium.en"
# fi

# Build whisper.cpp with Core ML and Metal support
echo ""
echo "🔨 Building whisper.cpp with Core ML and Metal acceleration..."

# Clean previous builds
rm -rf build

# Configure with CMake
cmake -B build \
    -DWHISPER_COREML=1 \
    -DWHISPER_METAL=1 \
    -DCMAKE_BUILD_TYPE=Release

# Build
cmake --build build -j --config Release

# Verify binary was created
if [ ! -f "build/bin/main" ]; then
    echo "❌ Error: Build failed - binary not found at build/bin/main"
    exit 1
fi

# Test whisper.cpp
echo ""
echo "🧪 Testing whisper.cpp..."

# Download a test audio file if samples directory doesn't exist
if [ ! -d "samples" ]; then
    mkdir -p samples
fi

if [ ! -f "samples/jfk.wav" ]; then
    echo "Downloading test audio..."
    curl -L "https://github.com/ggerganov/whisper.cpp/raw/master/samples/jfk.wav" \
        -o "samples/jfk.wav"
fi

# Run test transcription
echo "Running test transcription..."
./build/bin/main -m models/ggml-base.en.bin -f samples/jfk.wav

# Create convenience symlink
echo ""
echo "🔗 Creating convenience symlinks..."
mkdir -p "$INSTALL_DIR/bin"
ln -sf "$WHISPER_DIR/build/bin/main" "$INSTALL_DIR/bin/whisper"

# Update config.yaml with correct paths
CONFIG_FILE="$PROJECT_ROOT/python-service/config.yaml"
if [ -f "$CONFIG_FILE" ]; then
    echo ""
    echo "📝 Updating config.yaml with installation paths..."

    # Note: On Linux we use sed differently than macOS
    # This is a placeholder - actual implementation would use Python or proper sed
    echo "  Please manually verify paths in config.yaml:"
    echo "  - whisper.model_path: $MODEL_DIR"
    echo "  - whisper.binary_path: $WHISPER_DIR/build/bin/main"
fi

# Summary
echo ""
echo "================================================"
echo "✅ Whisper.cpp setup complete!"
echo "================================================"
echo ""
echo "Installation details:"
echo "  Whisper directory: $WHISPER_DIR"
echo "  Binary location: $WHISPER_DIR/build/bin/main"
echo "  Models directory: $MODEL_DIR"
echo "  Convenience binary: $INSTALL_DIR/bin/whisper"
echo ""
echo "Available models:"
ls -lh "$MODEL_DIR"/ggml-*.bin 2>/dev/null || echo "  (Run download script to add models)"
echo ""
echo "Core ML models:"
ls -d "$MODEL_DIR"/*.mlmodelc 2>/dev/null || echo "  (No Core ML models found)"
echo ""
echo "To test manually:"
echo "  $WHISPER_DIR/build/bin/main -m $MODEL_DIR/ggml-small.en.bin -f your_audio.wav"
echo ""
echo "Next steps:"
echo "  1. Verify paths in python-service/config.yaml"
echo "  2. Test with: voice-assistant-test"
echo "  3. Run the voice assistant: voice-assistant"
echo ""
