#!/bin/bash
# Build Verification Script for Voice Assistant
# Verifies that all components are properly built and bundled

set -e
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Configuration
BUNDLE_NAME="VoiceAssistant"
VERSION=$(grep "version" "$PROJECT_ROOT/python-service/pyproject.toml" | head -1 | sed 's/.*"\(.*\)".*/\1/')
DIST_DIR="$PROJECT_ROOT/dist"
DMG_NAME="${BUNDLE_NAME}-${VERSION}.dmg"
PKG_NAME="${BUNDLE_NAME}-${VERSION}.pkg"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

echo "================================================"
echo "Voice Assistant Build Verification"
echo "Version: $VERSION"
echo "================================================"
echo ""

# Helper functions
pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASS_COUNT++))
}

fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAIL_COUNT++))
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARN_COUNT++))
}

info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

check_file() {
    if [ -f "$1" ]; then
        pass "File exists: $1"
        return 0
    else
        fail "Missing file: $1"
        return 1
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        pass "Directory exists: $1"
        return 0
    else
        fail "Missing directory: $1"
        return 1
    fi
}

check_executable() {
    if [ -x "$1" ]; then
        pass "Executable: $1"
        return 0
    else
        fail "Not executable: $1"
        return 1
    fi
}

# 1. Check project structure
echo "1. Verifying Project Structure"
echo "--------------------------------"
check_dir "$PROJECT_ROOT/swift-app"
check_dir "$PROJECT_ROOT/python-service"
check_dir "$PROJECT_ROOT/scripts"
check_dir "$PROJECT_ROOT/docs"
check_file "$PROJECT_ROOT/README.md"
check_file "$PROJECT_ROOT/LICENSE"
check_file "$PROJECT_ROOT/CHANGELOG.md"
check_file "$PROJECT_ROOT/VERSION"
check_file "$PROJECT_ROOT/python-service/pyproject.toml"
check_file "$PROJECT_ROOT/python-service/config.yaml"
echo ""

# 2. Check build scripts
echo "2. Verifying Build Scripts"
echo "----------------------------"
check_executable "$SCRIPT_DIR/build_dmg.sh"
check_executable "$SCRIPT_DIR/build_pkg.sh"
check_executable "$SCRIPT_DIR/setup_whisper.sh"
check_executable "$SCRIPT_DIR/uninstall.sh"
check_executable "$SCRIPT_DIR/verify_build.sh"
echo ""

# 3. Check Python service structure
echo "3. Verifying Python Service"
echo "----------------------------"
PYTHON_SRC="$PROJECT_ROOT/python-service/src/voice_assistant"
check_dir "$PYTHON_SRC"
check_dir "$PYTHON_SRC/audio"
check_dir "$PYTHON_SRC/stt"
check_dir "$PYTHON_SRC/llm"
check_dir "$PYTHON_SRC/mcp"
check_file "$PYTHON_SRC/__init__.py"
check_file "$PYTHON_SRC/orchestrator.py"
echo ""

# 4. Check build artifacts
echo "4. Verifying Build Artifacts"
echo "-----------------------------"
if check_dir "$DIST_DIR"; then
    # Check for DMG
    if [ -f "$DIST_DIR/$DMG_NAME" ]; then
        pass "DMG exists: $DMG_NAME"
        DMG_SIZE=$(du -h "$DIST_DIR/$DMG_NAME" | cut -f1)
        info "DMG size: $DMG_SIZE"

        # Check DMG checksum
        if [ -f "$DIST_DIR/$DMG_NAME.sha256" ]; then
            pass "DMG checksum exists"
            info "SHA256: $(cat "$DIST_DIR/$DMG_NAME.sha256" | cut -d' ' -f1)"
        else
            warn "DMG checksum missing"
        fi

        # Verify DMG can be mounted (macOS only)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            info "Attempting to verify DMG structure..."
            hdiutil verify "$DIST_DIR/$DMG_NAME" &>/dev/null && pass "DMG structure valid" || warn "DMG verification failed"
        fi
    else
        warn "DMG not found: $DMG_NAME"
        info "Run ./scripts/build_dmg.sh to create DMG"
    fi

    # Check for PKG
    if [ -f "$DIST_DIR/$PKG_NAME" ]; then
        pass "PKG exists: $PKG_NAME"
        PKG_SIZE=$(du -h "$DIST_DIR/$PKG_NAME" | cut -f1)
        info "PKG size: $PKG_SIZE"

        # Verify PKG structure (macOS only)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            pkgutil --check-signature "$DIST_DIR/$PKG_NAME" &>/dev/null && pass "PKG signature valid" || warn "PKG not signed"
        fi
    else
        warn "PKG not found: $PKG_NAME"
        info "Run ./scripts/build_pkg.sh to create PKG"
    fi

    # Check for build manifest
    MANIFEST="$DIST_DIR/${BUNDLE_NAME}-${VERSION}-manifest.txt"
    if [ -f "$MANIFEST" ]; then
        pass "Build manifest exists"
        info "Manifest: $MANIFEST"
    else
        warn "Build manifest missing"
    fi
else
    fail "Distribution directory not found: $DIST_DIR"
    info "Run build scripts to create distribution artifacts"
fi
echo ""

