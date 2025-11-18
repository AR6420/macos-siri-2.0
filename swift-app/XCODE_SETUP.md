# Xcode Project Setup Guide

This guide explains how to create the Xcode project for Voice Assistant.

## Creating the Project

### Option 1: Create New Xcode Project

1. Open Xcode
2. File → New → Project
3. Select macOS → App
4. Configure:
   - **Product Name**: VoiceAssistant
   - **Team**: Your development team
   - **Organization Identifier**: com.voiceassistant
   - **Bundle Identifier**: com.voiceassistant.macos
   - **Interface**: SwiftUI (we'll use it with AppKit)
   - **Language**: Swift
   - **Include Tests**: Yes

5. Save to the `swift-app` directory

### Option 2: Use Swift Package Manager

The project includes `Package.swift` for SPM support:

```bash
cd swift-app
swift build
```

## Project Configuration

### General Settings

**Target: VoiceAssistant**

- **Display Name**: Voice Assistant
- **Bundle Identifier**: com.voiceassistant.macos
- **Version**: 1.0.0
- **Build**: 1
- **Minimum Deployments**: macOS 14.0

### Signing & Capabilities

1. **Signing**:
   - Automatically manage signing: ✓
   - Team: [Your Team]
   - Signing Certificate: Apple Development / Developer ID

2. **App Sandbox**: OFF
   - Voice Assistant needs system-wide access for automation
   - Sandboxing would prevent Accessibility API usage

3. **Hardened Runtime**: ON (for distribution)
   - Enable: ✓
   - Exceptions:
     - Allow Dyld Environment Variables (for Python)
     - Allow Unsigned Executable Memory (for Python)
     - Disable Library Validation (for Python modules)

4. **Capabilities to Add**:
   - None (permissions handled via Info.plist)

### Build Settings

**Key settings to configure:**

```
PRODUCT_NAME = VoiceAssistant
PRODUCT_BUNDLE_IDENTIFIER = com.voiceassistant.macos
INFOPLIST_FILE = Info.plist
ASSETCATALOG_COMPILER_APPICON_NAME = AppIcon
SWIFT_VERSION = 5.9
MACOSX_DEPLOYMENT_TARGET = 14.0

# For menu bar app
LS_UIELEMENT = YES

# Code signing
CODE_SIGN_STYLE = Automatic
CODE_SIGN_IDENTITY = Apple Development
ENABLE_HARDENED_RUNTIME = YES
```

### Info.plist Configuration

The `Info.plist` file is already configured with:

- [x] LSUIElement = true (no dock icon)
- [x] NSMicrophoneUsageDescription
- [x] NSAppleEventsUsageDescription
- [x] NSInputMonitoringUsageDescription
- [x] NSSystemAdministrationUsageDescription
- [x] Bundle identifier and version

### Build Phases

**1. Compile Sources**

Add all `.swift` files:
- Sources/App/main.swift
- Sources/App/AppDelegate.swift
- Sources/App/MenuBarController.swift
- Sources/App/PreferencesWindow.swift
- Sources/Permissions/PermissionManager.swift
- Sources/IPC/PythonService.swift
- Sources/Models/Configuration.swift

**2. Copy Bundle Resources**

Add:
- Info.plist
- Assets.xcassets

**3. Copy Python Service (Custom)**

Add a "Run Script" build phase:

```bash
# Copy Python service to app bundle
PYTHON_SERVICE_SRC="${PROJECT_DIR}/../python-service"
PYTHON_SERVICE_DEST="${BUILT_PRODUCTS_DIR}/${PRODUCT_NAME}.app/Contents/Resources/python-service"

if [ -d "$PYTHON_SERVICE_SRC" ]; then
    echo "Copying Python service..."
    mkdir -p "$PYTHON_SERVICE_DEST"
    rsync -av --exclude='__pycache__' --exclude='*.pyc' --exclude='.pytest_cache' \
        "$PYTHON_SERVICE_SRC/" "$PYTHON_SERVICE_DEST/"
    echo "Python service copied successfully"
else
    echo "Warning: Python service not found at $PYTHON_SERVICE_SRC"
fi
```

**4. Embed Frameworks**

None needed (using system frameworks only)

## Frameworks & Libraries

**Required Frameworks** (Link Binary with Libraries):

- AppKit.framework (automatically linked)
- Cocoa.framework (automatically linked)
- Foundation.framework (automatically linked)
- Security.framework (for Keychain)
- ApplicationServices.framework (for Accessibility)
- ServiceManagement.framework (for Launch at Login)
- SwiftUI.framework (for UI)
- Combine.framework (for reactive state)

These are all Apple system frameworks - no external dependencies.

## File Organization in Xcode

Organize files in groups matching the directory structure:

```
VoiceAssistant
├── App
│   ├── main.swift
│   ├── AppDelegate.swift
│   ├── MenuBarController.swift
│   └── PreferencesWindow.swift
├── Permissions
│   └── PermissionManager.swift
├── IPC
│   └── PythonService.swift
├── Models
│   └── Configuration.swift
└── Resources
    ├── Assets.xcassets
    └── Info.plist
```

## Schemes

**Scheme: VoiceAssistant**

### Build Configuration

- **Debug**: Development builds with logging
  - Optimization Level: None [-Onone]
  - Debug Information: Yes
  - Assertions: Active

- **Release**: Production builds
  - Optimization Level: Optimize for Speed [-O]
  - Debug Information: No
  - Assertions: Disabled

### Run

- Build Configuration: Debug
- Executable: VoiceAssistant.app
- Launch automatically: Yes
- Environment Variables:
  - `PYTHONUNBUFFERED=1` (for Python output)
  - `DEBUG=1` (for verbose logging)

### Test

- Build Configuration: Debug
- Test Target: VoiceAssistantTests

### Archive

- Build Configuration: Release
- Reveal Archive in Organizer: Yes

## Running from Xcode

1. Select the VoiceAssistant scheme
2. Choose "My Mac" as destination
3. Click Run (⌘R)

The app will:
1. Launch in menu bar (no window)
2. Show menu bar icon
3. Request microphone permission
4. Start Python backend service

## Debugging

### Enable Debug Logging

In Scheme → Run → Arguments:
- Add environment variable: `DEBUG=1`

### View Console Output

Window → Devices and Simulators → Select Mac → Open Console

Or use Console.app and filter for "VoiceAssistant"

### Breakpoints

Set breakpoints in:
- `applicationDidFinishLaunching` to debug startup
- `handlePythonOutput` to debug Python communication
- Permission checking methods

## Testing

### Unit Tests

Create test target:

1. File → New → Target → macOS Unit Testing Bundle
2. Name: VoiceAssistantTests
3. Add test files to Tests/ directory

Example test structure:

```
Tests/
├── AppTests/
│   └── AppDelegateTests.swift
├── PermissionsTests/
│   └── PermissionManagerTests.swift
├── ModelsTests/
│   └── ConfigurationTests.swift
└── Mocks/
    └── MockPythonService.swift
```

### UI Tests

For manual testing:
1. Launch app
2. Check menu bar icon appears
3. Click icon - menu should appear
4. Open Preferences - window should open
5. Check permissions tab
6. Test hotkey (Cmd+Shift+Space)

## Building for Distribution

### Archive

1. Product → Archive
2. Organizer window opens
3. Select archive → Distribute App

### Export Options

**For Testing (Developer ID)**:
- Development
- Export for Mac App Store: No
- Distribution method: Developer ID
- Code signing: Automatic

**For Distribution**:
- Distribution
- Export for Mac App Store: No (we're using direct distribution)
- Notarize: Yes
- Code signing: Developer ID Application

### Notarization

Required for macOS Gatekeeper:

```bash
# Export as .app
# Create DMG or ZIP
zip -r VoiceAssistant.zip VoiceAssistant.app

# Submit for notarization
xcrun notarytool submit VoiceAssistant.zip \
  --apple-id "your@email.com" \
  --team-id "TEAMID" \
  --password "app-specific-password" \
  --wait

# Staple ticket to app
xcrun stapler staple VoiceAssistant.app
```

## Troubleshooting

### "No such module 'Cocoa'"

- Check macOS deployment target is set
- Clean build folder (⇧⌘K)
- Restart Xcode

### App doesn't appear in menu bar

- Verify LSUIElement = true in Info.plist
- Check main.swift sets activation policy to .accessory
- Look for crashes in Console.app

### Python service not starting

- Check Build Phases includes "Copy Python Service" script
- Verify python-service directory exists
- Check Python path in PythonService.swift

### Permission prompts not showing

- Reset PPDB: `tccutil reset All com.voiceassistant.macos`
- Check Info.plist has usage descriptions
- Rebuild app completely

### Code signing issues

- Check certificate is valid in Keychain Access
- Verify team ID is correct
- Try manual signing instead of automatic

## CI/CD with GitHub Actions

See `.github/workflows/build.yml` for automated builds.

The workflow:
1. Checks out code
2. Sets up Xcode
3. Builds the app
4. Runs tests
5. Creates archive
6. Uploads artifacts

## Additional Resources

- [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/macos)
- [App Distribution Guide](https://developer.apple.com/documentation/xcode/distributing-your-app-for-beta-testing-and-releases)
- [Hardened Runtime](https://developer.apple.com/documentation/security/hardened_runtime)
- [Notarization](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
