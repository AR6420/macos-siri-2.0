# Voice Assistant v1.0.0 - Build Guide

**Date:** 2025-11-18
**Target Platform:** macOS Tahoe 26.1+ (Apple Silicon recommended)
**Status:** Production Ready

---

## Quick Build (TL;DR)

```bash
# On macOS M3 Ultra
cd /path/to/macos-siri-2.0

# 1. Verify prerequisites
./scripts/verify_build.sh

# 2. Setup dependencies
cd python-service && poetry install && cd ..

# 3. Build installers
./scripts/build_dmg.sh   # Creates DMG installer
./scripts/build_pkg.sh   # Creates PKG installer

# Outputs in dist/:
# - VoiceAssistant-1.0.0.dmg
# - VoiceAssistant-1.0.0.pkg
```

---

## Prerequisites

### System Requirements
- **macOS:** Tahoe 26.1 (macOS 26.1) or later
- **Hardware:** Apple Silicon (M1/M2/M3)
- **RAM:** 8GB minimum (16GB+ recommended)
- **Disk:** 2GB free space for build

### Development Tools
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required tools
brew install python@3.11
brew install poetry
brew install create-dmg
brew install node  # For DMG icon generation (optional)
```

### Python Dependencies
```bash
cd python-service
poetry install --no-root
```

---

## Build Process

### Step 1: Verify Build Environment

```bash
./scripts/verify_build.sh
```

**This checks:**
- ✓ Project structure is correct
- ✓ All required files exist
- ✓ Scripts are executable
- ✓ Xcode is installed
- ✓ Python environment is ready
- ✓ Swift Package Manager is available

**Expected output:**
```
================================================
Voice Assistant Build Verification
Version: 1.0.0
================================================

✓ All checks passed (45/45)
✓ Project is ready to build!
```

**If verification fails:**
- Check error messages carefully
- Install missing dependencies
- Fix any reported issues
- Run verification again

---

### Step 2: Build DMG Installer

```bash
./scripts/build_dmg.sh
```

**What this does:**
1. **Validates environment** (macOS version, architecture)
2. **Bundles Python backend:**
   - Installs dependencies with Poetry
   - Creates self-contained package
   - Includes whisper.cpp binaries
3. **Builds Swift app:**
   - Compiles VoiceAssistant.app
   - Links with Python backend
   - Embeds resources and icons
4. **Creates DMG:**
   - Professional drag-to-install layout
   - Includes README and documentation
   - Adds uninstaller script
   - Generates SHA256 checksum
5. **Verifies output:**
   - Tests DMG integrity
   - Validates app bundle structure

**Build time:** ~5-10 minutes (first build)

**Output:**
```
dist/
├── VoiceAssistant-1.0.0.dmg        # Main installer
├── VoiceAssistant-1.0.0.dmg.sha256 # Checksum
├── build_dmg.log                   # Build log
└── manifest.txt                    # Build details
```

**DMG Size:** ~200-300 MB (includes Python + whisper.cpp)

---

### Step 3: Build PKG Installer

```bash
./scripts/build_pkg.sh
```

**What this does:**
1. **Creates package structure:**
   - App bundle
   - Python service
   - Configuration files
   - Documentation
2. **Generates installer UI:**
   - Welcome screen
   - License agreement
   - Installation location
   - Progress indicators
3. **Adds scripts:**
   - Pre-installation checks
   - Post-installation setup
   - Permission requests
4. **Signs package** (if certificate available)
5. **Creates installer:**
   - Professional PKG with metadata
   - Suitable for enterprise deployment

**Build time:** ~3-5 minutes

**Output:**
```
dist/
├── VoiceAssistant-1.0.0.pkg        # PKG installer
├── VoiceAssistant-1.0.0.pkg.sha256 # Checksum
└── build_pkg.log                   # Build log
```

**PKG Size:** ~200-300 MB

---

## Build Artifacts

After successful build, you'll have:

```
dist/
├── VoiceAssistant-1.0.0.dmg           # DMG installer (recommended)
├── VoiceAssistant-1.0.0.dmg.sha256    # DMG checksum
├── VoiceAssistant-1.0.0.pkg           # PKG installer (enterprise)
├── VoiceAssistant-1.0.0.pkg.sha256    # PKG checksum
├── build_dmg.log                      # DMG build log
├── build_pkg.log                      # PKG build log
├── manifest.txt                       # Build manifest
└── VoiceAssistant.app/                # Standalone app bundle
    ├── Contents/
    │   ├── MacOS/VoiceAssistant       # Swift binary
    │   └── Resources/
    │       ├── python-service/        # Python backend
    │       ├── python-packages/       # Dependencies
    │       ├── whisper.cpp/           # Binaries & models
    │       ├── config.yaml            # Default config
    │       └── docs/                  # Documentation
    └── Info.plist                     # App metadata
