# Installation Guide for Voice Assistant

Complete installation guide for end users of Voice Assistant for macOS.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation Methods](#installation-methods)
3. [First-Time Setup](#first-time-setup)
4. [Configuration](#configuration)
5. [Verification](#verification)
6. [Uninstallation](#uninstallation)
7. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements

- **Operating System**: macOS Tahoe 26.1 or later
- **Processor**: Apple Silicon (M1 or later) or Intel x86_64
- **RAM**: 8GB minimum
- **Storage**: 2GB free space (4GB+ recommended with models)
- **Python**: 3.9 or later (will be installed if missing)

### Recommended Configuration

- **Operating System**: macOS Tahoe 26.1
- **Processor**: Apple Silicon M2/M3 or later
- **RAM**: 64GB (for local LLM support)
- **Storage**: 10GB free space
- **Internet**: Required for cloud LLM APIs and initial setup

---

## Installation Methods

### Method 1: DMG Installer (Recommended)

The easiest way to install Voice Assistant.

#### Step 1: Download

Download the latest `.dmg` file from:
- **GitHub Releases**: https://github.com/yourusername/macos-voice-assistant/releases
- Download: `VoiceAssistant-1.0.0.dmg`

#### Step 2: Verify Download (Optional but Recommended)

```bash
# Download checksum file
# Verify integrity
shasum -a 256 -c VoiceAssistant-1.0.0.dmg.sha256
```

#### Step 3: Install

1. **Open the DMG**
   - Double-click `VoiceAssistant-1.0.0.dmg`
   - A new window will open showing the Voice Assistant icon

2. **Drag to Applications**
   - Drag the `Voice Assistant` icon to the `Applications` folder
   - Wait for the copy to complete (may take a minute for large bundle)

3. **Eject the DMG**
   - Right-click the mounted DMG in Finder sidebar
   - Select "Eject"

4. **Launch Voice Assistant**
   - Open Applications folder
   - Double-click `Voice Assistant`
   - If you see a security warning, see [Troubleshooting](#app-from-unidentified-developer)

### Method 2: PKG Installer

For automated deployment or enterprise environments.

#### Step 1: Download PKG

Download `VoiceAssistant-1.0.0.pkg` from GitHub Releases.

#### Step 2: Run Installer

1. **Double-click the PKG file**
2. **Follow the installer wizard**
   - Read the Welcome screen
   - Accept the License Agreement (Apache 2.0)
   - Choose installation location (Applications folder)
   - Click Install
   - Enter your password if prompted
3. **Wait for installation to complete**
4. **Click Close**

#### Automated Installation (MDM/CLI)

```bash
# Silent installation
sudo installer -pkg VoiceAssistant-1.0.0.pkg -target /

# Verify installation
pkgutil --pkgs | grep voiceassistant
```

### Method 3: Build from Source

For developers or advanced users.

See [DEPLOYMENT.md](DEPLOYMENT.md) for build instructions.

---

## First-Time Setup

### Step 1: Launch the Application

1. Open Voice Assistant from Applications folder
2. The menu bar icon will appear (🎙️)
3. You may see a first-launch welcome screen

### Step 2: Grant Permissions

Voice Assistant requires several macOS permissions to function:

#### Microphone Access (Required)

**What it's for:** Voice input and wake word detection

1. When prompted, click "Allow" or "OK"
2. If you miss the prompt:
   - Open System Settings → Privacy & Security → Microphone
   - Find "Voice Assistant" in the list
   - Toggle it ON

**Test:** Say "Hey Claude" - the menu bar icon should change

#### Accessibility (Required)

**What it's for:** Controlling applications and automating tasks

1. Voice Assistant will show instructions
2. Open System Settings → Privacy & Security → Accessibility
3. Click the lock icon and enter your password
4. Click "+" button
5. Navigate to Applications and select Voice Assistant
6. Check the box next to Voice Assistant

**Test:** Ask to "open Safari" - Safari should launch

#### Input Monitoring (Optional)

**What it's for:** Hotkey support (Cmd+Shift+Space)

1. When prompted, click "Allow"
2. Or manually: System Settings → Privacy & Security → Input Monitoring
3. Enable Voice Assistant

**Test:** Press Cmd+Shift+Space - should activate listening

#### Full Disk Access (Optional)

**What it's for:** Reading files in protected directories

Only enable if you need the assistant to access all files.

1. System Settings → Privacy & Security → Full Disk Access
2. Click "+" and add Voice Assistant

### Step 3: Initial Configuration

#### Open Preferences

1. Click the menu bar icon
2. Select "Preferences..."

#### Choose LLM Backend

Voice Assistant supports multiple AI backends:

##### Option A: Local (gpt-oss:120b)

**Pros:** Complete privacy, no API costs, unlimited usage
**Cons:** Requires 64GB+ RAM, separate installation

**Setup:**
1. Install MLX: `brew install mlx`
2. Download model: `mlx-lm.download gpt-oss:120b`
3. Start server: `mlx-lm.server --model gpt-oss:120b --port 8080`
4. In Preferences:
   - Select "Local (gpt-oss)"
   - Verify URL: `http://localhost:8080`
   - Click "Test Connection"

##### Option B: Anthropic Claude

**Pros:** High quality responses, good at reasoning
**Cons:** Requires API key, pay-per-use

**Setup:**
1. Get API key from https://console.anthropic.com
2. In Preferences:
   - Select "Anthropic Claude"
   - Enter API key
   - Choose model (Claude Sonnet 4 recommended)
   - Click "Save"

##### Option C: OpenAI

**Pros:** Fast, widely supported
**Cons:** Requires API key, pay-per-use

**Setup:**
1. Get API key from https://platform.openai.com
2. In Preferences:
   - Select "OpenAI"
   - Enter API key
   - Choose model (GPT-4o recommended)
   - Click "Save"

##### Option D: OpenRouter

**Pros:** Access to many models via single API
**Cons:** Requires API key, pay-per-use

**Setup:**
1. Get API key from https://openrouter.ai
2. In Preferences:
   - Select "OpenRouter"
   - Enter API key
   - Choose model
   - Click "Save"

### Step 4: Test Voice Input

1. **Using Wake Word:**
   - Say "Hey Claude"
   - Wait for beep or icon change
   - Say your command: "What time is it?"
   - Listen for response

2. **Using Hotkey:**
   - Press Cmd+Shift+Space
   - Say your command
   - Release keys (or wait for auto-stop)

3. **Check Transcription:**
   - Preferences → General → Show Transcription
   - Enables notification showing what was heard

---

## Configuration

### Audio Settings

**Preferences → Audio**

- **Wake Word Sensitivity:** 0.0 (less sensitive) to 1.0 (more sensitive)
  - Default: 0.5
  - Increase if wake word not detected
  - Decrease if false positives

- **Input Device:** Choose microphone
  - Default: System default
  - Select specific mic if multiple available

### Voice Settings

**Preferences → Voice**

- **Voice:** Choose macOS voice for responses
  - Default: Samantha
  - Test different voices

- **Speech Rate:** Words per minute
  - Default: 200 WPM
  - Range: 170-300

- **Volume:** Response volume
  - Default: 0.8 (80%)
  - Independent of system volume

### Behavior Settings

**Preferences → Behavior**

- **Launch at Login:** Start Voice Assistant when you log in
- **Show Notifications:** Display what assistant hears/says
- **Confirm Actions:** Ask before executing certain commands
- **Conversation Context:** Remember previous exchanges

### Advanced Settings

**Preferences → Advanced**

- **Log Level:** DEBUG, INFO, WARNING, ERROR
- **Model Selection:** Choose Whisper model size
  - tiny.en: Fastest, least accurate
  - base.en: Fast, good accuracy
  - small.en: Recommended (default)
  - medium.en: Slower, best accuracy

---

## Verification

### Test Basic Functionality

```bash
# 1. Check if app is running
ps aux | grep VoiceAssistant

# 2. Check logs
tail -f ~/Library/Logs/VoiceAssistant/voice-assistant.log

# 3. Test wake word
# Say: "Hey Claude, hello"
# Should respond with greeting

# 4. Test hotkey
# Press Cmd+Shift+Space
# Say: "What's 2 plus 2?"
# Should respond with "4"
```

### Verify Installation

```bash
# Check app location
ls -la /Applications/VoiceAssistant.app

# Check data directory
ls -la ~/Library/Application\ Support/VoiceAssistant/

# Check configuration
cat ~/Library/Application\ Support/VoiceAssistant/config.yaml

# Verify Python backend
/Applications/VoiceAssistant.app/Contents/Resources/python-service/bin/voice-assistant --version
```

### Test Automation Tools

1. **AppleScript Test:**
   - Say: "Hey Claude, open Safari"
   - Safari should launch

2. **File Operations:**
   - Say: "Hey Claude, list files on my desktop"
   - Should list desktop files

3. **Web Search:**
   - Say: "Hey Claude, search for Python tutorials"
   - Should return search results

---

## Uninstallation

### Method 1: Using Built-in Uninstaller

```bash
# Run uninstaller
/Applications/VoiceAssistant.app/Contents/Resources/uninstall.sh
```

Follow the prompts to remove:
- Application
- Configuration files
- Log files
- Cached data
- Keychain items

### Method 2: Manual Uninstallation

1. **Quit Voice Assistant**
   ```bash
   killall VoiceAssistant
   ```

2. **Remove Application**
   ```bash
   rm -rf /Applications/VoiceAssistant.app
   ```

3. **Remove User Data**
   ```bash
   rm -rf ~/Library/Application\ Support/VoiceAssistant
   rm -rf ~/.voice-assistant
   rm -rf /tmp/voice-assistant
   ```

4. **Remove Logs**
   ```bash
   rm -rf ~/Library/Logs/VoiceAssistant
   ```

5. **Remove Preferences**
   ```bash
   rm ~/Library/Preferences/com.voiceassistant.app.plist
   ```

6. **Remove Keychain Items**
   ```bash
   security delete-generic-password -s "VoiceAssistant"
   ```

7. **Remove Launch Agent (if installed)**
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.voiceassistant.app.plist
   rm ~/Library/LaunchAgents/com.voiceassistant.app.plist
   ```

---

## Troubleshooting

### App from Unidentified Developer

**Problem:** macOS blocks the app from opening

**Solution:**
1. Right-click Voice Assistant in Applications
2. Select "Open"
3. Click "Open" in the dialog
4. Or: System Settings → Privacy & Security → scroll down → click "Open Anyway"

### Wake Word Not Detected

**Symptoms:** Saying "Hey Claude" does nothing

**Solutions:**
1. **Check microphone permission**
   - System Settings → Privacy & Security → Microphone
   - Ensure Voice Assistant is enabled

2. **Adjust sensitivity**
   - Preferences → Audio → Wake Word Sensitivity
   - Increase to 0.7 or 0.8

3. **Check microphone**
   - Test mic with another app (QuickTime, Voice Memos)
   - Try different mic if available

4. **Check logs**
   ```bash
   tail -f ~/Library/Logs/VoiceAssistant/audio.log
   ```

### Speech Not Recognized

**Symptoms:** Assistant hears you but transcription is wrong

**Solutions:**
1. **Speak clearly and close to microphone**
2. **Check for background noise**
3. **Try larger Whisper model**
   - Preferences → Advanced → Model: medium.en
4. **Check Whisper installation**
   ```bash
   ls ~/.voice-assistant/whisper.cpp/models/
   ```

### LLM Not Responding

**Symptoms:** Transcription works but no response

**Solutions:**
1. **Check API key** (cloud backends)
   - Preferences → LLM Backend
   - Re-enter API key
   - Click "Test Connection"

2. **Check internet connection** (cloud backends)
   ```bash
   ping api.anthropic.com
   ```

3. **Check local server** (local backend)
   ```bash
   curl http://localhost:8080/health
   ```

4. **Check logs**
   ```bash
   tail -f ~/Library/Logs/VoiceAssistant/llm.log
   ```

### Tools Not Working

**Symptoms:** Commands executed but actions don't happen

**Solutions:**
1. **Check Accessibility permission**
   - System Settings → Privacy & Security → Accessibility
   - Ensure Voice Assistant is checked

2. **Check app compatibility**
   - Not all apps support Accessibility API
   - Try with Safari, Finder, TextEdit first

3. **Check tool logs**
   ```bash
   tail -f ~/Library/Logs/VoiceAssistant/mcp.log
   ```

### High CPU Usage

**Symptoms:** Fan noise, slow system

**Solutions:**
1. **Check if local LLM is running**
   ```bash
   ps aux | grep mlx
   ```

2. **Adjust wake word sensitivity** (lower = less CPU)
3. **Close other applications**
4. **Check Activity Monitor**
   - Look for VoiceAssistant process
   - Check CPU and memory usage

### Installation Failed

**Problem:** DMG won't mount or PKG fails

**Solutions:**
1. **Re-download installer**
   - File may be corrupted
   - Verify checksum

2. **Check disk space**
   ```bash
   df -h
   ```

3. **Check macOS version**
   ```bash
   sw_vers
   ```
   - Requires macOS 26.1+

4. **Try alternate installation method**
   - DMG → PKG or vice versa

---

## Getting Help

### Log Files Location

```
~/Library/Logs/VoiceAssistant/
  ├── voice-assistant.log   # Main log
  ├── audio.log             # Audio pipeline
  ├── stt.log               # Speech recognition
  ├── llm.log               # AI backend
  └── mcp.log               # Automation tools
```

### Diagnostic Information

When requesting support, include:

```bash
# System info
sw_vers
uname -m

# App version
/Applications/VoiceAssistant.app/Contents/Resources/VERSION

# Permissions status
# Screenshot of: System Settings → Privacy & Security

# Recent logs
tail -100 ~/Library/Logs/VoiceAssistant/voice-assistant.log
```

### Support Channels

- **Documentation**: https://github.com/yourusername/macos-voice-assistant/docs
- **Issues**: https://github.com/yourusername/macos-voice-assistant/issues
- **Discussions**: https://github.com/yourusername/macos-voice-assistant/discussions
- **Email**: support@voiceassistant.dev

---

## Next Steps

After successful installation:

1. **Read Usage Guide**: [USAGE.md](docs/USAGE.md)
2. **Try Example Commands**: See docs for ideas
3. **Customize Settings**: Explore all preferences
4. **Join Community**: Share feedback and ideas

---

**Last Updated:** 2024-11-18
**Version:** 1.0.0
