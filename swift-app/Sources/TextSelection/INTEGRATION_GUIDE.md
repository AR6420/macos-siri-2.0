# Enhanced UI Integration Guide

## Quick Start

The enhanced in-line AI UI is ready to use! Here's how to integrate it:

### 1. Swift Integration (Already Complete)

The Swift components are production-ready. To use them:

```swift
// In your AppDelegate or main controller
InlineAIController.shared.configure(
    showOnHover: true,
    useEnhancedUI: true  // Enable the new UI
)

InlineAIController.shared.enable()
```

That's it! The enhanced UI will automatically appear when users select text.

### 2. Python Backend Integration (Required)

Update your Python backend to handle the new commands. Here's what you need to add:

#### Command Handlers

Add these handlers to your Python service:

```python
# python-service/src/voice_assistant/inline_ai/handlers.py

async def handle_proofread_text(text: str) -> str:
    """
    Check text for grammar, spelling, and clarity issues.
    Return corrected text.
    """
    # Use LLM to proofread
    prompt = f"Proofread this text and fix any errors:\n\n{text}"
    result = await llm_client.complete(prompt)
    return result.content

async def handle_rewrite_text(text: str, custom_input: str = None) -> str:
    """
    Rewrite text with optional custom instructions.
    """
    if custom_input:
        prompt = f"Rewrite this text. Instructions: {custom_input}\n\nText:\n{text}"
    else:
        prompt = f"Rewrite this text to improve clarity:\n\n{text}"

    result = await llm_client.complete(prompt)
    return result.content

async def handle_change_style(text: str, style: str) -> str:
    """
    Change the writing style (friendly, professional, concise).
    """
    style_prompts = {
        "friendly": "Rewrite this in a friendly, conversational tone:",
        "professional": "Rewrite this in a professional, formal tone:",
        "concise": "Rewrite this to be more concise and to-the-point:"
    }

    prompt = f"{style_prompts[style]}\n\n{text}"
    result = await llm_client.complete(prompt)
    return result.content

async def handle_summarize_text(text: str) -> str:
    """
    Create a concise summary of the text.
    """
    prompt = f"Summarize this text concisely:\n\n{text}"
    result = await llm_client.complete(prompt)
    return result.content

async def handle_extract_key_points(text: str) -> str:
    """
    Extract key points as a bulleted list.
    """
    prompt = f"Extract the key points from this text as a bulleted list:\n\n{text}"
    result = await llm_client.complete(prompt)
    return result.content

async def handle_convert_to_list(text: str) -> str:
    """
    Convert text to a formatted list.
    """
    prompt = f"Convert this text into a well-formatted bulleted list:\n\n{text}"
    result = await llm_client.complete(prompt)
    return result.content

async def handle_convert_to_table(text: str) -> str:
    """
    Convert text to a markdown table.
    """
    prompt = f"Convert this data into a markdown table:\n\n{text}"
    result = await llm_client.complete(prompt)
    return result.content

async def handle_compose_text(text: str, custom_input: str) -> str:
    """
    Compose new text based on instructions.
    text parameter provides context.
    """
    prompt = f"Context: {text}\n\nInstructions: {custom_input}\n\nCompose:"
    result = await llm_client.complete(prompt)
    return result.content
```

#### Command Router

Add a router to dispatch commands:

```python
# python-service/src/voice_assistant/inline_ai/router.py

import json
from typing import Dict, Any

async def route_inline_ai_command(command_data: Dict[str, Any]) -> str:
    """Route incoming commands to appropriate handlers."""

    command = command_data.get("command")
    text = command_data.get("text", "")

    handlers = {
        "proofread_text": lambda: handle_proofread_text(text),
        "rewrite_text": lambda: handle_rewrite_text(
            text,
            command_data.get("custom_input")
        ),
        "change_style": lambda: handle_change_style(
            text,
            command_data.get("style", "friendly")
        ),
        "summarize_text": lambda: handle_summarize_text(text),
        "extract_key_points": lambda: handle_extract_key_points(text),
        "convert_to_list": lambda: handle_convert_to_list(text),
        "convert_to_table": lambda: handle_convert_to_table(text),
        "compose_text": lambda: handle_compose_text(
            text,
            command_data.get("custom_input", "")
        ),
    }

    if command in handlers:
        result = await handlers[command]()
        return result
    else:
        raise ValueError(f"Unknown command: {command}")
```