```

---

## Testing the Build

### Test DMG Installation

```bash
# 1. Mount the DMG
open dist/VoiceAssistant-1.0.0.dmg

# 2. Drag to Applications (in Finder)

# 3. Launch
open /Applications/VoiceAssistant.app

# 4. Test features
# - Menu bar icon appears
# - Permissions requested
# - Preferences open
# - Inline AI works (select text)
```

### Test PKG Installation

```bash
# 1. Install (requires admin password)
sudo installer -pkg dist/VoiceAssistant-1.0.0.pkg -target /

# 2. Verify installation
ls /Applications/VoiceAssistant.app

# 3. Launch and test
open /Applications/VoiceAssistant.app
```

### Verify Checksums

```bash
# Verify DMG integrity
shasum -a 256 dist/VoiceAssistant-1.0.0.dmg
cat dist/VoiceAssistant-1.0.0.dmg.sha256

# Verify PKG integrity
shasum -a 256 dist/VoiceAssistant-1.0.0.pkg
cat dist/VoiceAssistant-1.0.0.pkg.sha256
```

---

## Code Signing (Optional but Recommended)

### Get Apple Developer Certificate

1. Join [Apple Developer Program](https://developer.apple.com/programs/) ($99/year)
2. Generate **Developer ID Application** certificate
3. Download and install in Keychain

### Sign the App

```bash
# Sign app bundle
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: Your Name (TEAM_ID)" \
  --options runtime \
  dist/VoiceAssistant.app

# Verify signature
codesign --verify --verbose dist/VoiceAssistant.app
spctl --assess --verbose dist/VoiceAssistant.app
```

### Sign Installers

```bash
# Sign DMG
codesign --sign "Developer ID Application: Your Name (TEAM_ID)" \
  dist/VoiceAssistant-1.0.0.dmg

# Sign PKG
productsign --sign "Developer ID Installer: Your Name (TEAM_ID)" \
  dist/VoiceAssistant-1.0.0.pkg \
  dist/VoiceAssistant-1.0.0-signed.pkg
```

---

## Notarization (Required for macOS 10.15+)

### Submit for Notarization

```bash
# Create app-specific password at appleid.apple.com

# Notarize DMG
xcrun notarytool submit dist/VoiceAssistant-1.0.0.dmg \
  --apple-id "your-email@example.com" \
  --team-id "TEAM_ID" \
  --password "app-specific-password" \
  --wait

# Check status
xcrun notarytool history --apple-id "your-email@example.com" \
  --team-id "TEAM_ID" --password "app-specific-password"
```

### Staple Notarization

```bash
# Staple to DMG
xcrun stapler staple dist/VoiceAssistant-1.0.0.dmg

# Verify
xcrun stapler validate dist/VoiceAssistant-1.0.0.dmg
spctl --assess --type install dist/VoiceAssistant-1.0.0.dmg
```

---

## Distribution

### GitHub Release

```bash
# Create release tag
git tag -a v1.0.0 -m "Voice Assistant v1.0.0 - Initial Release"
git push origin v1.0.0

# Create release on GitHub
gh release create v1.0.0 \
  dist/VoiceAssistant-1.0.0.dmg \
  dist/VoiceAssistant-1.0.0.dmg.sha256 \
  dist/VoiceAssistant-1.0.0.pkg \
  dist/VoiceAssistant-1.0.0.pkg.sha256 \
  --title "Voice Assistant v1.0.0" \
  --notes-file CHANGELOG.md
