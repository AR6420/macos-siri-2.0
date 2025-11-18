# Contributing to Voice Assistant

Thank you for your interest in contributing to Voice Assistant! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Agent-Based Development](#agent-based-development)

## Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow. Please be respectful and constructive in all interactions.

## Getting Started

### Prerequisites

- macOS Tahoe 26.1 or later
- Xcode 15+ with Command Line Tools
- Python 3.9 or later
- Poetry for Python dependency management
- Git

### Finding Issues to Work On

- Check [open issues](https://github.com/yourusername/macos-voice-assistant/issues)
- Look for issues tagged `good first issue` for beginner-friendly tasks
- Issues tagged `help wanted` are specifically looking for contributors
- Feel free to propose new features via issues before implementing

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/macos-voice-assistant.git
cd macos-voice-assistant

# Add upstream remote
git remote add upstream https://github.com/yourusername/macos-voice-assistant.git
```

### 2. Python Environment Setup

```bash
cd python-service

# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### 3. Whisper.cpp Setup

```bash
# Run the setup script
../scripts/setup_whisper.sh
```

### 4. Swift Project Setup

```bash
cd ../swift-app
open VoiceAssistant.xcodeproj
```

### 5. Configuration

```bash
# Copy example config
cp python-service/config.yaml ~/Library/Application\ Support/VoiceAssistant/config.yaml

# Edit configuration as needed
```

## Project Structure

```
macos-voice-assistant/
├── python-service/          # Python backend (Agents 2-6)
│   ├── src/voice_assistant/
│   │   ├── audio/          # Wake word & audio pipeline (Agent 2)
│   │   ├── stt/            # Speech-to-text (Agent 3)
│   │   ├── llm/            # LLM clients (Agent 4)
│   │   ├── mcp/            # MCP server & tools (Agent 5)
│   │   └── orchestrator.py # Main orchestration (Agent 6)
│   ├── tests/
│   └── config.yaml
├── swift-app/              # Swift menu bar app (Agent 1)
│   ├── Sources/
│   └── Resources/
├── scripts/                # Build and setup scripts (Agent 7)
├── docs/                   # Documentation
└── CLAUDE.md              # Development plan
```

## Development Workflow

### 1. Create a Branch

```bash
# Update main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/bug-description
```

### 2. Make Changes

- Write clean, well-documented code
- Follow the coding standards below
- Add tests for new functionality
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run Python tests
cd python-service
poetry run pytest

# Run specific test file
poetry run pytest tests/test_audio.py

# Run with coverage
poetry run pytest --cov=voice_assistant

# Test Swift app (in Xcode)
# Product → Test (Cmd+U)
```

### 4. Commit Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "Add feature: description of what you added"

# Follow commit message format:
# - Use present tense ("Add feature" not "Added feature")
# - First line should be 50 chars or less
# - Optionally add detailed description after blank line
```

### 5. Push and Create Pull Request

```bash
# Push to your fork
git push origin feature/your-feature-name

# Go to GitHub and create Pull Request
# Fill out the PR template
```

## Coding Standards

### Python Code Style

We follow PEP 8 with some modifications:

```python
# Use Black for formatting (line length 100)
poetry run black .

# Use isort for import sorting
poetry run isort .

# Use Ruff for linting
poetry run ruff check .

# Use MyPy for type checking
poetry run mypy src/
```

**Type Hints**: All functions should have type hints

```python
from typing import List, Optional

def process_audio(samples: np.ndarray, sample_rate: int = 16000) -> TranscriptionResult:
    """Process audio samples and return transcription."""
    pass
```

**Docstrings**: Use Google-style docstrings

```python
def transcribe(audio: AudioInput) -> TranscriptionResult:
    """Transcribe audio to text using Whisper.

    Args:
        audio: Audio input containing samples and metadata

    Returns:
        TranscriptionResult with text and confidence score

    Raises:
        TranscriptionError: If transcription fails
    """
    pass
```

### Swift Code Style

- Follow Swift API Design Guidelines
- Use SwiftLint for consistency
- Prefer value types (structs) over reference types (classes)
- Use meaningful variable names
- Add comments for complex logic

```swift
// MARK: - Audio Pipeline

/// Manages continuous audio monitoring and wake word detection
class AudioPipeline {
    private let bufferSize: Int
    private var isListening: Bool = false

    func startListening(completion: @escaping (Result<AudioData, Error>) -> Void) {
        // Implementation
    }
}
```

### Configuration

- Never commit API keys or secrets
- Use environment variables for sensitive data
- Update config.yaml schema when adding new options
- Document all configuration options

### Logging

Use consistent logging across the project:

```python
from loguru import logger

logger.info("Starting audio pipeline")
logger.debug("Buffer size: {size}", size=buffer_size)
logger.warning("Wake word sensitivity low: {value}", value=sensitivity)
logger.error("Failed to load model: {error}", error=str(e))
```

## Testing

### Test Requirements

- All new features must include tests
- Bug fixes should include regression tests
- Aim for >80% code coverage
- Write both unit tests and integration tests

### Python Testing

```python
# tests/test_audio.py
import pytest
from voice_assistant.audio import AudioPipeline

@pytest.fixture
def audio_pipeline():
    """Create audio pipeline for testing."""
    return AudioPipeline(config=test_config)

def test_wake_word_detection(audio_pipeline):
    """Test wake word detection with sample audio."""
    audio = load_test_audio("hey_claude.wav")
    result = audio_pipeline.detect_wake_word(audio)
    assert result.detected is True
    assert result.confidence > 0.8

@pytest.mark.asyncio
async def test_full_pipeline():
    """Integration test for full audio pipeline."""
    # Test implementation
```

### Swift Testing

```swift
import XCTest
@testable import VoiceAssistant

class PermissionManagerTests: XCTestCase {
    func testMicrophonePermissionCheck() {
        let manager = PermissionManager()
        let status = manager.checkMicrophonePermission()
        XCTAssertNotNil(status)
    }
}
```

### Manual Testing

Before submitting PR:
- [ ] Test on clean macOS installation
- [ ] Verify all permissions work correctly
- [ ] Test with multiple LLM backends
- [ ] Test wake word detection in various environments
- [ ] Verify resource usage is acceptable

## Submitting Changes

### Pull Request Guidelines

1. **Fill out the PR template completely**
   - Describe what the PR does
   - Link to related issues
   - List testing performed
   - Note any breaking changes

2. **Keep PRs focused**
   - One feature/fix per PR
   - Avoid mixing refactoring with features
   - Split large changes into multiple PRs

3. **Ensure CI passes**
   - All tests must pass
   - No linting errors
   - Coverage should not decrease

4. **Request review**
   - Tag relevant maintainers
   - Respond to review comments promptly
   - Make requested changes or explain why not

5. **Keep PR updated**
   - Rebase on main if conflicts arise
   - Keep commit history clean

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Example**:
```
feat(llm): add support for OpenRouter API

Implement OpenRouter provider to allow access to any LLM through
a unified API. Includes retry logic and streaming support.

Closes #123
```

## Agent-Based Development

This project uses a multi-agent development approach. See [CLAUDE.md](CLAUDE.md) for details.

### Agent Responsibilities

If you're working on a specific subsystem, consult the agent documentation:

- **Agent 1**: Swift Menu Bar App → [CLAUDE.md#agent-1](CLAUDE.md#agent-1-swift-menu-bar-application)
- **Agent 2**: Audio Pipeline → [CLAUDE.md#agent-2](CLAUDE.md#agent-2-audio-pipeline--wake-word-detection)
- **Agent 3**: Speech-to-Text → [CLAUDE.md#agent-3](CLAUDE.md#agent-3-speech-to-text-whisper-integration)
- **Agent 4**: LLM Client → [CLAUDE.md#agent-4](CLAUDE.md#agent-4-llm-client-flexible-multi-provider)
- **Agent 5**: MCP Server → [CLAUDE.md#agent-5](CLAUDE.md#agent-5-mcp-server--macos-automation-tools)
- **Agent 6**: Orchestration → [CLAUDE.md#agent-6](CLAUDE.md#agent-6-ai-orchestration--response-pipeline)
- **Agent 7**: Configuration → [CLAUDE.md#agent-7](CLAUDE.md#agent-7-configuration-packaging--distribution)

### Interface Contracts

When making changes to interfaces between subsystems:
1. Check the interface contract in CLAUDE.md
2. Discuss breaking changes in an issue first
3. Update all affected components
4. Add migration guide if needed

## Getting Help

- **Questions**: Open a [Discussion](https://github.com/yourusername/macos-voice-assistant/discussions)
- **Bugs**: Open an [Issue](https://github.com/yourusername/macos-voice-assistant/issues)
- **Security**: Email security@voiceassistant.dev (do not open public issue)

## Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes for their contributions
- CONTRIBUTORS.md file

Thank you for contributing to Voice Assistant!
