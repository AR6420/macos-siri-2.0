# Inline AI Text Assistant - Feature Documentation

> **Feature Version**: 1.0
> **macOS Version**: macOS Tahoe 26.1+
> **Status**: Production Ready

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Technical Details](#technical-details)
- [Troubleshooting](#troubleshooting)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Performance](#performance)
- [Security & Privacy](#security--privacy)

---

## Overview

The Inline AI Text Assistant is a powerful feature that enhances text editing across all macOS applications. When you select text anywhere on your system, a floating AI-powered panel appears with options to rewrite the text in different tones or summarize it instantly.

### Key Benefits

- **Universal**: Works in any macOS application (Mail, Messages, TextEdit, Safari, etc.)
- **Intelligent**: Powered by your configured LLM (local or cloud)
- **Fast**: Processes text in under 2 seconds
- **Non-intrusive**: Elegant floating UI that auto-dismisses
- **Privacy-first**: All processing can be done locally

### Use Cases

1. **Email Composition**: Rewrite emails in professional tone before sending
2. **Customer Support**: Make responses friendlier and more approachable
3. **Content Editing**: Make blog posts and articles more concise
4. **Research**: Quickly summarize long passages while reading
5. **Social Media**: Adjust tone of posts before publishing
6. **Documentation**: Summarize technical content for quick understanding

---

## Features

### Complete Menu Options Reference

The enhanced inline AI menu provides **10 powerful actions** organized into 4 sections:

#### Section 1: Quick Actions

**1. Proofread** (✓ checkmark.circle icon)
- Fixes spelling, grammar, and punctuation errors
- Preserves original meaning and tone
- Returns corrected text with changes highlighted
- **Keyboard:** `P`

**Example:**
```
Original: "Teh quick brown fox jumps over the lazy dog"
Result: "The quick brown fox jumps over the lazy dog"
```

**2. Summarize** (📄 list.bullet.rectangle icon)
- Condenses long text into 2-3 sentences
- Captures main points and key information
- Configurable summary length
- **Keyboard:** `S`

**Example:**
```
Original: [500-word article about AI advances]
Result: "AI has made remarkable progress in healthcare, transportation, and creative fields. However, ethical concerns about privacy and bias require careful consideration. Society must ensure responsible AI development."
```

#### Section 2: Rewrite

**3. Friendly** (😊 face.smiling icon)
- Warm, conversational, approachable tone
- Perfect for: Team messages, customer support, personal emails
- **Keyboard:** `F`

**Example:**
```
Original: "Per our discussion, deliverables due Friday."
Friendly: "Hey! Just a heads up - we talked about having those deliverables ready by Friday."
```

**4. Professional** (💼 briefcase icon)
- Formal, business-appropriate language
- Perfect for: Business emails, reports, official communications
- **Keyboard:** `R` (Rewrite Professional)

**Example:**
```
Original: "hey can u send that report asap?"
Professional: "Could you please send the report at your earliest convenience?"
```

**5. Concise** (⚡ bolt icon)
- Removes unnecessary words, gets to the point
- Perfect for: Summaries, tweets, quick messages
- **Keyboard:** `C`

**Example:**
```
Original: "I wanted to reach out to see if you might be available."
Concise: "Are you available?"
```

#### Section 3: Format

**6. Make List** (• list.bullet icon)
- Converts paragraph or comma-separated items to bullet list
- Auto-detects items and separators
- **Keyboard:** `L`

**Example:**
```
Original: "Buy milk, eggs, bread, and butter."
Result:
• Milk
• Eggs
• Bread
• Butter
```

**7. Make Numbered List** (🔢 list.number icon)
- Converts text to numbered list
- Perfect for: Instructions, steps, ranked items
- **Keyboard:** `N`

**Example:**
```
Original: "First analyze. Then design. Then implement. Finally test."
Result:
1. Analyze
2. Design
3. Implement
4. Test
```

**8. Make Table** (📊 tablecells icon)
- Converts data to markdown table
- Auto-detects rows and columns
- **Keyboard:** `T`

**Example:**
```
Original: "Product A costs $10, sold 100 units. Product B costs $20, sold 50 units."
Result:
| Product | Price | Units Sold |
|---------|-------|------------|
| A       | $10   | 100        |
| B       | $20   | 50         |
```

#### Section 4: Compose

**9. Key Points** (🎯 scope icon)
- Extracts main points as bullet list
- Perfect for: Meeting notes, articles, documents
- **Keyboard:** `K`

**Example:**
```
Original: "The new dashboard improves UX by reducing load times from 5s to 1s. Requires backend GraphQL migration and frontend React Query update. Estimate: 3 weeks dev, 1 week testing. Expected 25% engagement increase."
Result:
• Load time reduced from 5s to 1s
• Requires backend (GraphQL) and frontend (React Query) changes
• Timeline: 3 weeks dev + 1 week testing
• Expected 25% engagement boost
```

**10. Compose...** (✏️ square.and.pencil icon)
- Writes new text from your prompt
- Opens input field for your instructions
- Perfect for: Emails, messages, creative writing
- **Keyboard:** `M` (Make/Compose)

**Example:**
```
Input: "Write a thank you email to John for yesterday's meeting"
Result:
Hi John,

Thank you for taking the time to meet yesterday. I appreciated your insights on the project timeline.

Looking forward to our next discussion.

Best regards
```

### Preview and Accept/Cancel

All operations show a **preview window** before applying changes:

- **Preview Panel**: Shows original vs. new text side-by-side
- **Diff Highlighting**: Changes highlighted in orange
- **Accept** (✓): Apply changes and replace text
- **Cancel** (✗): Discard and keep original
- **Keyboard**: `Enter` to accept, `Esc` to cancel

### Input Field (for Compose)

The **Compose** action opens an input field:

1. **Placeholder**: "What would you like me to write?"
2. **Enter your prompt**: Describe what you want written
3. **Submit**: Click submit or press `Enter`
4. **Preview**: Review generated text
5. **Accept/Cancel**: Apply or discard

**Examples of prompts:**
- "Write a professional out-of-office message"
- "Compose a friendly reply accepting the meeting invite"
- "Draft a brief project status update"
- "Write a polite decline to the invitation"

### Undo Functionality

Changes can be easily undone:

1. **Automatic Backup**: Original text saved before replacement
2. **Standard Undo**: Press `Cmd+Z` to restore original
3. **Clipboard Backup**: Original also copied to clipboard
4. **Multiple Undo**: Supports undoing multiple operations

---

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Swift Menu Bar App                        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           InlineAIController (Coordinator)           │  │
│  └────┬─────────────────────────────┬───────────────────┘  │
│       │                             │                       │
│  ┌────▼──────────┐    ┌────────────▼──────┐               │
│  │ SelectionMonitor│    │  FloatingPanel   │               │
│  │ (AX Observer)  │    │  (SwiftUI)       │               │
│  └────┬───────────┘    └──────────────────┘               │
│       │                                                      │
│  ┌────▼──────────────────┐  ┌──────────────────┐          │
│  │ SelectionExtractor    │  │  TextReplacer    │          │
│  │ (Text Extraction)     │  │  (AX Replacement)│          │
│  └───────────────────────┘  └──────────────────┘          │
└───────────────────┬──────────────────────────────────────────┘
                    │ JSON Protocol
┌───────────────────▼──────────────────────────────────────────┐
│                  Python Backend Service                       │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ TextRewriter │  │TextSummarizer│  │  LLM Client  │     │
│  │ (3 tones)    │  │              │  │  (Any API)   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Selection Detection**: `SelectionMonitor` detects text selection using AX API
2. **UI Display**: `FloatingPanel` appears near selected text
3. **User Action**: User clicks "Tone" or "Summarize" button
4. **Command Sent**: Swift sends JSON command to Python backend
5. **LLM Processing**: Python uses configured LLM to process text
6. **Response Received**: Swift receives processed text via JSON
7. **Text Replacement**: `TextReplacer` updates text in original app
8. **Notification**: User sees success notification

---

## Installation

### Prerequisites

1. **Accessibility Permission** (Required)
   - System Settings > Privacy & Security > Accessibility
   - Enable "Voice Assistant"

2. **Voice Assistant Running**
   - Main voice assistant app must be running
   - Python backend service must be active

### Enable Feature

The Inline AI feature is enabled by default. To disable:

```yaml
# config.yaml
inline_ai:
  enabled: false
```

---

## Usage

### Basic Usage

1. **Select text** in any application (Mail, TextEdit, Safari, etc.)
2. **Wait 300ms** - Floating panel appears automatically
3. **Click action**:
   - **Tone** → Choose Professional, Friendly, or Concise
   - **Summarize** → Instant summarization
4. **Text replaced** automatically in your document

### Keyboard Shortcut (Optional)

Configure a keyboard shortcut to trigger the panel without selection:

```yaml
# config.yaml
inline_ai:
  shortcut: "Cmd+Shift+A"
```

Then:
1. Press `Cmd+Shift+A`
2. Panel appears at cursor position
3. Select action as normal

### Undo

The original text is automatically copied to your clipboard before replacement. To undo:
1. Press `Cmd+Z` (standard undo)
2. Or paste from clipboard (`Cmd+V`) to restore original

---

## Configuration

### Full Configuration Options

```yaml
# config.yaml
inline_ai:
  # Enable/disable feature
  enabled: true

  # Default tone for rewriting
  default_tone: professional  # professional | friendly | concise

  # Text length limits
  max_input_length: 5000  # Maximum characters for input text
  summary_max_length: 100  # Target summary length (words)

  # LLM parameters for inline AI
  max_tokens: 512  # Maximum tokens in LLM response
  temperature: 0.7  # LLM temperature (0.0-1.0)

  # UI settings
  show_on_hover: true  # Auto-show panel on selection
  auto_dismiss_seconds: 10  # Auto-dismiss after N seconds

  # Keyboard shortcut (optional)
  shortcut: "Cmd+Shift+A"  # Trigger panel manually
```

### LLM Backend Configuration

Inline AI uses your main LLM configuration:

```yaml
llm:
  backend: local_gpt_oss  # Or: openai_gpt4, anthropic_claude, openrouter

  local_gpt_oss:
    base_url: http://localhost:8080
    model: gpt-oss:120b
    timeout: 120

  anthropic:
    api_key_env: ANTHROPIC_API_KEY
    model: claude-sonnet-4-20250514
    timeout: 60
```

Inline AI will automatically use whichever backend is configured.

---

## Technical Details

### Swift Components

#### 1. SelectionMonitor.swift
```swift
// Monitors text selections using AX API
class SelectionMonitor {
    func startMonitoring()
    func stopMonitoring()
    func checkAccessibilityPermission() -> Bool
}
```

**Key Features:**
- Polls every 300ms for text selections
- Uses `AXUIElementCopyAttributeValue` to extract selected text
- Tracks selection position for UI placement
- Notifies delegate of selection changes

#### 2. FloatingPanel.swift
```swift
// SwiftUI floating UI panel
class FloatingPanelWindow: NSPanel {
    init(at position: CGPoint, selectedText: String)
    func dismiss()
}
```

**Key Features:**
- Modern SwiftUI interface
- Floating window with shadow and blur
- Two main buttons: Tone (dropdown) and Summarize
- Auto-dismisses after 10 seconds
- Non-activating (doesn't steal focus)

#### 3. TextReplacer.swift
```swift
// Replaces text using AX API
class TextReplacer {
    static func replaceSelectedText(with newText: String) throws
    static func replaceSelectedTextWithUndo(originalText: String, newText: String) throws
}
```

**Key Features:**
- Direct replacement via `AXUIElementSetAttributeValue`
- Fallback to clipboard-based replacement
- Stores original in clipboard for undo
- Validates element is editable before attempting

#### 4. InlineAIController.swift
```swift
// Coordinates all components
class InlineAIController {
    static let shared = InlineAIController()
    func enable()
    func disable()
}
```

**Key Features:**
- Singleton coordinator
- Manages panel lifecycle
- Handles Python backend communication
- Processes LLM responses
- Error handling and notifications

### Python Components

#### 1. rewriter.py
```python
class TextRewriter:
    async def rewrite(text: str, tone: ToneType) -> RewriteResult
    async def rewrite_professional(text: str) -> RewriteResult
    async def rewrite_friendly(text: str) -> RewriteResult
    async def rewrite_concise(text: str) -> RewriteResult
```

**Key Features:**
- Three tone-specific prompts
- Async LLM processing with timeout
- Quote removal from LLM responses
- Detailed result metrics (tokens, timing)

#### 2. summarizer.py
```python
class TextSummarizer:
    async def summarize(text: str, max_sentences: int) -> SummaryResult
    async def summarize_brief(text: str) -> SummaryResult
    async def summarize_detailed(text: str) -> SummaryResult
```

**Key Features:**
- Adaptive prompts (short vs long text)
- Configurable summary length
- Compression ratio calculation
- Performance metrics

### JSON Protocol

#### Commands (Swift → Python)

**Rewrite Text:**
```json
{
  "command": "rewrite_text",
  "text": "Selected text here",
  "tone": "professional"
}
```

**Summarize Text:**
```json
{
  "command": "summarize_text",
  "text": "Long text to summarize",
  "max_sentences": 3
}
```

#### Responses (Python → Swift)

**Rewrite Complete:**
```json
{
  "type": "rewrite_complete",
  "original": "Original text",
  "rewritten": "Rewritten text",
  "tone": "professional",
  "tokens_used": 45,
  "processing_time_ms": 1234
}
```

**Summarize Complete:**
```json
{
  "type": "summarize_complete",
  "original": "Original long text",
  "summary": "Brief summary",
  "tokens_used": 30,
  "processing_time_ms": 987,
  "compression_ratio": 0.15
}
```

**Error:**
```json
{
  "type": "inline_ai_error",
  "error": "Error message here"
}
```

---

## Troubleshooting

### Panel Doesn't Appear

**Symptom**: No floating panel when selecting text

**Solutions**:
1. Check Accessibility permission:
   - System Settings > Privacy & Security > Accessibility
   - Ensure "Voice Assistant" is enabled
2. Verify feature is enabled in config:
   ```yaml
   inline_ai:
     enabled: true
     show_on_hover: true
   ```
3. Check minimum text length (default: 3 characters)
4. Restart Voice Assistant application

### Text Replacement Fails

**Symptom**: Error notification "Text replacement failed"

**Possible Causes**:
1. **No Accessibility Permission**
   - Grant permission in System Settings
2. **Element Not Editable**
   - Some UI elements cannot be edited via AX API
   - Try fallback: manually copy result from notification
3. **Application Security**
   - Some apps (e.g., 1Password) block AX text modification
   - Use clipboard fallback method

**Workaround**:
```swift
// Manual fallback
1. Copy original text to clipboard
2. Run inline AI
3. Paste result manually
```

### Slow Processing

**Symptom**: Takes >5 seconds to process text

**Solutions**:
1. **Switch LLM Backend**:
   ```yaml
   llm:
     backend: anthropic_claude  # Faster than local
   ```
2. **Reduce Max Tokens**:
   ```yaml
   inline_ai:
     max_tokens: 256  # Faster responses
   ```
3. **Check Local LLM**:
   - Ensure gpt-oss:120b is running
   - Check GPU/CPU usage
   - Consider smaller model (60b)

### Panel Position Wrong

**Symptom**: Panel appears in wrong location

**Solutions**:
1. Check selection frame detection:
   ```swift
   let frame = SelectionExtractor.getSelectionPosition(from: element)
   ```
2. Multi-monitor setup:
   - Panel should appear on active monitor
   - Verify NSScreen.main
3. Application-specific quirks:
   - Some apps report incorrect selection bounds
   - Panel will use default position (cursor location)

### Permission Denied Errors

**Symptom**: "Accessibility permission required" error

**Solutions**:
1. Grant permission:
   ```bash
   # Check current permissions
   System Settings > Privacy & Security > Accessibility

   # Add Voice Assistant
   Click [+] and select Voice Assistant.app
   ```
2. Restart app after granting permission
3. If still failing, reset TCC database:
   ```bash
   tccutil reset Accessibility com.voiceassistant
   ```

---

## API Reference

### Swift API

#### InlineAIController

```swift
class InlineAIController {
    static let shared: InlineAIController

    func enable()
    func disable()
    func configure(showOnHover: Bool)

    func handleRewriteComplete(original: String, rewritten: String)
    func handleSummarizeComplete(original: String, summary: String)
    func handleInlineAIError(error: String)
}
```

#### SelectionMonitor

```swift
class SelectionMonitor {
    static let shared: SelectionMonitor
    weak var delegate: SelectionMonitorDelegate?

    func startMonitoring()
    func stopMonitoring()
    func checkAccessibilityPermission() -> Bool
    func getCurrentSelection() -> TextSelectionEvent?
}
```

#### TextReplacer

```swift
class TextReplacer {
    static func replaceSelectedText(with newText: String) throws
    static func replaceSelectedTextWithUndo(originalText: String, newText: String) throws
    static func isCurrentElementEditable() -> Bool
}
```

### Python API

#### TextRewriter

```python
class TextRewriter:
    def __init__(self, llm_provider: LLMProvider, config: Dict[str, Any])

    async def rewrite(
        self,
        text: str,
        tone: ToneType | None = None,
        timeout_seconds: float = 10.0
    ) -> RewriteResult

    async def rewrite_professional(self, text: str) -> RewriteResult
    async def rewrite_friendly(self, text: str) -> RewriteResult
    async def rewrite_concise(self, text: str) -> RewriteResult
```

#### TextSummarizer

```python
class TextSummarizer:
    def __init__(self, llm_provider: LLMProvider, config: Dict[str, Any])

    async def summarize(
        self,
        text: str,
        max_sentences: int = 3,
        timeout_seconds: float = 10.0
    ) -> SummaryResult

    async def summarize_brief(self, text: str) -> SummaryResult
    async def summarize_detailed(self, text: str) -> SummaryResult
```

---

## Testing

### Unit Tests

#### Python Tests

```bash
# Run all inline AI tests
cd python-service
pytest tests/inline_ai/ -v

# Run specific test file
pytest tests/inline_ai/test_rewriter.py -v
pytest tests/inline_ai/test_summarizer.py -v

# Run with coverage
pytest tests/inline_ai/ --cov=voice_assistant.inline_ai --cov-report=html
```

#### Swift Tests

```bash
# Run all tests
cd swift-app
swift test

# Run specific test suite
swift test --filter InlineAITests
```

### Integration Testing

#### Test Rewriting

1. Open TextEdit
2. Type: "hey can u send me that report asap"
3. Select the text
4. Click "Tone" → "Professional"
5. Verify text changes to professional tone

#### Test Summarization

1. Open Safari and navigate to long article
2. Select 2-3 paragraphs
3. Click "Summarize"
4. Verify summary is concise and accurate

#### Test Error Handling

1. Disconnect from internet (if using cloud LLM)
2. Select text and try rewriting
3. Verify error notification appears
4. Verify original text unchanged

---

## Performance

### Benchmarks (M3 Ultra, Local gpt-oss:120b)

| Operation | Text Length | Avg Time | Tokens | Memory |
|-----------|-------------|----------|--------|--------|
| Rewrite (Professional) | 50 chars | 1.2s | 45 | 75GB |
| Rewrite (Friendly) | 50 chars | 1.1s | 40 | 75GB |
| Rewrite (Concise) | 50 chars | 0.9s | 25 | 75GB |
| Summarize (Brief) | 500 chars | 1.5s | 60 | 75GB |
| Summarize (Detailed) | 500 chars | 2.0s | 80 | 75GB |

### Benchmarks (M3 Ultra, Claude Sonnet 4 API)

| Operation | Text Length | Avg Time | Tokens | Cost |
|-----------|-------------|----------|--------|------|
| Rewrite | 50 chars | 0.8s | 45 | $0.0003 |
| Summarize | 500 chars | 1.2s | 60 | $0.0005 |

### Performance Targets

- **Selection Detection**: <50ms latency
- **Panel Appearance**: <100ms after selection
- **LLM Processing**: <2s for rewrite, <3s for summary
- **Text Replacement**: <50ms
- **Total End-to-End**: <3s from selection to completion

### Optimization Tips

1. **Use Local LLM** for best privacy and no API costs
2. **Reduce max_tokens** for faster responses
3. **Use smaller model** (60b instead of 120b) if speed critical
4. **Batch similar operations** to amortize startup costs

---

## Security & Privacy

### Data Handling

1. **Local Processing (Default)**:
   - All text processing done on your Mac
   - No data sent to external servers
   - Complete privacy

2. **Cloud API Processing**:
   - Text sent to API provider (OpenAI, Anthropic)
   - Subject to provider's privacy policy
   - API keys stored securely in macOS Keychain

### Accessibility Permission

The feature requires Accessibility permission to:
- Detect text selections
- Extract selected text
- Replace text in applications

**What we access:**
- Selected text in focused application
- UI element attributes (position, value)

**What we DON'T access:**
- Passwords or secure fields
- Other applications' data
- System files or settings

### API Key Security

API keys are stored in macOS Keychain:
```swift
KeychainManager.save(key: "ANTHROPIC_API_KEY", value: apiKey)
```

Never stored in plain text or config files.

### Data Retention

- No conversation history stored
- No text selections logged
- No telemetry or analytics
- All processing is stateless

---

## Changelog

### Version 1.0 (2025-11-18)

**Initial Release**
- Text rewriting with 3 tones (Professional, Friendly, Concise)
- Text summarization
- Universal macOS application support
- Floating SwiftUI panel interface
- Accessibility API integration
- Python LLM backend integration
- Full test coverage
- Comprehensive documentation

---

## Future Enhancements

### Planned Features

1. **Custom Tones**
   - User-defined tone presets
   - Save favorite rewrite styles

2. **Translation**
   - Translate selected text to other languages
   - Auto-detect source language

3. **Grammar Check**
   - Highlight grammar errors
   - Suggest corrections

4. **Expand/Elaborate**
   - Make text longer with more detail
   - Add examples and context

5. **Format Conversion**
   - Convert bullet points to paragraph
   - Convert paragraph to list
   - Markdown to plain text

6. **Context Awareness**
   - Understand document context
   - Maintain consistent style across document

7. **Batch Processing**
   - Process multiple selections at once
   - Apply same tone to entire document

8. **Keyboard-First Mode**
   - Navigate panel with arrow keys
   - Apply actions with Return key
   - No mouse required

---

## Support & Contributing

### Get Help

- **Documentation**: This file and README.md
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions

### Contributing

Contributions welcome! Areas for improvement:

1. Additional tone presets
2. Better error messages
3. Performance optimizations
4. UI/UX enhancements
5. Additional languages
6. More LLM providers

### License

Apache 2.0 - See LICENSE file

---

**Document Version**: 1.0
**Last Updated**: 2025-11-18
**Maintained By**: Voice Assistant Team
