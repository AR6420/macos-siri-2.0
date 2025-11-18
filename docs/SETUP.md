# Voice Assistant - Setup Guide

This guide will help you install and configure Voice Assistant on macOS.

## System Requirements

- **macOS**: Tahoe 26.1 (macOS 26.1) or later
- **Hardware**: Apple Silicon Mac (M1, M2, M3, or M4)
- **RAM**: 8GB minimum, 64GB+ recommended for local LLM
- **Storage**: 10GB free space (more for local models)
- **Python**: 3.9 or later

## Installation Methods

### Method 1: DMG Installer (Recommended)

1. Download `VoiceAssistant-X.X.X.dmg` from releases
2. Open the DMG file
3. Drag Voice Assistant to Applications folder
4. Launch from Applications
5. Grant permissions when prompted

### Method 2: PKG Installer

1. Download `VoiceAssistant-X.X.X.pkg` from releases
2. Double-click to run installer
3. Follow installation wizard
4. Launch from Applications

### Method 3: Build from Source

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed build instructions.

## First Launch

### 1. Grant Permissions

Voice Assistant requires several permissions to function:

#### Microphone Access (Required)
- Needed for voice input
- System Settings → Privacy & Security → Microphone
- Enable for Voice Assistant

#### Accessibility Access (Required)
- Needed for system automation
- System Settings → Privacy & Security → Accessibility
- Click +, add Voice Assistant, enable checkbox

#### Input Monitoring (Optional)
- Needed for hotkey support
- System Settings → Privacy & Security → Input Monitoring
- Enable for Voice Assistant

#### Full Disk Access (Optional)
- Needed for full file access and Messages
- System Settings → Privacy & Security → Full Disk Access
- Enable for Voice Assistant

### 2. Configure LLM Backend

Open Preferences from the menu bar icon:

#### Option A: Local (gpt-oss:120b)

**Pros**: Complete privacy, no API costs
**Cons**: Requires powerful Mac, ~75GB RAM

1. Install MLX: `pip install mlx-lm`
2. Start server:
   ```bash
   mlx-lm.server --model gpt-oss:120b --port 8080
   ```
3. Select "Local (gpt-oss:120b)" in Preferences
4. No API key needed

#### Option B: Claude (Anthropic)

**Pros**: Very capable, good at reasoning
**Cons**: Requires API key, costs money

1. Get API key from [console.anthropic.com](https://console.anthropic.com)
2. Select "Anthropic Claude" in Preferences
3. Enter API key (stored securely in Keychain)
4. Choose model (Claude Sonnet 4 recommended)

#### Option C: OpenAI

**Pros**: Well-known, reliable
**Cons**: Requires API key, costs money

1. Get API key from [platform.openai.com](https://platform.openai.com)
2. Select "OpenAI" in Preferences
3. Enter API key
4. Choose model (GPT-4o recommended)

#### Option D: OpenRouter

**Pros**: Access to any model
**Cons**: Requires API key, variable costs

1. Get API key from [openrouter.ai](https://openrouter.ai)
2. Select "OpenRouter" in Preferences
3. Enter API key
4. Choose model from dropdown

### 3. Test Setup

1. Say "Hey Claude, hello" or press Cmd+Shift+Space
2. Speak a simple command
3. Wait for response

If it works - congratulations! If not, see troubleshooting below.

## Configuration

### Configuration File Location

```
~/Library/Application Support/VoiceAssistant/config.yaml
```

### Common Configuration Changes

See full config reference in main `config.yaml` or [CONFIGURATION.md](CONFIGURATION.md)

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## Next Steps

- Read [USAGE.md](USAGE.md) for usage examples
- Join discussions on GitHub
- Report bugs or request features
