# Voice Assistant - Usage Guide

Learn how to use Voice Assistant effectively.

## Activation Methods

### Wake Word

Say **"Hey Claude"** followed by your command:

```
"Hey Claude, what time is it?"
"Hey Claude, open Safari"
"Hey Claude, search for Python tutorials"
```

### Hotkey

Press **Cmd+Shift+Space**, wait for the beep, then speak your command.

## Example Commands

### General Queries

- "What's the weather today?"
- "Tell me a joke"
- "Explain quantum computing"
- "What's 15% of 240?"

### System Control

- "Open Safari"
- "Close all windows"
- "Increase volume"
- "Take a screenshot"

### File Operations

- "Create a file called notes.txt on my desktop"
- "List files in my Downloads folder"
- "Read the file README.md"
- "Move this file to Documents"

### Web Search

- "Search for best restaurants near me"
- "Find the latest news about AI"
- "Look up the Python documentation"

### Messages

- "Send a message to John saying I'll be late"
- "Text Mom asking about dinner"

### AppleScript

- "Tell Spotify to play music"
- "Make Safari open example.com"

## Tips for Best Results

1. **Speak clearly** - Enunciate words, don't mumble
2. **Be specific** - "Open Safari and search for X" vs "search"
3. **Wait for beep** - When using hotkey, wait for audio confirmation
4. **Natural language** - Speak naturally, no need for rigid commands
5. **One command at a time** - For complex tasks, break into steps

## Advanced Usage

### Multi-step Tasks

You can chain commands:

```
"Hey Claude, create a file called todo.txt, write 'Buy groceries' to it, then open it in TextEdit"
```

### Context Awareness

The assistant remembers recent conversation:

```
You: "Hey Claude, what's the capital of France?"
Assistant: "The capital of France is Paris."
You: "What's the population?"
Assistant: "The population of Paris is approximately 2.2 million..."
```

### Tool Chaining

The assistant can use multiple tools to accomplish tasks:

```
"Hey Claude, search for the best pizza recipe, then create a file with the recipe"
```

## Customization

### Wake Word Sensitivity

Adjust in Preferences → Wake Word → Sensitivity

- Lower (0.3): Fewer false positives, may miss wake word
- Default (0.5): Balanced
- Higher (0.8): More sensitive, may have false positives

### Hotkey

Change in Preferences → Hotkey

### Voice Speed

Adjust TTS speed in Preferences → Text-to-Speech → Speed

## Privacy & Security

- All processing is local by default
- API calls only when using cloud providers
- No telemetry or usage tracking
- API keys stored in macOS Keychain
- Conversations not saved unless configured

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