#### Main Service Integration

Update your main Python service to handle inline AI commands:

```python
# python-service/src/voice_assistant/main.py

async def handle_stdin_command(line: str):
    """Handle commands from Swift app via stdin."""

    try:
        data = json.loads(line)
        command = data.get("command")

        # Route inline AI commands
        if command in [
            "proofread_text",
            "rewrite_text",
            "change_style",
            "summarize_text",
            "extract_key_points",
            "convert_to_list",
            "convert_to_table",
            "compose_text"
        ]:
            result = await route_inline_ai_command(data)

            # Send result back to Swift
            response = {
                "status": "success",
                "command": command,
                "original_text": data.get("text"),
                "result_text": result
            }
            print(json.dumps(response), flush=True)

        # Handle other commands...

    except Exception as e:
        # Send error back to Swift
        error_response = {
            "status": "error",
            "command": data.get("command"),
            "error": str(e)
        }
        print(json.dumps(error_response), flush=True)
```

#### Swift Response Handler

Update the Swift service to handle responses:

```swift
// In PythonService.swift or similar

extension InlineAIController {

    func handlePythonResponse(_ response: [String: Any]) {
        guard let status = response["status"] as? String else { return }

        if status == "success" {
            let original = response["original_text"] as? String ?? ""
            let result = response["result_text"] as? String ?? ""

            // Replace text with result
            handleRewriteComplete(original: original, rewritten: result)

        } else if status == "error" {
            let error = response["error"] as? String ?? "Unknown error"
            handleInlineAIError(error: error)
        }
    }
}
```

### 3. Testing the Integration

#### Manual Testing

1. **Enable the enhanced UI:**
   ```swift
   InlineAIController.shared.configure(
       showOnHover: true,
       useEnhancedUI: true
   )
   InlineAIController.shared.enable()
   ```

2. **Select some text** in any text editor

3. **Orange button appears** at the end of selection

4. **Click the button** → Enhanced panel opens

5. **Try each action:**
   - Proofread
   - Rewrite
   - Change style (Friendly/Professional/Concise)
   - Summarize
   - Extract key points
   - Convert to list
   - Convert to table
   - Compose

6. **Verify text replacement** works correctly

#### Automated Testing

Run the test suite:

```bash
cd swift-app
xcodebuild test \
  -scheme VoiceAssistant \
  -destination 'platform=macOS' \
  -only-testing:VoiceAssistantTests/MenuOptionTests \
  -only-testing:VoiceAssistantTests/SelectionButtonTests \
  -only-testing:VoiceAssistantTests/EnhancedFloatingPanelTests
```

#### Python Backend Testing

```python
# Test command generation
import pytest
from voice_assistant.inline_ai.router import route_inline_ai_command

@pytest.mark.asyncio
async def test_proofread_command():
    command = {
        "command": "proofread_text",
        "text": "This text has some erors."
    }
    result = await route_inline_ai_command(command)
    assert "errors" in result.lower()

@pytest.mark.asyncio
async def test_change_style():
    command = {
        "command": "change_style",
        "text": "Hey, what's up?",
        "style": "professional"
    }
    result = await route_inline_ai_command(command)
    assert len(result) > 0
```

### 4. Troubleshooting

#### Button Not Appearing

**Check:**
- Is InlineAIController enabled?
- Is text selection >= 3 characters?
- Are Accessibility permissions granted?
- Is SelectionMonitor running?

**Debug:**
```swift
print("Enabled: \(InlineAIController.shared.isEnabled)")
print("Status: \(InlineAIController.shared.currentStatus)")
```

