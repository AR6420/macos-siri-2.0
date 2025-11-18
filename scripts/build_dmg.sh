#!/bin/bash
# Build macOS .dmg installer for Voice Assistant
# Requires: create-dmg (install with: brew install create-dmg)

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Configuration
APP_NAME="Voice Assistant"
BUNDLE_NAME="VoiceAssistant"
VERSION=$(grep "version" "$PROJECT_ROOT/python-service/pyproject.toml" | head -1 | sed 's/.*"\(.*\)".*/\1/')
DMG_NAME="${BUNDLE_NAME}-${VERSION}.dmg"
TEMP_DMG="temp.dmg"

SWIFT_PROJECT="$PROJECT_ROOT/swift-app"
BUILD_DIR="$SWIFT_PROJECT/build/Release"
APP_PATH="$BUILD_DIR/${BUNDLE_NAME}.app"
DIST_DIR="$PROJECT_ROOT/dist"

echo "================================================"
echo "Building Voice Assistant .dmg Installer"
echo "Version: $VERSION"
echo "================================================"
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ Error: This script must be run on macOS"
    exit 1
fi

# Check for create-dmg
if ! command -v create-dmg &> /dev/null; then
    echo "❌ Error: create-dmg is required but not installed"
    echo "Install with: brew install create-dmg"
    exit 1
fi

# Check for Xcode
if ! command -v xcodebuild &> /dev/null; then
    echo "❌ Error: Xcode command line tools are required"
    echo "Install with: xcode-select --install"
    exit 1
fi

# Build Swift application
echo "🔨 Building Swift application..."
cd "$SWIFT_PROJECT"

# Clean previous builds
echo "  Cleaning previous builds..."
rm -rf build

# Build for Release
echo "  Building for Release..."
xcodebuild \
    -scheme VoiceAssistant \
    -configuration Release \
    -derivedDataPath build \
    CODE_SIGN_IDENTITY="" \
    CODE_SIGNING_REQUIRED=NO \
    CODE_SIGNING_ALLOWED=NO

# Verify app was built
if [ ! -d "$APP_PATH" ]; then
    echo "❌ Error: App not found at $APP_PATH"
    echo "Build may have failed."
    exit 1
fi

echo "  ✓ App built successfully"

# Bundle Python backend into app
echo ""
echo "📦 Bundling Python backend..."

RESOURCES_DIR="$APP_PATH/Contents/Resources"
mkdir -p "$RESOURCES_DIR"

# Copy Python service
echo "  Copying Python service..."
cp -R "$PROJECT_ROOT/python-service" "$RESOURCES_DIR/"

# Copy configuration
echo "  Copying configuration..."
cp "$PROJECT_ROOT/python-service/config.yaml" "$RESOURCES_DIR/"

# Copy whisper.cpp (if installed)
if [ -d "$HOME/.voice-assistant/whisper.cpp" ]; then
    echo "  Bundling whisper.cpp..."
    mkdir -p "$RESOURCES_DIR/whisper.cpp"
    cp -R "$HOME/.voice-assistant/whisper.cpp/build" "$RESOURCES_DIR/whisper.cpp/"
    cp -R "$HOME/.voice-assistant/whisper.cpp/models" "$RESOURCES_DIR/whisper.cpp/"
else
    echo "  ⚠️  Warning: whisper.cpp not found at ~/.voice-assistant/whisper.cpp"
    echo "     Run scripts/setup_whisper.sh first for full functionality"
fi

# Create distribution directory
echo ""
echo "📁 Creating distribution directory..."
mkdir -p "$DIST_DIR"
cd "$DIST_DIR"

# Remove old DMG if exists
[ -f "$DMG_NAME" ] && rm "$DMG_NAME"
[ -f "$TEMP_DMG" ] && rm "$TEMP_DMG"

# Create DMG
echo ""
echo "💿 Creating DMG installer..."

create-dmg \
    --volname "${APP_NAME}" \
    --volicon "$SWIFT_PROJECT/Resources/Assets.xcassets/AppIcon.icns" \
    --window-pos 200 120 \
    --window-size 800 400 \
    --icon-size 100 \
    --icon "${BUNDLE_NAME}.app" 175 120 \
    --hide-extension "${BUNDLE_NAME}.app" \
    --app-drop-link 625 120 \
    --background "$SWIFT_PROJECT/Resources/dmg-background.png" \
    --no-internet-enable \
    "$DMG_NAME" \
    "$APP_PATH"

# Calculate DMG size
DMG_SIZE=$(du -h "$DMG_NAME" | cut -f1)

# Summary
echo ""
echo "================================================"
echo "✅ DMG created successfully!"
echo "================================================"
echo ""
echo "Details:"
echo "  File: $DIST_DIR/$DMG_NAME"
echo "  Size: $DMG_SIZE"
echo "  Version: $VERSION"
echo ""
echo "Testing the DMG:"
echo "  1. Open: $DMG_NAME"
echo "  2. Drag app to Applications folder"
echo "  3. Launch from Applications"
echo ""
echo "For distribution:"
echo "  - Code sign: codesign --sign \"Developer ID\" \"$APP_PATH\""
echo "  - Notarize: xcrun notarytool submit \"$DMG_NAME\""
echo "  - Staple: xcrun stapler staple \"$DMG_NAME\""
echo ""
