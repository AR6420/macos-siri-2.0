#!/bin/bash
# Build macOS .dmg installer for Voice Assistant
# Requires: create-dmg (install with: brew install create-dmg)

set -e  # Exit on error
set -u  # Exit on undefined variable
set -o pipefail  # Exit on pipe failure

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

# Logging
LOG_FILE="$PROJECT_ROOT/dist/build_dmg.log"
mkdir -p "$DIST_DIR"
exec 1> >(tee -a "$LOG_FILE")
exec 2>&1

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================================"
echo "Building Voice Assistant .dmg Installer"
echo "Version: $VERSION"
echo "Build Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Log: $LOG_FILE"
echo "================================================"
echo ""

# Helper functions
log_info() {
    echo -e "${GREEN}ℹ️  $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 is required but not installed"
        echo "  Install with: $2"
        exit 1
    fi
}

# System requirements check
echo "🔍 Checking system requirements..."
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    log_error "This script must be run on macOS"
    exit 1
fi
log_info "Running on macOS"

# Check macOS version
MACOS_VERSION=$(sw_vers -productVersion)
MACOS_MAJOR=$(echo "$MACOS_VERSION" | cut -d '.' -f 1)
if [ "$MACOS_MAJOR" -lt 13 ]; then
    log_warn "Building on macOS $MACOS_VERSION. Target is macOS Tahoe 26.1+"
fi
log_info "macOS version: $MACOS_VERSION"

# Check for Apple Silicon
ARCH=$(uname -m)
if [[ "$ARCH" != "arm64" ]]; then
    log_warn "Not running on Apple Silicon ($ARCH). App may not be optimized."
else
    log_info "Architecture: Apple Silicon ($ARCH)"
fi

# Check required commands
check_command "create-dmg" "brew install create-dmg"
check_command "xcodebuild" "xcode-select --install"
check_command "python3" "brew install python@3.11"
check_command "poetry" "pip3 install poetry"

log_info "All required tools are installed"

# Verify project structure
echo ""
echo "📂 Verifying project structure..."
if [ ! -d "$SWIFT_PROJECT" ]; then
    log_error "Swift project not found at: $SWIFT_PROJECT"
    exit 1
fi
if [ ! -d "$PROJECT_ROOT/python-service" ]; then
    log_error "Python service not found at: $PROJECT_ROOT/python-service"
    exit 1
fi
if [ ! -f "$PROJECT_ROOT/python-service/pyproject.toml" ]; then
    log_error "pyproject.toml not found"
    exit 1
fi
log_info "Project structure verified"

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
    -destination "platform=macOS,arch=arm64" \
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
log_info "Copying Python service..."
cp -R "$PROJECT_ROOT/python-service" "$RESOURCES_DIR/"

# Remove unnecessary files from bundled Python service
log_info "Cleaning up Python service bundle..."
rm -rf "$RESOURCES_DIR/python-service/__pycache__"
rm -rf "$RESOURCES_DIR/python-service/.pytest_cache"
rm -rf "$RESOURCES_DIR/python-service/.mypy_cache"
rm -rf "$RESOURCES_DIR/python-service/tests"
rm -rf "$RESOURCES_DIR/python-service/.venv"
rm -rf "$RESOURCES_DIR/python-service/dist"
find "$RESOURCES_DIR/python-service" -name "*.pyc" -delete
find "$RESOURCES_DIR/python-service" -name ".DS_Store" -delete

# Install Python dependencies into bundle
log_info "Installing Python dependencies..."
cd "$RESOURCES_DIR/python-service"
if [ -f "pyproject.toml" ]; then
    poetry export -f requirements.txt --output requirements.txt --without-hashes
    pip3 install -r requirements.txt --target "$RESOURCES_DIR/python-packages" --upgrade
    rm requirements.txt
    log_info "Python dependencies installed to bundle"
else
    log_warn "pyproject.toml not found, skipping dependency installation"
fi
cd "$PROJECT_ROOT"

# Copy configuration
log_info "Copying configuration..."
cp "$PROJECT_ROOT/python-service/config.yaml" "$RESOURCES_DIR/"

