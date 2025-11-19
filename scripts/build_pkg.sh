#!/bin/bash
# Build macOS .pkg installer for Voice Assistant
# Creates a proper installer package with pre/post-install scripts

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Configuration
APP_NAME="Voice Assistant"
BUNDLE_NAME="VoiceAssistant"
IDENTIFIER="com.voiceassistant.app"
VERSION=$(grep "version" "$PROJECT_ROOT/python-service/pyproject.toml" | head -1 | sed 's/.*"\(.*\)".*/\1/')
PKG_NAME="${BUNDLE_NAME}-${VERSION}.pkg"

SWIFT_PROJECT="$PROJECT_ROOT/swift-app"
BUILD_DIR="$SWIFT_PROJECT/build/Release"
APP_PATH="$BUILD_DIR/${BUNDLE_NAME}.app"
DIST_DIR="$PROJECT_ROOT/dist"
PKG_ROOT="$DIST_DIR/pkg-root"
PKG_SCRIPTS="$DIST_DIR/pkg-scripts"

echo "================================================"
echo "Building Voice Assistant .pkg Installer"
echo "Version: $VERSION"
echo "================================================"
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ Error: This script must be run on macOS"
    exit 1
fi

# Check for Xcode
if ! command -v xcodebuild &> /dev/null; then
    echo "❌ Error: Xcode command line tools are required"
    echo "Install with: xcode-select --install"
    exit 1
fi

# Build Swift application (if not already built)
if [ ! -d "$APP_PATH" ]; then
    echo "🔨 Building Swift application..."
    cd "$SWIFT_PROJECT"
    xcodebuild \
        -scheme VoiceAssistant \
        -configuration Release \
        -destination "platform=macOS,arch=arm64" \
        -derivedDataPath build \
        CODE_SIGN_IDENTITY="" \
        CODE_SIGNING_REQUIRED=NO \
        CODE_SIGNING_ALLOWED=NO

    if [ ! -d "$APP_PATH" ]; then
        echo "❌ Error: Build failed"
        exit 1
    fi
    echo "  ✓ App built successfully"
else
    echo "✓ Using existing app build"
fi

# Create package directories
echo ""
echo "📁 Creating package structure..."
rm -rf "$PKG_ROOT" "$PKG_SCRIPTS"
mkdir -p "$PKG_ROOT/Applications"
mkdir -p "$PKG_SCRIPTS"

# Copy app to package root
echo "  Copying application..."
cp -R "$APP_PATH" "$PKG_ROOT/Applications/"

# Create pre-install script
echo ""
echo "📝 Creating installation scripts..."

cat > "$PKG_SCRIPTS/preinstall" << 'EOF'
#!/bin/bash
# Pre-installation script

echo "Voice Assistant Pre-Install"

# Kill running instance if exists
killall VoiceAssistant 2>/dev/null || true

# Remove old version if exists
if [ -d "/Applications/VoiceAssistant.app" ]; then
    echo "Removing old version..."
    rm -rf "/Applications/VoiceAssistant.app"
fi

exit 0
EOF

# Create post-install script
cat > "$PKG_SCRIPTS/postinstall" << 'EOF'
#!/bin/bash
# Post-installation script

echo "Voice Assistant Post-Install"

# Get the user who invoked the installer
CONSOLE_USER=$(stat -f "%Su" /dev/console)
USER_HOME=$(eval echo "~$CONSOLE_USER")

# Create data directory
DATA_DIR="$USER_HOME/Library/Application Support/VoiceAssistant"
mkdir -p "$DATA_DIR"
chown -R "$CONSOLE_USER:staff" "$DATA_DIR"

# Create log directory
LOG_DIR="/tmp/voice-assistant/logs"
mkdir -p "$LOG_DIR"
chmod 777 "$LOG_DIR"

# Copy default configuration if not exists
CONFIG_FILE="$DATA_DIR/config.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Installing default configuration..."
    cp "/Applications/VoiceAssistant.app/Contents/Resources/config.yaml" "$CONFIG_FILE"
    chown "$CONSOLE_USER:staff" "$CONFIG_FILE"
fi

# Install Python dependencies (optional)
# Note: This requires Python to be installed
if command -v python3 &> /dev/null; then
    echo "Installing Python dependencies..."

    # Install Poetry if not present
    if ! command -v poetry &> /dev/null; then
        sudo -u "$CONSOLE_USER" pip3 install poetry
    fi

    # Install dependencies
    cd "/Applications/VoiceAssistant.app/Contents/Resources/python-service"
    sudo -u "$CONSOLE_USER" poetry install --no-dev
else
    echo "Warning: Python 3 not found. Please install Python and run setup manually."
fi

# Display success message
cat << 'WELCOME'

╔════════════════════════════════════════════════════════╗
║                                                        ║
║           Voice Assistant Installed!                   ║
║                                                        ║
║  Next steps:                                           ║
║  1. Open Voice Assistant from Applications folder      ║
║  2. Grant required permissions (Microphone, etc.)      ║
║  3. Configure your LLM backend in Preferences          ║
║  4. Say "Hey Claude" to start using!                   ║
║                                                        ║
╚════════════════════════════════════════════════════════╝

