# Quick Start Guide - Voice Assistant

Get up and running in **5 minutes**! 🚀

---

## 📋 Requirements

- macOS Tahoe 26.1+ (or macOS Sequoia 15.0+)
- Apple Silicon Mac (M1/M2/M3) recommended
- Claude API key ([get free trial](https://console.anthropic.com/))

---

## ⚡ Quick Install

**Just run this one command:**

```bash
./install.sh
```

That's it! The installer will:
- ✅ Install all dependencies (Homebrew, Python, etc.)
- ✅ Download and build Whisper.cpp
- ✅ Install Python packages
- ✅ Build the macOS app

**Time:** ~10-15 minutes on first run

---

## 🔑 Configure API Key

Before using the app, set your Claude API key:

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

**Get your key:** https://console.anthropic.com/

**Optional:** Make it permanent:
```bash
echo 'export ANTHROPIC_API_KEY="your-key-here"' >> ~/.zshrc
source ~/.zshrc
```

---

## 🚀 Start the App

```bash
./run.sh
```

The app will:
- ✅ Start in the background
- ✅ Show an icon in the menu bar
- ✅ Request permissions (grant them!)

---

## 🎤 Try It Out

### Voice Commands

**Activate:**
- Say **"Hey Claude"** (wake word), OR
- Press **Cmd+Shift+Space** (hotkey)

**Try these commands:**
- "What time is it?"
- "Open Safari"
- "Search the web for Mac tutorials"
- "What's the weather today?"

### Inline AI

**Use in any app:**
1. **Select text** (in Mail, TextEdit, Safari, etc.)
2. **Click orange button** that appears
3. **Choose an operation:**
   - Proofread - Fix grammar/spelling
   - Rewrite - Improve text
   - Friendly/Professional/Concise - Change tone
   - Summary - Summarize content
   - Key Points - Extract bullet points
   - List/Table - Format as list or table
   - Compose - Generate new content

**Works in:** Mail, Messages, Safari, TextEdit, VS Code, Slack, Notion, and more!

---

## 🛑 Stop the App

```bash
# Stop background service
pkill -f voice-assistant

# Then quit from menu bar:
Click menu bar icon → Quit
```

---

## 🔧 Common Issues

### "Permission Denied"

Make scripts executable:
```bash
chmod +x install.sh run.sh
```

### "API Key Not Set"

Export your key:
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

Or set it in app Preferences (menu bar → Preferences).

### "Microphone Not Working"

Grant permission:
- System Settings → Privacy & Security → Microphone
- Enable for "VoiceAssistant"

### "Inline AI Button Not Appearing"

Grant Accessibility permission:
- System Settings → Privacy & Security → Accessibility
- Enable for "VoiceAssistant"

### "Build Failed"

Make sure Xcode Command Line Tools are installed:
```bash
xcode-select --install
```

Then re-run:
```bash
./install.sh
```

---

## 📊 View Logs

**App logs:**
```bash
tail -f /tmp/voice-assistant.log
```

**Python service logs:**
```bash
tail -f /tmp/voice-assistant/logs/app.log
```

---

## 💰 Cost

With Claude Haiku 4.5 (default):
- **Typical usage:** $1-5/month
- **Per inline operation:** ~$0.0003 (less than 1/100th of a cent)
- **Per voice command:** ~$0.0016

Much cheaper than:
- ChatGPT Plus: $20/month
- Grammarly Premium: $12/month
- Notion AI: $10/month

---

## 📚 Learn More

**Core Documentation:**
- **Full README:** `cat README.md`
- **Inline AI Guide:** `cat INLINE_AI_FEATURE.md`
- **Troubleshooting:** `cat docs/TROUBLESHOOTING.md`
- **API Setup:** `cat docs/CLAUDE_API_SETUP.md`

**Build Documentation:**
- **Build Guide:** `cat BUILD_GUIDE.md`
- **Deployment:** `cat DEPLOYMENT.md`
- **Project Summary:** `cat FINAL_PROJECT_SUMMARY.md`

---

## 🎯 Quick Commands Cheat Sheet

```bash
# Install everything
./install.sh

# Set API key (replace with yours)
export ANTHROPIC_API_KEY="sk-ant-..."

# Run the app
./run.sh

# View logs
tail -f /tmp/voice-assistant.log

# Stop the app
pkill -f voice-assistant

# Rebuild the app
cd swift-app
xcodebuild -scheme VoiceAssistant -configuration Release \
  -destination "platform=macOS,arch=arm64" -derivedDataPath build
cd ..

# Reinstall Python dependencies
cd python-service && poetry install && cd ..

# Create DMG installer (for distribution)
./scripts/build_dmg.sh

# Create PKG installer (for enterprise)
./scripts/build_pkg.sh
```

---

## 🎨 Customize

**Change LLM provider:**
Edit `python-service/config.yaml`:
```yaml
llm:
  backend: anthropic_claude  # or openai_gpt4, local_gpt_oss, openrouter
```

**Adjust wake word sensitivity:**
Edit `python-service/config.yaml`:
```yaml
audio:
  wake_word:
    sensitivity: 0.5  # 0.0-1.0 (higher = more sensitive)
```

**Change Whisper model:**
Edit `python-service/config.yaml`:
```yaml
stt:
  model: small.en  # or base.en, medium.en
```

---

## 🆘 Get Help

**Having issues?**

1. Check **Troubleshooting:** `cat docs/TROUBLESHOOTING.md`
2. View logs: `tail -f /tmp/voice-assistant.log`
3. Check GitHub Issues: https://github.com/AR6420/macos-siri-2.0/issues
4. Start a Discussion: https://github.com/AR6420/macos-siri-2.0/discussions

---

## ✨ Tips & Tricks

1. **Use hotkey for quick access:** Cmd+Shift+Space is faster than wake word
2. **Customize in Preferences:** Menu bar icon → Preferences
3. **Check menu bar icon:** Shows status (idle/listening/processing)
4. **Use inline AI everywhere:** Works in 15+ apps!
5. **Preview before accepting:** Inline AI shows preview before replacing text
6. **Undo mistakes:** Cmd+Z works in most apps after replacement

---

## 🚀 Next Steps

After setup:
1. ✅ Try voice commands
2. ✅ Test inline AI in different apps
3. ✅ Customize settings in Preferences
4. ✅ Set up launch at login (Preferences → General)
5. ✅ Explore all 10 inline AI operations

---

**Enjoy your AI-powered voice assistant!** 🎉

For the full guide, see [README.md](README.md)
