# Claude API Setup Guide

The Voice Assistant now uses **Claude Haiku 4.5** as the default LLM for optimal performance, cost-effectiveness, and wider audience reach.

## Why Claude Haiku 4.5?

- **Fast**: Sub-second responses for most operations
- **Affordable**: ~80% cheaper than Claude Sonnet while maintaining quality
- **Accurate**: Excellent for text rewriting, proofreading, and formatting
- **Reliable**: High uptime and consistent performance
- **API-friendly**: Simple REST API, easy to integrate

## Setting Up Your API Key

### Option 1: macOS Keychain (Recommended for End Users)

**For users with the installed .app:**

1. Launch **Voice Assistant** from Applications
2. Click the menu bar icon → **Preferences**
3. Go to the **AI Backend** tab
4. Select **"Anthropic Claude"** from the dropdown
5. Click **"Enter API Key"**
6. Paste your Anthropic API key
7. Click **"Save"**

The key is securely stored in macOS Keychain and never written to disk in plaintext.

---

### Option 2: Environment Variable (Recommended for Developers)

**For developers running from source:**

```bash
# Add to your shell profile (~/.zshrc or ~/.bash_profile)
export ANTHROPIC_API_KEY="your-anthropic-api-key-here"

# Or set for current session only
export ANTHROPIC_API_KEY="your-anthropic-api-key-here"
source ~/.zshrc  # or restart terminal

# Verify it's set
echo $ANTHROPIC_API_KEY
```

Then run the Voice Assistant:
```bash
cd /home/user/macos-siri-2.0/python-service
poetry run python -m voice_assistant.main
```

---

### Option 3: Configuration File (NOT RECOMMENDED)

**⚠️ Security Warning:** Only use this for local testing, never commit API keys to git!

Edit `python-service/config.yaml`:
```yaml
llm:
  anthropic:
    api_key: "your-key-here"  # NOT RECOMMENDED - use api_key_env instead
```

**Better approach:**
```yaml
llm:
  anthropic:
    api_key_env: ANTHROPIC_API_KEY  # Reads from environment variable
```

---

## Getting an Anthropic API Key

### For Individual Users

