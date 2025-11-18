# Changelog

All notable changes to Voice Assistant for macOS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Multi-language support beyond English
- Custom wake word training
- Response streaming for faster feedback
- Screen content understanding
- Plugin system for community-contributed tools
- iOS companion app
- Home Assistant integration

## [1.0.0] - 2024-11-18

### Added
- Initial release of Voice Assistant for macOS
- Wake word detection with "Hey Claude" using Porcupine
- Hotkey activation (Cmd+Shift+Space)
- Speech-to-text using whisper.cpp with Core ML acceleration
- Multiple LLM backend support:
  - Local gpt-oss:120b via MLX
  - OpenAI GPT-4/GPT-4o
  - Anthropic Claude Sonnet/Opus
  - OpenRouter (any model)
- macOS automation tools via MCP server:
  - AppleScript execution
  - Accessibility API control
  - File operations
  - iMessage/SMS sending
  - Web search
  - System information queries
- Native Swift menu bar application
- Preferences window with LLM backend configuration
- Secure API key storage in macOS Keychain
- Conversation context management
- Voice Activity Detection (VAD) with Silero
- Text-to-speech with native macOS voices
- Privacy-first design (local processing by default)
- Comprehensive logging and error handling
- DMG and PKG installers
- Apache 2.0 open source license

### Performance
- Wake word detection: <500ms latency
- STT transcription: <500ms for 5s audio on M3 Ultra
- Local LLM response: <2s on M3 Ultra with gpt-oss:120b
- Cloud LLM response: <5s typical
- Idle CPU usage: <5%
- Idle memory usage: <200MB
- With local LLM: ~75GB RAM usage

### Security
- All voice data processed on-device by default
- API keys stored in macOS Keychain
- No telemetry or usage tracking
- Explicit user permission for all capabilities
- File operations sandboxed to user directories
- Message sending requires confirmation

### Documentation
- Comprehensive README with quick start guide
- Detailed setup documentation
- Usage guide with example commands
- Troubleshooting guide
- Development guide for contributors
- API documentation for tool developers
- Multi-agent development plan (CLAUDE.md)

### Known Issues
- Requires macOS Tahoe 26.1 or later
- Apple Silicon recommended (Intel Macs may have reduced performance)
- Some applications may not fully support Accessibility API
- Messages sending requires Messages app to be running
- Large local models (120b) require significant RAM (64GB+)

### Dependencies
- Python 3.9+
- whisper.cpp with Core ML support
- Porcupine wake word engine (requires API key)
- PyObjC for macOS integration
- FastMCP for tool server
- MLX for local LLM support (optional)
- Poetry for Python dependency management

---

## Version History Format

### [Version] - YYYY-MM-DD

#### Added
- New features

#### Changed
- Changes to existing functionality

#### Deprecated
- Features that will be removed in future versions

#### Removed
- Removed features

#### Fixed
- Bug fixes

#### Security
- Security improvements and fixes

---

## Contributing

When making changes, please:
1. Update this CHANGELOG under the [Unreleased] section
2. Follow the format above
3. Include ticket/PR numbers where applicable
4. Move items to a version section on release

Example:
```markdown
### Added
- Multi-language support for Spanish and French (#123)
```

---

[Unreleased]: https://github.com/yourusername/macos-voice-assistant/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/yourusername/macos-voice-assistant/releases/tag/v1.0.0