```

### Direct Distribution

Upload to your website/CDN:
- `VoiceAssistant-1.0.0.dmg` (primary download)
- `VoiceAssistant-1.0.0.dmg.sha256` (for verification)
- `VoiceAssistant-1.0.0.pkg` (alternative download)

---

## Troubleshooting

### Build Fails: "Xcode not found"

```bash
# Install Xcode CLI tools
xcode-select --install

# Set Xcode path
sudo xcode-select --switch /Applications/Xcode.app
```

### Build Fails: "Poetry not found"

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add to PATH
export PATH="$HOME/.local/bin:$PATH"
```

### Build Fails: "create-dmg not found"

```bash
brew install create-dmg
```

### DMG Mount Fails

```bash
# Clean previous builds
rm -rf dist/
mkdir dist/

# Rebuild
./scripts/build_dmg.sh
```

### App Won't Launch: "Damaged or incomplete"

This means the app isn't signed/notarized. Either:
1. **Sign and notarize** (recommended for distribution)
2. **Allow in System Settings** (for testing):
   - System Settings → Privacy & Security
   - Click "Open Anyway" for VoiceAssistant

### Permission Issues

```bash
# Fix script permissions
chmod +x scripts/*.sh

# Fix Python permissions
chmod +x python-service/src/voice_assistant/main.py
```

---

## Build Customization

### Change App Name

Edit `swift-app/Info.plist`:
```xml
<key>CFBundleName</key>
<string>Your Custom Name</string>
```

### Change Version

Edit `VERSION` file:
```
1.0.1
```

Then rebuild.

### Change Bundle ID

Edit `swift-app/Info.plist`:
```xml
<key>CFBundleIdentifier</key>
<string>com.yourcompany.voiceassistant</string>
```

### Customize DMG Background

Place custom background image at:
```
swift-app/Resources/dmg-background.png
```

Size: 800x400 pixels

---

## Performance Optimization

### Reduce Build Size

```bash
# Strip debug symbols
export BUILD_CONFIGURATION=Release

# Minimize Python packages
cd python-service
poetry install --no-dev
```

### Speed Up Builds

```bash
# Use parallel builds
export MAKEFLAGS="-j$(sysctl -n hw.ncpu)"

# Cache dependencies
# Poetry automatically caches
```

---

## CI/CD Integration

### GitHub Actions

See `.github/workflows/release.yml` (local file)

### Manual CI Build

```bash
# Clean build from scratch
rm -rf dist/ build/ python-service/.venv

# Fresh install
cd python-service && poetry install && cd ..

# Build
./scripts/build_dmg.sh
./scripts/build_pkg.sh

# Sign (if certificates available)
# codesign ...

# Upload artifacts
# gh release upload ...
```

---

## Next Steps After Build

1. **Test installation** on clean macOS system
2. **Verify all features** work
3. **Sign and notarize** for public distribution
4. **Create GitHub release** with installers
5. **Update documentation** with download links
6. **Announce release** to target audience
7. **Gather feedback** and iterate

---

## Build Checklist

Before building for release:

- [ ] All tests passing (`pytest python-service/tests/`)
- [ ] Version updated in `VERSION` file
- [ ] CHANGELOG.md updated with release notes
- [ ] README.md accurate and up-to-date
- [ ] API keys removed from config (use env vars)
- [ ] Build scripts tested and working
- [ ] Clean build directory (`rm -rf dist/`)
- [ ] Build on clean macOS install (recommended)
- [ ] Test installation on multiple Macs
- [ ] Code signed with Developer ID
- [ ] Notarized by Apple
- [ ] Checksums generated and verified
- [ ] GitHub release created
- [ ] Documentation deployed

---

## Support

**Build Issues:** Check build logs in `dist/build_*.log`
**Script Issues:** Add `set -x` to scripts for debug output
**GitHub Issues:** https://github.com/AR6420/macos-siri-2.0/issues

---

**Version:** 1.0.0
**Last Updated:** 2025-11-18
**Platform:** macOS Tahoe 26.1+
**Build System:** Shell scripts + Poetry + Xcode

**Ready to build! 🚀**
