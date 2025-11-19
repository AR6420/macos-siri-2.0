# Voice Assistant for macOS

> An intelligent, privacy-first voice assistant for macOS Tahoe 26.1 that combines local AI processing with flexible cloud API support.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![macOS](https://img.shields.io/badge/macOS-Tahoe%2026.1-brightgreen.svg)]()
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)]()
[![Swift](https://img.shields.io/badge/Swift-5.9%2B-orange.svg)]()

## Features

- **Privacy-First**: All voice processing happens on-device by default
- **Wake Word Activation**: Say "Hey Claude" or use hotkey (Cmd+Shift+Space)
- **Claude Haiku 4.5**: Fast, affordable AI (default) with optional local/cloud alternatives
- **Inline AI Assistant**: Select text anywhere → Rewrite, proofread, summarize, format
- **10 AI Operations**: Proofread, rewrite (3 tones), summarize, key points, list, table, compose
- **macOS Automation**: Control applications, manage files, send messages, search the web
- **Fast & Accurate**: Whisper.cpp with Core ML acceleration for speech recognition
- **Native Integration**: Beautiful menu bar app with native macOS UI
- **Cross-App Support**: Works in Mail, Messages, TextEdit, Safari, and 15+ apps

## Demo

[Screenshot placeholder - menu bar icon and preferences window]

## ⚡ Quick Start

**Get started in 3 commands:**

```bash
# 1. Clone the repository
git clone https://github.com/AR6420/macos-siri-2.0.git
cd macos-siri-2.0

# 2. Run the installer (installs everything)
./install.sh

# 3. Set your API key and run
export ANTHROPIC_API_KEY="your-key-here"
./run.sh
```

**That's it!** See [QUICKSTART.md](QUICKSTART.md) for detailed quick start guide.

## Installation

### Quick Install (Recommended)

1. Download the latest `.dmg` from [Releases](https://github.com/yourusername/macos-voice-assistant/releases)
2. Open the DMG and drag Voice Assistant to Applications
3. Launch Voice Assistant from Applications folder
4. Grant required permissions when prompted
5. Configure your LLM backend in Preferences
6. Say "Hey Claude" to start using!

### Build from Source

See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed build instructions.

## Requirements

- **macOS**: Tahoe 26.1 (macOS 26.1) or later
- **Hardware**: Apple Silicon Mac (M1 or later recommended)
- **RAM**: 8GB minimum, 64GB+ recommended for local LLM
- **Python**: 3.10 or later
- **Xcode**: Command Line Tools (for building from source)

## Quick Start

### 1. First Launch

When you first launch Voice Assistant, you'll be prompted to grant permissions:

- **Microphone**: Required for voice input
- **Accessibility**: Required for system automation
- **Input Monitoring**: Required for hotkey support

### 2. Configure LLM Backend

Open Preferences from the menu bar icon and choose your backend:

#### Option A: Claude Haiku 4.5 (Default - Recommended ⭐)
- **Get API key** from [console.anthropic.com](https://console.anthropic.com)
- **Enter key** in Preferences → AI Backend → Anthropic
- **Model**: Claude Haiku 4.5 (pre-selected)
- **Best for**: General use, inline AI, all features
- **Performance**: Fast (0.8-1.5s), Affordable ($0.0003/operation)
- **Why recommended**: Excellent quality-to-cost ratio, perfect for text operations

See [CLAUDE_API_SETUP.md](docs/CLAUDE_API_SETUP.md) for detailed setup instructions.

#### Option B: Local (gpt-oss:120b)
- Download and install [MLX](https://github.com/ml-explore/mlx)
- Start local server: `mlx-lm.server --model gpt-oss:120b --port 8080`
- No API key required
- Best for maximum privacy (but slower, requires powerful Mac)

#### Option C: OpenAI
- Get API key from [platform.openai.com](https://platform.openai.com)
- Enter key in Preferences → AI Backend → OpenAI
- Select model: GPT-4o
- Good alternative to Claude

#### Option D: OpenRouter
- Get API key from [openrouter.ai](https://openrouter.ai)
- Access 100+ models through unified API
- Best for experimentation

### 3. Start Using

**Wake Word**: Say "Hey Claude" followed by your command

**Hotkey**: Press Cmd+Shift+Space, then speak

**Example Commands**:
- "Hey Claude, what's the weather today?"
- "Hey Claude, open Safari and search for Python tutorials"
- "Hey Claude, create a new file called todo.txt on my desktop"
- "Hey Claude, send a message to John saying I'll be late"

## Configuration

The main configuration file is located at:
```
~/Library/Application Support/VoiceAssistant/config.yaml
```

See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for detailed configuration options.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Swift Menu Bar App                        │
│  (User Interface, Permissions Management, Status Indicator)  │
└──────────────────────┬──────────────────────────────────────┘
                       │ XPC Communication
┌──────────────────────▼──────────────────────────────────────┐
│                  Python Backend Service                       │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Wake Word    │  │  Whisper     │  │  LLM Client  │     │
│  │ Detection    │→ │  Speech-to-  │→ │  (Flexible)  │     │
│  │ (Porcupine)  │  │  Text        │  │              │     │
│  └──────────────┘  └──────────────┘  └──────┬───────┘     │
│                                              │              │
│  ┌──────────────────────────────────────────▼───────────┐  │
│  │           MCP Server (FastMCP 2.0)                   │  │
│  │  - execute_applescript                               │  │
│  │  - control_application                               │  │
│  │  - file_operations                                   │  │
│  │  - send_message                                      │  │
│  │  - web_search                                        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Available Tools

The assistant has access to these macOS automation tools:

- **execute_applescript**: Run AppleScript to control applications
- **control_application**: Use Accessibility API for UI automation
- **file_operation**: Read, write, list, move, copy files
- **send_message**: Send iMessages or SMS
- **web_search**: Search the web and get results
- **get_system_info**: Query system status and information

## Performance

Typical latency on Mac Studio M3 Ultra:

| Operation | Latency |
|-----------|---------|
| Wake word detection | <500ms |
| Speech-to-text (5s audio) | <500ms |
| LLM response (local) | <2s |
| LLM response (cloud) | <5s |
| Total end-to-end | <5s |

Resource usage:
- Idle CPU: <5%
- Idle RAM: <200MB
- With local LLM: ~75GB RAM

## Privacy & Security

- **Local Processing**: All voice data processed on-device by default
- **No Telemetry**: No usage data sent anywhere
- **Secure Storage**: API keys stored in macOS Keychain
- **User Control**: Explicit permissions for every capability
- **Open Source**: Fully auditable code

## Documentation

- [Setup Guide](docs/SETUP.md) - Detailed installation and setup
- [Usage Guide](docs/USAGE.md) - How to use the voice assistant
- [Configuration](docs/CONFIGURATION.md) - Configuration options
- [Development](docs/DEVELOPMENT.md) - Build from source and contribute
- [API Documentation](docs/API.md) - API reference for developers

## Troubleshooting

### Wake word not detected
- Check microphone permissions in System Settings → Privacy & Security
- Adjust wake word sensitivity in Preferences
- Test microphone with another app to verify it's working

### Speech recognition not working
- Verify whisper.cpp is installed: `ls ~/.voice-assistant/whisper.cpp`
- Run setup script: `./scripts/setup_whisper.sh`
- Check logs: `~/Library/Logs/VoiceAssistant/`

### LLM not responding
- Verify API key is correct in Preferences
- Check network connection for cloud APIs
- For local: Verify MLX server is running on port 8080
- Check logs for error messages

### Tools not working
- Verify Accessibility permission is granted
- Check System Settings → Privacy & Security → Accessibility
- Some apps may not support Accessibility API

For more help, see [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) or [open an issue](https://github.com/yourusername/macos-voice-assistant/issues).

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone repository
git clone https://github.com/yourusername/macos-voice-assistant.git
cd macos-voice-assistant

# Setup Python environment
cd python-service
poetry install

# Setup whisper.cpp
../scripts/setup_whisper.sh

# Open Swift project
open swift-app/VoiceAssistant.xcodeproj
```

## Roadmap

- [ ] Multi-language support
- [ ] Custom wake words
- [ ] Response streaming
- [ ] Screen content understanding
- [ ] Plugin system for community tools
- [ ] iOS companion app
- [ ] Home Assistant integration
- [ ] Calendar and email automation

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [whisper.cpp](https://github.com/ggerganov/whisper.cpp) - Fast speech recognition
- [MLX](https://github.com/ml-explore/mlx) - Apple Silicon ML framework
- [Porcupine](https://picovoice.ai/platform/porcupine/) - Wake word detection
- [FastMCP](https://github.com/jlowin/fastmcp) - MCP server framework
- [Claude](https://www.anthropic.com/claude) - AI assistant inspiration

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/macos-voice-assistant/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/macos-voice-assistant/discussions)
- **Email**: support@voiceassistant.dev

## Star History

If you find this project useful, please consider giving it a star!

---

Made with ❤️ for the macOS community
