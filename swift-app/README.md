# Voice Assistant - Swift Menu Bar Application

This is the native macOS Swift application for Voice Assistant, providing the user interface and system integration.

## Architecture

```
┌─────────────────────────────────────┐
│     Swift Menu Bar Application      │
│                                     │
│  ┌──────────┐    ┌──────────────┐  │
│  │  Menu    │    │  Preferences │  │
│  │  Bar UI  │    │   Window     │  │
│  └────┬─────┘    └──────┬───────┘  │
│       │                 │           │
│  ┌────▼─────────────────▼───────┐  │
│  │   Permission Manager         │  │
│  └──────────────────────────────┘  │
│                │                    │
│  ┌─────────────▼────────────────┐  │
│  │   Python Service (XPC)       │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
           │
           ▼
    Python Backend
```

## Directory Structure

```
swift-app/
├── Sources/
│   ├── App/
│   │   ├── main.swift              # Entry point
│   │   ├── AppDelegate.swift       # App lifecycle
│   │   ├── MenuBarController.swift # Menu bar management
│   │   └── PreferencesWindow.swift # Settings UI
│   ├── Permissions/
│   │   └── PermissionManager.swift # Permission handling
│   ├── IPC/
│   │   └── PythonService.swift     # Python backend communication
│   └── Models/
│       └── Configuration.swift     # Settings and Keychain
├── Resources/
│   └── Assets.xcassets/            # App icons
├── Info.plist                      # App metadata and permissions
├── Package.swift                   # Swift Package Manager
└── README.md                       # This file
```

## Building the App

### Prerequisites

- macOS 14.0 or later
- Xcode 15.0 or later
- Swift 5.9 or later

### Build with Xcode

1. Open the project in Xcode:
   ```bash
   open VoiceAssistant.xcodeproj
   ```

2. Select the "VoiceAssistant" scheme

3. Build and run (⌘R)

### Build with Swift Package Manager

```bash
swift build -c release
```

The executable will be at:
```
.build/release/VoiceAssistant
```

## Permissions Required

The app requests the following macOS permissions:

### Required Permissions

1. **Microphone** (Required)
   - For wake word detection and voice commands
   - Requested automatically on first launch

2. **Accessibility** (Required)
   - For application automation and control
   - Must be granted manually in System Settings

### Optional Permissions

3. **Input Monitoring** (Optional)
   - For hotkey detection (Cmd+Shift+Space)
   - Must be granted manually in System Settings

4. **Full Disk Access** (Optional)
   - For sending messages via Messages app
   - Must be granted manually in System Settings

## Features

### Menu Bar Icon

The menu bar icon changes based on assistant status:

- **Gray mic** (○): Idle - ready to listen
- **Blue waveform** (～): Listening - processing voice input
- **Orange hourglass** (⧗): Processing - generating response
- **Red warning** (⚠): Error state

### Preferences Window

Access via menu bar → Preferences:

#### General Tab
- Launch at login toggle
- Wake word enable/disable
- Hotkey display

#### AI Backend Tab
- Backend selection (Local/OpenAI/Anthropic/OpenRouter)
- API key management (stored in Keychain)
- Model configuration

#### Permissions Tab
- Permission status overview
- Quick access to System Settings
- Permission request buttons

#### Advanced Tab
- Wake word sensitivity slider
- Max conversation turns
- Logging enable/disable

### Keyboard Shortcuts

- **⌘⇧Space**: Activate voice assistant (hotkey)
- **⌘,**: Open preferences
- **⌘Q**: Quit application

## Communication with Python Backend

The Swift app communicates with the Python backend service via standard input/output (STDIN/STDOUT) using JSON messages.

### Message Protocol

#### Swift → Python (Commands)

```json
{
  "command": "start_listening"
}
```

```json
{
  "command": "update_config",
  "config": { ... }
}
```

#### Python → Swift (Events)

```json
{
  "type": "status",
  "status": "listening"
}
```

```json
{
  "type": "wake_word"
}
```

```json
{
  "type": "transcription",
  "text": "What's the weather like?"
}
```

```json
{
  "type": "response",
  "text": "Let me check the weather for you."
}
```

```json
{
  "type": "error",
  "message": "Failed to connect to LLM backend"
}
```

### Status Flow

```
Idle → Listening → Processing → Idle
  ↓        ↓          ↓
Error ←────┴──────────┘
```

## Configuration Management

Settings are stored in:
- **UserDefaults**: UI preferences, backend selection
- **macOS Keychain**: API keys (secure storage)
- **YAML Export**: Generated for Python backend

### Configuration Export

The Swift app exports configuration to YAML format for the Python backend:

```yaml
llm:
  backend: local_gpt_oss
  local_gpt_oss:
    base_url: http://localhost:8080
    temperature: 0.7
audio:
  wake_word:
    enabled: true
    sensitivity: 0.5
```

Config location:
```
~/Library/Application Support/VoiceAssistant/config.yaml
```

## Security

### API Key Storage

All API keys are stored securely in macOS Keychain:

```swift
KeychainManager.save(key: "OPENAI_API_KEY", value: apiKey)
let apiKey = KeychainManager.retrieve(key: "OPENAI_API_KEY")
```

### Privacy

- No cloud communication without explicit user consent
- Wake word processing happens locally
- Speech-to-text runs on-device (whisper.cpp)
- User chooses LLM backend (local vs cloud)

## Development

### Code Organization

- **MARK** comments for section organization
- Swift naming conventions
- ObservableObject for reactive UI
- Combine framework for state management

### Testing

Unit tests location:
```
Tests/VoiceAssistantTests/
```

Run tests:
```bash
swift test
```

### Debugging

Enable verbose logging:
1. Open Preferences
2. Advanced tab
3. Enable "Enable Logging"

Logs location:
```
/tmp/voice-assistant/logs/
```

## Distribution

### Creating .app Bundle

The app bundle should include:
```
VoiceAssistant.app/
├── Contents/
│   ├── MacOS/
│   │   └── VoiceAssistant       # Executable
│   ├── Resources/
│   │   ├── Assets.car           # Compiled assets
│   │   └── python-service/      # Python backend
│   └── Info.plist
```

### Code Signing

Sign the app with Apple Developer certificate:

```bash
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: Your Name" \
  VoiceAssistant.app
```

### Notarization

Required for macOS Gatekeeper:

```bash
xcrun notarytool submit VoiceAssistant.zip \
  --apple-id your@email.com \
  --team-id TEAMID \
  --password app-specific-password
```

## Troubleshooting

### App doesn't appear in menu bar

- Check Console.app for errors
- Ensure LSUIElement is set to true in Info.plist
- Verify app activation policy is set to .accessory

### Python service not starting

- Check Python executable path in PythonService.swift
- Verify python-service directory exists
- Check stderr output in Console.app

### Permissions not working

- Open System Settings → Privacy & Security
- Manually verify each permission
- Restart app after granting permissions

### Hotkey not working

- Ensure Input Monitoring permission granted
- Check for conflicts with other apps
- Try disabling and re-enabling in Preferences

## License

Apache 2.0 - See LICENSE file

## Contributing

See CONTRIBUTING.md for development guidelines.
