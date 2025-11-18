# Deployment Guide for Voice Assistant

This guide covers building, packaging, and distributing Voice Assistant for macOS.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Build Environment Setup](#build-environment-setup)
3. [Building from Source](#building-from-source)
4. [Creating Installers](#creating-installers)
5. [Code Signing](#code-signing)
6. [Notarization](#notarization)
7. [Distribution](#distribution)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **macOS**: Tahoe 26.1 or later (for building)
- **Xcode**: 15.0 or later with Command Line Tools
- **Python**: 3.9 or later
- **Homebrew**: Package manager for macOS
- **Poetry**: Python dependency management

### Required Tools

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required tools
brew install create-dmg cmake python@3.11

# Install Poetry
pip3 install poetry

# Install Python dependencies
cd python-service
poetry install
```

### Apple Developer Account

For distribution outside the development team:
- **Apple Developer Program** membership ($99/year)
- **Developer ID Application Certificate** (for code signing)
- **Developer ID Installer Certificate** (for PKG signing)
- **App-specific password** (for notarization)

---

## Build Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/macos-voice-assistant.git
cd macos-voice-assistant
```

### 2. Setup Whisper.cpp

```bash
./scripts/setup_whisper.sh
```

This will:
- Clone whisper.cpp repository
- Download and compile Whisper models (base.en, small.en)
- Build with Core ML and Metal acceleration
- Install to `~/.voice-assistant/whisper.cpp`

### 3. Verify Project Structure

```bash
./scripts/verify_build.sh
```

This checks that all required files and dependencies are present.

---

## Building from Source

### Quick Build (Development)

```bash
# Build Swift app
cd swift-app
xcodebuild -scheme VoiceAssistant -configuration Debug

# Run Python service
cd ../python-service
poetry run voice-assistant
```

### Release Build

```bash
# Full release build with optimizations
cd swift-app
xcodebuild \
    -scheme VoiceAssistant \
    -configuration Release \
    -derivedDataPath build \
    CODE_SIGN_IDENTITY="" \
    CODE_SIGNING_REQUIRED=NO
```

The built app will be in: `swift-app/build/Release/VoiceAssistant.app`

---

## Creating Installers

### DMG Installer (Recommended for User Distribution)

The DMG installer provides a drag-and-drop installation experience.

```bash
./scripts/build_dmg.sh
```

**What it does:**
1. Builds the Swift app in Release mode
2. Bundles Python service and dependencies
3. Includes whisper.cpp binaries and models
4. Adds documentation and uninstaller
5. Creates a distributable DMG file
6. Generates SHA256 checksum
7. Creates build manifest

**Output:**
- `dist/VoiceAssistant-1.0.0.dmg` - DMG installer
- `dist/VoiceAssistant-1.0.0.dmg.sha256` - Checksum
- `dist/VoiceAssistant-1.0.0-manifest.txt` - Build manifest
- `dist/build_dmg.log` - Build log

**DMG Contents:**
- VoiceAssistant.app (complete bundle)
- README.txt (installation instructions)
- Applications folder symlink (for drag-install)

### PKG Installer (For Enterprise/MDM Distribution)

The PKG installer supports automated deployment and MDM systems.

```bash
./scripts/build_pkg.sh
```

**What it does:**
1. Builds or uses existing app bundle
2. Creates package structure
3. Adds pre/post-install scripts
4. Creates installer with welcome/license screens
5. Generates signed PKG (if certificates available)

**Output:**
- `dist/VoiceAssistant-1.0.0.pkg` - PKG installer

**PKG Features:**
- Automated installation to /Applications
- Pre-install: Quits running app, removes old version
- Post-install: Creates data directories, installs dependencies
- Welcome, license, and completion screens
- Uninstall support

---

## Code Signing

Code signing is required for distribution outside the Mac App Store.

### Prerequisites

1. Join Apple Developer Program
2. Download certificates from Apple Developer portal
3. Install certificates in Keychain

### Signing the App Bundle

```bash
# Sign the app with hardened runtime
codesign --deep --force --verify --verbose \
    --sign "Developer ID Application: Your Name (TEAM_ID)" \
    --options runtime \
    --entitlements swift-app/VoiceAssistant.entitlements \
    swift-app/build/Release/VoiceAssistant.app

# Verify signing
codesign --verify --verbose=4 \
    swift-app/build/Release/VoiceAssistant.app

# Check signature details
codesign -dv --verbose=4 \
    swift-app/build/Release/VoiceAssistant.app
```

### Signing the DMG

```bash
codesign --sign "Developer ID Application: Your Name (TEAM_ID)" \
    dist/VoiceAssistant-1.0.0.dmg

# Verify
codesign --verify --verbose=4 \
    dist/VoiceAssistant-1.0.0.dmg
```

### Signing the PKG

```bash
productsign --sign "Developer ID Installer: Your Name (TEAM_ID)" \
    dist/VoiceAssistant-1.0.0.pkg \
    dist/VoiceAssistant-1.0.0-signed.pkg

# Verify
pkgutil --check-signature \
    dist/VoiceAssistant-1.0.0-signed.pkg
```

---

## Notarization

Notarization is required for apps distributed outside the App Store to run on macOS 10.15+.

### Setup

1. Create app-specific password at appleid.apple.com
2. Store credentials (one-time setup):

```bash
xcrun notarytool store-credentials "voice-assistant-notary" \
    --apple-id "your@email.com" \
    --team-id "TEAM_ID" \
    --password "app-specific-password"
```

### Notarize DMG

```bash
# Submit for notarization
xcrun notarytool submit dist/VoiceAssistant-1.0.0.dmg \
    --keychain-profile "voice-assistant-notary" \
    --wait

# If successful, staple the ticket
xcrun stapler staple dist/VoiceAssistant-1.0.0.dmg

# Verify stapling
xcrun stapler validate dist/VoiceAssistant-1.0.0.dmg
```

### Notarize PKG

```bash
# Submit for notarization
xcrun notarytool submit dist/VoiceAssistant-1.0.0-signed.pkg \
    --keychain-profile "voice-assistant-notary" \
    --wait

# Staple the ticket
xcrun stapler staple dist/VoiceAssistant-1.0.0-signed.pkg

# Verify
xcrun stapler validate dist/VoiceAssistant-1.0.0-signed.pkg
```

### Check Notarization Status

```bash
# Get submission history
xcrun notarytool history \
    --keychain-profile "voice-assistant-notary"

# Get details for a specific submission
xcrun notarytool info <submission-id> \
    --keychain-profile "voice-assistant-notary"

# Get notarization log
xcrun notarytool log <submission-id> \
    --keychain-profile "voice-assistant-notary"
```

---

## Distribution

### GitHub Releases

1. Create a new release on GitHub
2. Tag with semantic version (e.g., `v1.0.0`)
3. Upload artifacts:
   - DMG file
   - DMG checksum (.sha256)
   - PKG file (if notarized)
   - Build manifest
4. Write release notes from CHANGELOG.md

### Automated Release (GitHub Actions)

The repository includes a GitHub Actions workflow for automated releases:

```yaml
# .github/workflows/release.yml
# Triggers on version tags (v*)
```

To create a release:
```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

### Update Distribution Channels

After creating a release:
1. Update website download links
2. Post announcement on social media
3. Update documentation
4. Notify users via email list
5. Submit to relevant app directories

---

## Troubleshooting

### Build Failures

**Xcode build fails:**
```bash
# Clean build folder
cd swift-app
rm -rf build
xcodebuild clean

# Verify Xcode installation
xcode-select --print-path

# Reset if needed
sudo xcode-select --reset
```

**Python dependencies fail:**
```bash
# Clear Poetry cache
cd python-service
poetry cache clear . --all

# Reinstall
poetry install --no-cache
```

**Whisper.cpp build fails:**
```bash
# Clean and rebuild
cd ~/.voice-assistant/whisper.cpp
rm -rf build
cmake -B build -DWHISPER_COREML=1 -DWHISPER_METAL=1
cmake --build build -j
```

### DMG Creation Fails

**create-dmg not found:**
```bash
brew install create-dmg
```

**DMG verification fails:**
```bash
# Check DMG manually
hdiutil verify dist/VoiceAssistant-1.0.0.dmg

# Try mounting
hdiutil mount dist/VoiceAssistant-1.0.0.dmg
```

### Code Signing Issues

**Certificate not found:**
```bash
# List available signing identities
security find-identity -v -p codesigning

# Import certificate if needed
open DeveloperID.p12
```

**Signing fails with "resource fork, Finder information, or similar detritus not allowed":**
```bash
# Clean extended attributes
xattr -cr swift-app/build/Release/VoiceAssistant.app
```

### Notarization Issues

**Notarization rejected:**
```bash
# Get detailed log
xcrun notarytool log <submission-id> \
    --keychain-profile "voice-assistant-notary" \
    > notarization-log.json

# Common issues:
# 1. Missing hardened runtime
# 2. Incorrect entitlements
# 3. Unsigned nested frameworks
# 4. Invalid bundle structure
```

**Fix hardened runtime issues:**
```bash
# Re-sign with hardened runtime
codesign --deep --force \
    --sign "Developer ID Application: Your Name" \
    --options runtime \
    VoiceAssistant.app
```

### Bundle Issues

**Python packages not found:**
```bash
# Verify bundle contents
ls -la swift-app/build/Release/VoiceAssistant.app/Contents/Resources/

# Check Python path in app
cat swift-app/build/Release/VoiceAssistant.app/Contents/Info.plist
```

**Whisper.cpp not working:**
```bash
# Verify whisper binary
file ~/.voice-assistant/whisper.cpp/build/bin/main

# Test whisper
~/.voice-assistant/whisper.cpp/build/bin/main --help
```

---

## Build Verification Checklist

Before distributing, run through this checklist:

```bash
# 1. Run verification script
./scripts/verify_build.sh

# 2. Test on clean macOS system
# - Install from DMG
# - Launch app
# - Grant permissions
# - Test wake word
# - Test all LLM backends
# - Test automation tools

# 3. Verify code signing
codesign --verify --verbose=4 dist/VoiceAssistant.app
spctl --assess --verbose=4 dist/VoiceAssistant.app

# 4. Verify notarization
xcrun stapler validate dist/VoiceAssistant-1.0.0.dmg

# 5. Check bundle size
du -sh dist/VoiceAssistant-1.0.0.dmg

# 6. Verify checksums
shasum -a 256 -c dist/VoiceAssistant-1.0.0.dmg.sha256
```

---

## Environment Variables

Optional environment variables for build customization:

```bash
# Skip code signing
export CODE_SIGN_IDENTITY=""

# Custom build location
export BUILD_DIR=/path/to/build

# Enable verbose logging
export VERBOSE=1

# Skip dependency bundling (for testing)
export SKIP_DEPENDENCIES=1
```

---

## Continuous Integration

### GitHub Actions

The project includes CI/CD workflows:

**On Push:**
- Build Swift app
- Run Python tests
- Verify project structure

**On Tag:**
- Create release builds
- Sign and notarize
- Upload to GitHub Releases
- Update documentation

### Local CI Testing

```bash
# Install act (GitHub Actions local runner)
brew install act

# Test workflow locally
act -j build
```

---

## Support

For deployment issues:
- Check logs: `dist/build_dmg.log`, `dist/build_pkg.log`
- Review build manifest: `dist/VoiceAssistant-1.0.0-manifest.txt`
- Run verification: `./scripts/verify_build.sh`
- Open issue: [GitHub Issues](https://github.com/yourusername/macos-voice-assistant/issues)

---

## Additional Resources

- [Apple Code Signing Guide](https://developer.apple.com/support/code-signing/)
- [Apple Notarization Guide](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
- [DMG Canvas](https://www.araelium.com/dmgcanvas) - GUI DMG creator
- [Packages](http://s.sudre.free.fr/Software/Packages/about.html) - GUI PKG creator

---

**Last Updated:** 2024-11-18
**Version:** 1.0.0