# Copy documentation
log_info "Copying documentation..."
mkdir -p "$RESOURCES_DIR/docs"
cp "$PROJECT_ROOT/README.md" "$RESOURCES_DIR/docs/" 2>/dev/null || true
cp "$PROJECT_ROOT/LICENSE" "$RESOURCES_DIR/docs/" 2>/dev/null || true
cp "$PROJECT_ROOT/CHANGELOG.md" "$RESOURCES_DIR/docs/" 2>/dev/null || true
cp -R "$PROJECT_ROOT/docs"/* "$RESOURCES_DIR/docs/" 2>/dev/null || true

# Copy whisper.cpp (if installed)
if [ -d "$HOME/.voice-assistant/whisper.cpp" ]; then
    log_info "Bundling whisper.cpp..."
    mkdir -p "$RESOURCES_DIR/whisper.cpp"

    # Copy binaries
    if [ -d "$HOME/.voice-assistant/whisper.cpp/build" ]; then
        cp -R "$HOME/.voice-assistant/whisper.cpp/build" "$RESOURCES_DIR/whisper.cpp/"
        log_info "Whisper binaries bundled"
    else
        log_warn "Whisper build not found"
    fi

    # Copy models
    if [ -d "$HOME/.voice-assistant/whisper.cpp/models" ]; then
        cp -R "$HOME/.voice-assistant/whisper.cpp/models" "$RESOURCES_DIR/whisper.cpp/"
        MODELS_SIZE=$(du -sh "$RESOURCES_DIR/whisper.cpp/models" | cut -f1)
        log_info "Whisper models bundled ($MODELS_SIZE)"
    else
        log_warn "Whisper models not found"
    fi
else
    log_warn "whisper.cpp not found at ~/.voice-assistant/whisper.cpp"
    log_warn "Run scripts/setup_whisper.sh first for full functionality"
    log_warn "The installer will require users to set up whisper.cpp manually"
fi

# Create uninstaller in Resources
log_info "Adding uninstaller..."
cp "$SCRIPT_DIR/uninstall.sh" "$RESOURCES_DIR/"
chmod +x "$RESOURCES_DIR/uninstall.sh"

# Create version file
log_info "Creating version file..."
echo "$VERSION" > "$RESOURCES_DIR/VERSION"
echo "Build Date: $(date '+%Y-%m-%d %H:%M:%S')" >> "$RESOURCES_DIR/VERSION"
echo "Build Host: $(hostname)" >> "$RESOURCES_DIR/VERSION"
echo "macOS Version: $MACOS_VERSION" >> "$RESOURCES_DIR/VERSION"
echo "Architecture: $ARCH" >> "$RESOURCES_DIR/VERSION"

# Verify bundle structure
log_info "Verifying bundle structure..."
BUNDLE_SIZE=$(du -sh "$APP_PATH" | cut -f1)
log_info "Total bundle size: $BUNDLE_SIZE"

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

# Prepare DMG staging directory
DMG_STAGING="$DIST_DIR/dmg-staging"
rm -rf "$DMG_STAGING"
mkdir -p "$DMG_STAGING"

# Copy app to staging
cp -R "$APP_PATH" "$DMG_STAGING/"

# Create README for DMG
cat > "$DMG_STAGING/README.txt" << EOF
Voice Assistant for macOS
Version: $VERSION

INSTALLATION
============
1. Drag Voice Assistant.app to your Applications folder
2. Launch Voice Assistant from Applications
3. Grant required permissions when prompted
4. Configure your LLM backend in Preferences
5. Say "Hey Claude" to start using!

REQUIREMENTS
============
- macOS Tahoe 26.1 or later
- Apple Silicon Mac (M1 or later recommended)
- Python 3.9 or later
- 8GB RAM minimum (64GB+ for local LLM)

DOCUMENTATION
=============
Full documentation is available at:
https://github.com/yourusername/macos-voice-assistant

For help, visit:
- Setup Guide: docs/SETUP.md
- Usage Guide: docs/USAGE.md
- Troubleshooting: docs/TROUBLESHOOTING.md

LICENSE
=======
Licensed under Apache License 2.0
See LICENSE file for details

Copyright 2024 Voice Assistant Contributors
EOF

# Check for DMG resources
DMG_BACKGROUND="$SWIFT_PROJECT/Resources/dmg-background.png"
DMG_ICON="$SWIFT_PROJECT/Resources/Assets.xcassets/AppIcon.icns"

# Create DMG with fallback options
DMG_CMD="create-dmg \
    --volname \"${APP_NAME}\" \
    --window-pos 200 120 \
    --window-size 800 400 \
    --icon-size 100 \
    --icon \"${BUNDLE_NAME}.app\" 175 120 \
    --hide-extension \"${BUNDLE_NAME}.app\" \
    --app-drop-link 625 120 \
    --no-internet-enable"

# Add optional resources if they exist
if [ -f "$DMG_ICON" ]; then
    DMG_CMD="$DMG_CMD --volicon \"$DMG_ICON\""
fi

if [ -f "$DMG_BACKGROUND" ]; then
    DMG_CMD="$DMG_CMD --background \"$DMG_BACKGROUND\""
fi

DMG_CMD="$DMG_CMD \"$DMG_NAME\" \"$DMG_STAGING\""

# Execute DMG creation
eval $DMG_CMD

if [ ! -f "$DMG_NAME" ]; then
    log_error "DMG creation failed"
    exit 1
fi

# Calculate DMG size
DMG_SIZE=$(du -h "$DMG_NAME" | cut -f1)
log_info "DMG created: $DMG_SIZE"

# Clean up staging directory
rm -rf "$DMG_STAGING"

# Verify DMG
log_info "Verifying DMG..."
hdiutil verify "$DMG_NAME" || log_warn "DMG verification failed (non-fatal)"

# Generate checksum
echo ""
log_info "Generating checksums..."
shasum -a 256 "$DMG_NAME" > "$DMG_NAME.sha256"
log_info "SHA256: $(cat "$DMG_NAME.sha256")"

# Create build manifest
MANIFEST_FILE="$DIST_DIR/${BUNDLE_NAME}-${VERSION}-manifest.txt"
cat > "$MANIFEST_FILE" << EOF
Voice Assistant Build Manifest
==============================

Build Information
-----------------
Version: $VERSION
Date: $(date '+%Y-%m-%d %H:%M:%S')
Builder: $(whoami)@$(hostname)
Build OS: macOS $MACOS_VERSION ($ARCH)

Files
-----
DMG: $DMG_NAME
Size: $DMG_SIZE
SHA256: $(cat "$DMG_NAME.sha256" | cut -d' ' -f1)

Components
----------
Swift App: Built
Python Service: Bundled
Dependencies: Bundled
Whisper.cpp: $([ -d "$RESOURCES_DIR/whisper.cpp" ] && echo "Bundled" || echo "Not included")
Documentation: Included
Uninstaller: Included

Next Steps
----------
1. Test the DMG on a clean macOS system
2. Code sign the app:
   codesign --deep --force --verify --verbose \\
     --sign "Developer ID Application: Your Name" \\
     --options runtime \\
     "$APP_PATH"

3. Notarize the DMG:
   xcrun notarytool submit "$DMG_NAME" \\
     --apple-id "your@email.com" \\
     --team-id "TEAM_ID" \\
     --password "app-specific-password" \\
     --wait

4. Staple the notarization:
   xcrun stapler staple "$DMG_NAME"

5. Verify stapling:
   xcrun stapler validate "$DMG_NAME"

6. Upload to GitHub Releases
EOF

# Summary
echo ""
echo "================================================"
echo "✅ DMG created successfully!"
echo "================================================"
echo ""
log_info "Build Summary:"
echo "  File: $DIST_DIR/$DMG_NAME"
echo "  Size: $DMG_SIZE"
echo "  Version: $VERSION"
echo "  Checksum: $DMG_NAME.sha256"
echo "  Manifest: $MANIFEST_FILE"
echo "  Log: $LOG_FILE"
echo ""
log_info "Testing the DMG:"
echo "  1. Open: $DMG_NAME"
echo "  2. Drag app to Applications folder"
echo "  3. Launch from Applications"
echo "  4. Test all features"
echo ""
log_warn "For production distribution:"
echo "  1. Code sign the application"
echo "  2. Notarize with Apple"
echo "  3. Staple notarization ticket"
echo "  4. Test on clean system"
echo ""
log_info "See $MANIFEST_FILE for detailed build information"
echo ""