# 5. Check Swift app build (if on macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "5. Verifying Swift App Build"
    echo "------------------------------"
    SWIFT_BUILD="$PROJECT_ROOT/swift-app/build/Release/${BUNDLE_NAME}.app"

    if [ -d "$SWIFT_BUILD" ]; then
        pass "Swift app built: $SWIFT_BUILD"

        # Check app bundle structure
        check_dir "$SWIFT_BUILD/Contents"
        check_dir "$SWIFT_BUILD/Contents/MacOS"
        check_dir "$SWIFT_BUILD/Contents/Resources"
        check_file "$SWIFT_BUILD/Contents/Info.plist"
        check_executable "$SWIFT_BUILD/Contents/MacOS/$BUNDLE_NAME"

        # Check bundled Python service
        if check_dir "$SWIFT_BUILD/Contents/Resources/python-service"; then
            check_file "$SWIFT_BUILD/Contents/Resources/python-service/pyproject.toml"
            check_file "$SWIFT_BUILD/Contents/Resources/config.yaml"
        fi

        # Check bundled documentation
        if check_dir "$SWIFT_BUILD/Contents/Resources/docs"; then
            info "Documentation bundled"
        fi

        # Check for uninstaller
        if [ -f "$SWIFT_BUILD/Contents/Resources/uninstall.sh" ]; then
            pass "Uninstaller bundled"
            check_executable "$SWIFT_BUILD/Contents/Resources/uninstall.sh"
        else
            warn "Uninstaller not bundled"
        fi

        # Check for version file
        check_file "$SWIFT_BUILD/Contents/Resources/VERSION"

        # Check bundle size
        BUNDLE_SIZE=$(du -sh "$SWIFT_BUILD" | cut -f1)
        info "Bundle size: $BUNDLE_SIZE"

        # Check code signing
        codesign -dv "$SWIFT_BUILD" &>/dev/null && pass "App is code signed" || warn "App is not code signed"
    else
        warn "Swift app not built"
        info "Run ./scripts/build_dmg.sh to build the app"
    fi
    echo ""
else
    info "Skipping Swift app verification (not on macOS)"
    echo ""
fi

# 6. Check whisper.cpp installation
echo "6. Verifying Whisper.cpp Setup"
echo "-------------------------------"
WHISPER_DIR="$HOME/.voice-assistant/whisper.cpp"
if [ -d "$WHISPER_DIR" ]; then
    pass "Whisper.cpp installed"

    # Check build
    if [ -f "$WHISPER_DIR/build/bin/main" ]; then
        pass "Whisper binary exists"
        check_executable "$WHISPER_DIR/build/bin/main"
    else
        warn "Whisper binary not found"
        info "Run ./scripts/setup_whisper.sh"
    fi

    # Check models
    if [ -d "$WHISPER_DIR/models" ]; then
        MODEL_COUNT=$(find "$WHISPER_DIR/models" -name "*.bin" | wc -l)
        if [ "$MODEL_COUNT" -gt 0 ]; then
            pass "Whisper models found ($MODEL_COUNT models)"
            ls "$WHISPER_DIR/models"/*.bin 2>/dev/null | while read model; do
                info "  - $(basename $model)"
            done
        else
            warn "No Whisper models found"
        fi
    else
        warn "Models directory not found"
    fi
else
    warn "Whisper.cpp not installed"
    info "Run ./scripts/setup_whisper.sh to install"
fi
echo ""

# 7. Check documentation
echo "7. Verifying Documentation"
echo "---------------------------"
check_file "$PROJECT_ROOT/docs/SETUP.md"
check_file "$PROJECT_ROOT/docs/USAGE.md"
check_file "$PROJECT_ROOT/docs/TROUBLESHOOTING.md"

if [ -f "$PROJECT_ROOT/DEPLOYMENT.md" ]; then
    pass "DEPLOYMENT.md exists"
else
    warn "DEPLOYMENT.md missing"
fi

if [ -f "$PROJECT_ROOT/INSTALLATION.md" ]; then
    pass "INSTALLATION.md exists"
else
    warn "INSTALLATION.md missing"
fi

if [ -f "$PROJECT_ROOT/RELEASE_CHECKLIST.md" ]; then
    pass "RELEASE_CHECKLIST.md exists"
else
    warn "RELEASE_CHECKLIST.md missing"
fi
echo ""

# 8. Check Python dependencies
echo "8. Verifying Python Dependencies"
echo "----------------------------------"
if command -v poetry &> /dev/null; then
    pass "Poetry is installed"
    cd "$PROJECT_ROOT/python-service"
    if poetry check &>/dev/null; then
        pass "pyproject.toml is valid"
    else
        fail "pyproject.toml has errors"
    fi
    cd "$PROJECT_ROOT"
else
    warn "Poetry not installed"
    info "Install with: pip3 install poetry"
fi

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    pass "Python installed: $PYTHON_VERSION"

    # Check minimum version (3.9+)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 9 ]; then
        pass "Python version is compatible (>= 3.9)"
    else
        fail "Python version too old. Requires 3.9+"
    fi
else
    fail "Python 3 not installed"
fi
echo ""

# 9. Summary
echo "================================================"
echo "Verification Summary"
echo "================================================"
echo ""
echo -e "${GREEN}Passed:${NC}  $PASS_COUNT"
echo -e "${YELLOW}Warnings:${NC} $WARN_COUNT"
echo -e "${RED}Failed:${NC}  $FAIL_COUNT"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    if [ $WARN_COUNT -eq 0 ]; then
        echo -e "${GREEN}✅ All checks passed! Build is ready for distribution.${NC}"
        EXIT_CODE=0
    else
        echo -e "${YELLOW}⚠️  Build has warnings but is functional.${NC}"
        echo "   Address warnings for production release."
        EXIT_CODE=0
    fi
else
    echo -e "${RED}❌ Build verification failed!${NC}"
    echo "   Fix the failed checks before distributing."
    EXIT_CODE=1
fi

echo ""
echo "Verification complete."
echo ""

exit $EXIT_CODE