1. Go to [console.anthropic.com](https://console.anthropic.com/)
2. Sign up or log in
3. Go to **API Keys** section
4. Click **"Create Key"**
5. Copy your key (starts with `sk-ant-...`)
6. Store it securely

### For Developers with Claude Code OAuth

If you're using Claude Code OAuth Long-Lived Token:
- This is a valid Anthropic API key
- Format: `sk-ant-oat01-...`
- Can be used directly with the Voice Assistant
- Same setup process as above

---

## Switching Between LLM Providers

The Voice Assistant supports **4 LLM backends** for maximum flexibility:

### 1. **Anthropic Claude** (Default)
- **Models**: Haiku 4.5, Sonnet 4, Opus 4
- **Best for**: General use, inline AI, all features
- **Cost**: $ (Haiku), $$ (Sonnet), $$$ (Opus)
- **Speed**: Fast (Haiku), Medium (Sonnet), Slower (Opus)

### 2. **OpenAI GPT**
- **Models**: GPT-4o, GPT-4, GPT-3.5
- **Best for**: Alternative to Claude
- **Setup**: Set `OPENAI_API_KEY` environment variable
- **Config**: Change `backend: openai_gpt4`

### 3. **Local gpt-oss:120b**
- **Models**: Local LLM via MLX
- **Best for**: Privacy-focused users, no API costs
- **Requirements**: Mac with Apple Silicon, 64GB+ RAM
- **Setup**: See [LOCAL_LLM_SETUP.md](LOCAL_LLM_SETUP.md)
- **Config**: Change `backend: local_gpt_oss`

### 4. **OpenRouter**
- **Models**: Access to 100+ models via one API
- **Best for**: Model experimentation, flexibility
- **Setup**: Get key from [openrouter.ai](https://openrouter.ai/)
- **Config**: Change `backend: openrouter`

---

## Configuration Reference

**File**: `python-service/config.yaml`

```yaml
llm:
  backend: anthropic_claude  # Default

  anthropic:
    api_key_env: ANTHROPIC_API_KEY
    model: claude-haiku-4-20250122  # Haiku 4.5 (default)
    # model: claude-sonnet-4-20250514  # More powerful
    # model: claude-opus-4-20250514    # Most powerful
    timeout: 60
    max_tokens: 2048
    temperature: 0.7
```

---

## Performance Comparison

| Model | Speed | Cost (1M tokens) | Quality | Best For |
|-------|-------|------------------|---------|----------|
| **Claude Haiku 4.5** | ⚡⚡⚡ | $0.80 | ⭐⭐⭐⭐ | **Default - Recommended** |
| Claude Sonnet 4 | ⚡⚡ | $3.00 | ⭐⭐⭐⭐⭐ | Complex tasks |
| Claude Opus 4 | ⚡ | $15.00 | ⭐⭐⭐⭐⭐ | Highest quality |
| GPT-4o | ⚡⚡ | $2.50 | ⭐⭐⭐⭐ | Alternative |
| Local gpt-oss | ⚡⚡⚡ | $0.00 | ⭐⭐⭐ | Privacy |

---

## Inline AI Performance with Haiku 4.5

Expected latencies for text operations:

| Operation | Latency | Tokens Used (avg) | Cost per Op |
|-----------|---------|-------------------|-------------|
| Proofread | 0.8s | 300 | $0.00024 |
| Rewrite | 1.0s | 400 | $0.00032 |
| Summarize | 0.9s | 350 | $0.00028 |
| Key Points | 1.1s | 450 | $0.00036 |
| Format | 1.2s | 500 | $0.00040 |
| Compose | 1.5s | 600 | $0.00048 |

**Average cost per operation: ~$0.0003 (less than 1/100th of a cent!)**

---

## Security Best Practices

### ✅ DO:
- Store API keys in environment variables
- Use macOS Keychain via the app preferences
- Rotate keys regularly
- Use separate keys for dev/prod
- Set spending limits in Anthropic console

### ❌ DON'T:
- Commit API keys to git
- Store keys in plaintext files
- Share keys publicly
- Use the same key across multiple projects
- Hardcode keys in source code

---

## Troubleshooting

### Error: "ANTHROPIC_API_KEY not set"

**Solution**:
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

### Error: "Authentication failed"

**Causes**:
- Invalid API key
- Key has been revoked
- Insufficient credits

**Solution**:
- Verify key in Anthropic console
- Check account status
- Regenerate key if needed

### Error: "Rate limit exceeded"

**Solution**:
- Wait a few seconds
- Upgrade to higher tier
- Implement request throttling

### Slow responses

**Solutions**:
- Check internet connection
- Verify Anthropic API status
- Switch to Haiku for faster responses
- Enable streaming for progressive output

---

## Support

**Anthropic API Issues**: [support.anthropic.com](https://support.anthropic.com/)
**Voice Assistant Issues**: [GitHub Issues](https://github.com/AR6420/macos-siri-2.0/issues)
**Claude Documentation**: [docs.anthropic.com](https://docs.anthropic.com/)

---

## Migration from Local LLM

If you were using local gpt-oss:120b and want to switch to Claude Haiku 4.5:

1. **Get API key** from console.anthropic.com
2. **Set environment variable**: `export ANTHROPIC_API_KEY="..."`
3. **Update config**: Change `backend: anthropic_claude` in config.yaml
4. **Restart app**: The switch is instant
5. **Enjoy**: Much faster responses, no local GPU usage!

**Comparison**:
- **Local**: Free, private, slow (2-5s), requires powerful Mac
- **Haiku 4.5**: Very cheap ($0.0003/op), fast (0.8-1.5s), works on any Mac

---

## FAQ

**Q: Is Claude Haiku 4.5 good enough for inline AI?**
A: Yes! Haiku 4.5 is specifically designed for fast, high-quality text operations. It's perfect for proofreading, rewriting, and formatting.

**Q: Can I use Claude Sonnet or Opus instead?**
A: Absolutely! Just change the `model` in config.yaml to `claude-sonnet-4-20250514` or `claude-opus-4-20250514`.

**Q: How much will this cost me?**
A: Typical usage: ~1000 operations/month = $0.30/month. Very affordable!

**Q: Is my data private?**
A: Anthropic doesn't train on API data. For maximum privacy, use local LLM option.

**Q: Can I switch providers anytime?**
A: Yes! Just update the `backend` in config.yaml and restart. No data migration needed.

---

## What's Next?

- ✅ API key configured
- ✅ Backend set to Claude Haiku 4.5
- ⏭️ Test the inline AI features
- ⏭️ Try different models
- ⏭️ Monitor usage and costs

**Ready to go!** 🚀