#### Panel Not Opening

**Check:**
- Is button delegate set correctly?
- Is showEnhancedPanel being called?
- Any console errors?

**Debug:**
```swift
// In InlineAIController
override func showEnhancedPanel(at position: CGPoint) {
    print("🔵 Showing enhanced panel at: \(position)")
    super.showEnhancedPanel(at: position)
}
```

#### Commands Not Working

**Check:**
- Python backend running?
- JSON serialization working?
- Command format matches backend?

**Debug:**
```python
# In Python backend
async def route_inline_ai_command(command_data: Dict[str, Any]) -> str:
    print(f"🔵 Received command: {command_data}")
    # ... rest of handler
```

#### Text Not Replacing

**Check:**
- Is TextReplacer working?
- Are Accessibility permissions granted?
- Is original text still selected?

**Debug:**
```swift
// In InlineAIController
func handleRewriteComplete(original: String, rewritten: String) {
    print("🔵 Original: \(original)")
    print("🔵 Rewritten: \(rewritten)")
    print("🔵 Current selection: \(currentSelection?.selectedText ?? "none")")
    // ... rest of handler
}
```

### 5. Customization

#### Custom Colors

Edit the theme colors in `EnhancedFloatingPanel.swift`:

```swift
private let primaryOrange = Color(hex: "#YOUR_COLOR")
private let secondaryPurple = Color(hex: "#YOUR_COLOR")
```

#### Custom Menu Options

Add new options to `MenuOption.swift`:

```swift
enum MenuOption: String, CaseIterable {
    // ... existing options
    case myCustomAction

    var displayName: String {
        case .myCustomAction:
            return "My Action"
    }

    var icon: String {
        case .myCustomAction:
            return "custom.icon"  // SF Symbol name
    }
}
```

#### Custom Button Position

Modify button positioning in `SelectionButton.swift`:

```swift
let buttonOrigin = CGPoint(
    x: position.x + yourOffsetX,
    y: position.y - buttonSize - yourOffsetY
)
```

### 6. Performance Optimization

#### Reduce Panel Size

If the panel is too large, adjust in `EnhancedFloatingPanel.swift`:

```swift
private let panelWidth: CGFloat = 280  // Reduced from 320
private let panelMaxHeight: CGFloat = 400  // Reduced from 500
```

#### Faster Auto-Dismiss

Reduce auto-dismiss time:

```swift
autoDismissTimer = Timer.scheduledTimer(
    withTimeInterval: 10.0,  // Reduced from 15.0
    repeats: false
)
```

#### Disable Animations

For debugging or slower machines:

```swift
// In EnhancedFloatingPanelWindow
private func animateIn() {
    self.orderFront(nil)
    self.alphaValue = 1.0
    // Skip animation
}
```

### 7. Deployment Checklist

Before deploying to users:

- [ ] All unit tests pass
- [ ] Manual testing on macOS Tahoe 26.1
- [ ] Python backend handlers implemented
- [ ] Error handling works gracefully
- [ ] Accessibility permissions requested
- [ ] Performance is acceptable
- [ ] UI matches design specs
- [ ] Documentation is complete
- [ ] Example commands tested

### 8. Migration from Legacy UI

If you're currently using the legacy FloatingPanel:

1. **Test enhanced UI** in development first
2. **Add toggle** for A/B testing:
   ```swift
   let useEnhanced = UserDefaults.standard.bool(forKey: "useEnhancedUI")
   InlineAIController.shared.configure(
       showOnHover: true,
       useEnhancedUI: useEnhanced
   )
   ```
3. **Collect feedback** from users
4. **Gradually migrate** once stable
5. **Remove legacy code** after full migration

### 9. Support

For issues or questions:

1. Check this integration guide
2. Review README_ENHANCED_UI.md
3. Check unit tests for examples
4. Review SwiftUI previews in EnhancedUIPreviews.swift
5. Open an issue on GitHub

---

**Happy coding! 🚀**
