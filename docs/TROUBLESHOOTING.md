# Troubleshooting Guide

Common issues and solutions for Voice Assistant.

## Wake Word Issues

### Wake word not detected

**Possible causes:**
- Microphone permission not granted
- Wake word sensitivity too low
- Background noise interference
- Microphone not working

**Solutions:**
1. Check microphone permission:
   - System Settings → Privacy & Security → Microphone
   - Ensure Voice Assistant is enabled

2. Test microphone:
   - Open Voice Memos app
   - Record and play back audio
   - If Voice Memos doesn't work, hardware issue

3. Adjust sensitivity:
   - Open Preferences → Wake Word
   - Increase sensitivity slider
   - Test with "Hey Claude"

4. Check logs:
   ```bash
   tail -f ~/Library/Logs/VoiceAssistant/audio.log
   ```

### Too many false positives

**Solution:**
- Lower wake word sensitivity in Preferences
- Reduce background noise
- Move microphone away from speakers

## Speech Recognition Issues

### Transcription inaccurate

**Solutions:**
1. Verify whisper.cpp installation:
   ```bash
   ls ~/.voice-assistant/whisper.cpp/build/bin/main
   ```

2. Try larger model:
   - Preferences → Speech Recognition → Model
   - Change from base.en to small.en or medium.en

3. Check for background noise
4. Speak more clearly and slowly

### "Whisper not found" error

**Solution:**
Run setup script:
```bash
./scripts/setup_whisper.sh
```

## LLM Issues

### "Connection refused" (Local LLM)

**Cause:** Local LLM server not running

**Solution:**
```bash
mlx-lm.server --model gpt-oss:120b --port 8080
```

### "Invalid API key" (Cloud providers)

**Solutions:**
1. Verify API key:
   - Open Preferences
   - Re-enter API key
   - Ensure no extra spaces

2. Check API key validity:
   - Visit provider's dashboard
   - Ensure key is active
   - Check account has credits

### "Rate limit exceeded"

**Cause:** Too many API requests

**Solutions:**
- Wait a few minutes
- Upgrade API plan
- Switch to local LLM

### Slow responses

**Local LLM:**
- Normal on first request (model loading)
- Ensure sufficient RAM (64GB+)
- Check Activity Monitor for memory pressure

**Cloud APIs:**
- Check internet connection
- Try different provider
- Check provider status page

## Tool Execution Issues

### "Accessibility permission denied"

**Solution:**
1. System Settings → Privacy & Security → Accessibility
2. Remove Voice Assistant from list
3. Click +, add Voice Assistant again
4. Restart Voice Assistant

### File operations fail

**Solutions:**
1. Check Full Disk Access permission
2. Verify file paths are correct
3. Ensure user has write permissions
4. Check logs for specific error

### Messages not sending

**Known limitation:** macOS requires user confirmation for sending messages programmatically

**Workaround:** Voice Assistant will open Messages with pre-filled message for you to confirm

## Performance Issues

### High CPU usage

**Causes:**
- Wake word detection running
- Large LLM model loaded

**Normal:**
- <5% when idle
- 20-40% during processing

**If excessive:**
- Check Activity Monitor
- Restart Voice Assistant
- Check for background processes

### High memory usage

**Expected:**
- ~200MB without local LLM
- ~75GB with gpt-oss:120b loaded

**If excessive:**
- Restart Voice Assistant
- Use smaller model
- Close other applications

## Installation Issues

### "App is damaged and can't be opened"

**Cause:** Gatekeeper blocking unsigned app

**Solution (temporary, until we sign releases):**
```bash
xattr -cr /Applications/VoiceAssistant.app
```

### Python dependencies fail to install

**Solutions:**
1. Install Xcode Command Line Tools:
   ```bash
   xcode-select --install
   ```

2. Install Homebrew:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

3. Retry installation

## Getting Logs

### Python backend logs:
```bash
tail -f /tmp/voice-assistant/logs/app.log
```

### System logs:
```bash
log show --predicate 'subsystem == "com.voiceassistant"' --last 1h
```

### Export all logs:
```bash
zip -r assistant-logs.zip \
  ~/Library/Logs/VoiceAssistant/ \
  /tmp/voice-assistant/logs/
```

## Still Having Issues?

1. Check [GitHub Issues](https://github.com/yourusername/macos-voice-assistant/issues)
2. Search [GitHub Discussions](https://github.com/yourusername/macos-voice-assistant/discussions)
3. Create new issue with:
   - macOS version
   - Hardware specs
   - Steps to reproduce
   - Relevant logs
   - Screenshots if applicable