WELCOME

exit 0
EOF

# Make scripts executable
chmod +x "$PKG_SCRIPTS/preinstall"
chmod +x "$PKG_SCRIPTS/postinstall"

echo "  ✓ Installation scripts created"

# Build component package
echo ""
echo "📦 Building component package..."

COMPONENT_PKG="$DIST_DIR/${BUNDLE_NAME}-component.pkg"

pkgbuild \
    --root "$PKG_ROOT" \
    --identifier "$IDENTIFIER" \
    --version "$VERSION" \
    --install-location "/" \
    --scripts "$PKG_SCRIPTS" \
    "$COMPONENT_PKG"

# Create distribution XML
echo ""
echo "📝 Creating distribution definition..."

cat > "$DIST_DIR/distribution.xml" << EOF
<?xml version="1.0" encoding="utf-8"?>
<installer-gui-script minSpecVersion="1">
    <title>Voice Assistant</title>
    <organization>com.voiceassistant</organization>
    <domains enable_localSystem="true"/>
    <options customize="never" require-scripts="true" rootVolumeOnly="true"/>

    <welcome file="welcome.html" mime-type="text/html"/>
    <license file="license.html" mime-type="text/html"/>
    <conclusion file="conclusion.html" mime-type="text/html"/>

    <pkg-ref id="$IDENTIFIER"/>

    <options customize="never" require-scripts="false"/>

    <choices-outline>
        <line choice="default">
            <line choice="$IDENTIFIER"/>
        </line>
    </choices-outline>

    <choice id="default"/>

    <choice id="$IDENTIFIER" visible="false">
        <pkg-ref id="$IDENTIFIER"/>
    </choice>

    <pkg-ref id="$IDENTIFIER" version="$VERSION" onConclusion="none">
        ${BUNDLE_NAME}-component.pkg
    </pkg-ref>
</installer-gui-script>
EOF

# Create welcome HTML
cat > "$DIST_DIR/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        h1 { color: #007AFF; }
    </style>
</head>
<body>
    <h1>Welcome to Voice Assistant</h1>
    <p>This installer will install Voice Assistant on your Mac.</p>
    <p>Voice Assistant is a privacy-first AI voice assistant for macOS that runs entirely on your device.</p>
    <h2>Requirements:</h2>
    <ul>
        <li>macOS Tahoe 26.1 or later</li>
        <li>Apple Silicon Mac (M1 or later recommended)</li>
        <li>Python 3.9 or later</li>
        <li>At least 8GB of RAM (64GB+ recommended for local LLM)</li>
    </ul>
</body>
</html>
EOF

# Create license HTML
cat > "$DIST_DIR/license.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <h1>Apache License 2.0</h1>
    <pre>
Copyright 2024 Voice Assistant Contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
    </pre>
</body>
</html>
EOF

# Create conclusion HTML
cat > "$DIST_DIR/conclusion.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        h1 { color: #34C759; }
    </style>
</head>
<body>
    <h1>Installation Complete!</h1>
    <p>Voice Assistant has been successfully installed.</p>
    <h2>Next Steps:</h2>
    <ol>
        <li>Open <strong>Voice Assistant</strong> from your Applications folder</li>
        <li>Grant the required permissions when prompted</li>
        <li>Configure your preferred LLM backend in Preferences</li>
        <li>Say <strong>"Hey Claude"</strong> to activate the assistant</li>
    </ol>
    <p>For setup help, visit the documentation at: <a href="https://github.com/yourusername/macos-voice-assistant">GitHub</a></p>
</body>
</html>
EOF

# Build product package
echo ""
echo "📦 Building final installer package..."

cd "$DIST_DIR"

productbuild \
    --distribution distribution.xml \
    --resources "$DIST_DIR" \
    --package-path "$DIST_DIR" \
    "$PKG_NAME"

# Clean up temporary files
echo ""
echo "🧹 Cleaning up..."
rm -rf "$PKG_ROOT" "$PKG_SCRIPTS" "$COMPONENT_PKG"
rm -f distribution.xml welcome.html license.html conclusion.html

# Calculate package size
PKG_SIZE=$(du -h "$PKG_NAME" | cut -f1)

# Summary
echo ""
echo "================================================"
echo "✅ Package created successfully!"
echo "================================================"
echo ""
echo "Details:"
echo "  File: $DIST_DIR/$PKG_NAME"
echo "  Size: $PKG_SIZE"
echo "  Version: $VERSION"
echo "  Identifier: $IDENTIFIER"
echo ""
echo "Testing the installer:"
echo "  sudo installer -pkg \"$PKG_NAME\" -target /"
echo ""
echo "For distribution:"
echo "  - Sign: productsign --sign \"Developer ID Installer\" \"$PKG_NAME\" \"${PKG_NAME%.pkg}-signed.pkg\""
echo "  - Notarize: xcrun notarytool submit \"$PKG_NAME\""
echo ""
