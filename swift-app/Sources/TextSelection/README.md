# Enhanced Text Operations - Implementation Guide

This document describes the enhanced input field editing and advanced text replacement capabilities implemented for the macOS Voice Assistant inline AI features.

## Table of Contents

1. [Overview](#overview)
2. [Components](#components)
3. [Features](#features)
4. [Architecture](#architecture)
5. [Usage](#usage)
6. [API Reference](#api-reference)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

## Overview

The enhanced text operations provide a comprehensive suite of tools for inline AI-powered text editing, including:

- Editable text input fields with validation
- Multiple text replacement modes
- Diff visualization with change tracking
- Loading states with progress indicators
- Result preview before applying changes
- Undo/redo support with history management
- Keyboard shortcuts for improved UX

## Components

### 1. EditableTextSection.swift

Provides editable text input components with character counting and validation.

**Key Classes:**
- `EditableTextSection`: Main editable text view with validation
- `CompactEditableTextSection`: Collapsible version for space-constrained UIs
- `MultilineTextField`: NSTextView wrapper for rich editing

**Features:**
- Real-time character count (max 5000 characters)
- Copy/paste/clear operations
- Visual validation feedback
- Placeholder text support

### 2. DiffView.swift

Displays text differences with inline highlighting and multiple view modes.

**Key Components:**
- `DiffView`: Main diff viewer with three modes
  - Side-by-side comparison
  - Unified diff view
  - Inline word-level diff
- `DiffSegment`: Represents individual changes
- `DiffChangeType`: Deletion, insertion, modification, unchanged

**Algorithm:**
- Uses Longest Common Subsequence (LCS) for accurate diff calculation
- Line-by-line and word-level comparison support
- Color-coded changes (red=deletion, green=insertion, yellow=modification)

### 3. LoadingOverlay.swift

Comprehensive loading states for asynchronous operations.

**Loading States:**
- `idle`: No operation
- `loading`: Indeterminate progress
- `progress`: Determinate progress with percentage
- `success`: Operation completed successfully
- `error`: Operation failed

**Specialized Views:**
- `RewriteLoadingView`: Tone-specific rewriting feedback
- `SummarizeLoadingView`: Summary progress indicator
- `ProofreadLoadingView`: Multi-step proofreading progress

### 4. ResultPreviewPanel.swift

Preview changes before applying them to the document.

**Features:**
- Side-by-side original/modified comparison
- Diff view integration
- Editable result before acceptance
- Character count and change statistics
- Accept/Reject/Edit Further actions

**Window Types:**
- `ResultPreviewPanelWindow`: Floating panel window
- `ResultPreviewView`: SwiftUI content view
- `CompactPreviewView`: Lightweight preview for quick decisions

### 5. Enhanced TextReplacer.swift

Advanced text replacement with multiple modes and undo support.

**Replacement Modes:**
```swift
enum ReplacementMode {
    case replaceSelection      // Replace selected text
    case insertBefore          // Insert before selection
    case insertAfter           // Insert after selection
    case replaceParagraph      // Replace entire paragraph
    case replaceAll            // Replace all occurrences
}
```

**Features:**
- Undo/redo stack (50 items)
- Formatting preservation attempts
- Accessibility API integration
- Clipboard-based fallback
- Error recovery

### 6. EnhancedFloatingPanel.swift

Existing comprehensive floating panel with sectioned layout and custom input support.

## Features

### Input Field Editing

```swift
// Basic usage
EditableTextSection(text: $editedText)

// With validation
if editedText.count > 0 && editedText.count <= 5000 {
    // Valid text
}

// Compact version
CompactEditableTextSection(text: $editedText)
```

### Text Replacement Modes

```swift
// Replace selected text (default)
try TextReplacer.replaceText(with: newText)

// Insert before selection
try TextReplacer.replaceText(with: newText, mode: .insertBefore)

// Insert after selection
try TextReplacer.replaceText(with: newText, mode: .insertAfter)

// Replace entire paragraph
try TextReplacer.replaceText(with: newText, mode: .replaceParagraph)

// Replace all occurrences
try TextReplacer.replaceText(with: newText, mode: .replaceAll)
```

### Undo/Redo Support

```swift
// Check if undo is available
if TextReplacer.canUndo() {
    try TextReplacer.undoLastReplacement()
}

// Get undo stack size
let stackSize = TextReplacer.undoStackSize()

// Clear undo history
TextReplacer.clearUndoStack()
```

### Diff Visualization

```swift
DiffView(
    originalText: original,
    modifiedText: modified,
    showLineNumbers: true
)
```

### Loading States

```swift
// Show loading
LoadingOverlay(
    state: .loading("Processing your text..."),
    onCancel: { /* cancel handler */ }
)

// Show progress
LoadingOverlay(
    state: .progress(0.65, "Analyzing content..."),
    onCancel: nil
)

// Show success
LoadingOverlay(
    state: .success("Text updated successfully!"),
    onCancel: nil
)
```

### Preview Before Applying

```swift
let previewPanel = ResultPreviewPanelWindow(
    originalText: original,
    modifiedText: modified,
    operationType: "Rewrite (Professional)"
)

previewPanel.actionHandler = { action in
    switch action {
    case .accept:
        // Apply changes
    case .reject:
        // Discard changes
    case .editFurther:
        // Show editor
    case .copyResult:
        // Copy to clipboard
    }
}

previewPanel.show()
```

## Architecture

### Data Flow

```
User Selection
    ↓
SelectionMonitor detects selection
    ↓
InlineAIController shows EnhancedFloatingPanel
    ↓
User edits text in EditableTextSection
    ↓
User selects action (Rewrite/Summarize/Proofread)
    ↓
LoadingOverlay shows progress
    ↓
Python backend processes request
    ↓
ResultPreviewPanel shows changes (with DiffView)
    ↓
User accepts/rejects
    ↓
TextReplacer applies changes (with undo support)
    ↓
Success notification
```

### Component Dependencies

```
InlineAIController
  ├── EnhancedFloatingPanel
  │   └── EditableTextSection
  ├── LoadingOverlay
  ├── ResultPreviewPanel
  │   └── DiffView
  └── TextReplacer
```

## Usage

### Integration with InlineAIController

```swift
class InlineAIController {
    func showEnhancedPanel(for selection: TextSelectionEvent) {
        let panel = EnhancedFloatingPanelWindow(
            at: selection.selectionFrame.origin,
            selectedText: selection.selectedText
        )

        panel.panelDelegate = self
        panel.show()
    }

    func handleAction(_ action: EnhancedPanelAction) {
        switch action {
        case .rewrite(let tone, let text):
            showLoading(.loading("Rewriting with \(tone) tone..."))
            sendRewriteRequest(text: text, tone: tone)

        case .summarize(let text):
            showLoading(.loading("Summarizing..."))
            sendSummarizeRequest(text: text)

        case .proofread(let text):
            showLoading(.loading("Proofreading..."))
            sendProofreadRequest(text: text)

        default:
            break
        }
    }

    func handleBackendResponse(original: String, modified: String, type: String) {
        dismissLoading()

        // Show preview
        let preview = ResultPreviewPanelWindow(
            originalText: original,
            modifiedText: modified,
            operationType: type
        )

        preview.actionHandler = { [weak self] action in
            if action == .accept {
                self?.applyChanges(modified)
            }
        }

        preview.show()
    }

    func applyChanges(_ text: String) {
        do {
            try TextReplacer.replaceText(with: text)
            TextReplacer.showReplacementNotification(success: true)
        } catch {
            TextReplacer.showReplacementNotification(success: false, error: error)
        }
    }
}
```

### Python Backend Integration

Extended JSON protocol for preview support:

```json
// Request with edited text
{
    "command": "rewrite_text",
    "text": "{edited_text}",
    "original": "{original_text}",
    "tone": "professional",
    "preview": true
}

// Response with preview
{
    "type": "preview_ready",
    "original": "Original text...",
    "modified": "Rewritten text...",
    "action": "rewrite",
    "metadata": {
        "tone": "professional",
        "changes_count": 15
    }
}

// Immediate replacement (no preview)
{
    "command": "summarize_text",
    "text": "{text}",
    "preview": false
}
```

## API Reference

### EditableTextSection

```swift
struct EditableTextSection: View {
    @Binding var text: String
    let maxLength: Int = 5000
    let minLength: Int = 1
    let placeholder: String = "Enter or edit text..."

    var characterCount: Int
    var isValid: Bool
}
```

### TextReplacer

```swift
class TextReplacer {
    // Main replacement methods
    static func replaceText(with newText: String, mode: ReplacementMode, preserveFormatting: Bool) throws
    static func replaceSelectedText(with newText: String) throws

    // Undo/redo
    static func undoLastReplacement() throws
    static func canUndo() -> Bool
    static func undoStackSize() -> Int
    static func clearUndoStack()

    // Validation
    static func isCurrentElementEditable() -> Bool

    // Notifications
    static func showReplacementNotification(success: Bool, error: Error?)
    static func showUndoNotification()
}
```

### DiffView

```swift
struct DiffView: View {
    let originalText: String
    let modifiedText: String
    let showLineNumbers: Bool

    enum DiffViewMode {
        case sideBySide
        case unified
        case inline
    }
}
```

### LoadingOverlay

```swift
enum LoadingState {
    case idle
    case loading(String)
    case progress(Double, String)
    case success(String)
    case error(String)
}

struct LoadingOverlay: View {
    let state: LoadingState
    let onCancel: (() -> Void)?
}
```

### ResultPreviewPanel

```swift
enum PreviewAction {
    case accept
    case reject
    case editFurther
    case copyResult
}

class ResultPreviewPanelWindow: NSPanel {
    var actionHandler: ((PreviewAction) -> Void)?

    init(originalText: String, modifiedText: String, operationType: String)
    func show()
}
```

## Testing

### Unit Tests

```swift
// Character count validation
func testEditableTextSectionCharacterCount()
func testEditableTextSectionMaxLength()

// Replacement modes
func testReplacementModes()
func testUndoStackManagement()

// Diff algorithm
func testDiffAlgorithmLCS()
func testDiffAlgorithmLineDiff()

// Loading states
func testLoadingStates()

// Error handling
func testReplacementErrors()
func testErrorRecovery()
```

### Integration Tests

```swift
// Full pipeline
func testFullTextReplacementFlow()

// Preview workflow
func testPreviewAcceptReject()

// Keyboard shortcuts
func testKeyboardShortcutHandling()
```

### Manual Testing Checklist

- [ ] Text input accepts characters and enforces max length
- [ ] Character count updates in real-time
- [ ] Copy/paste operations work correctly
- [ ] All replacement modes function properly
- [ ] Undo/redo works across different apps
- [ ] Diff view displays changes accurately
- [ ] All three diff view modes work
- [ ] Loading indicators appear and animate
- [ ] Preview panel shows correct before/after
- [ ] Accept applies changes correctly
- [ ] Reject discards changes
- [ ] Edit further reopens editor
- [ ] Keyboard shortcuts work (Cmd+Enter, Esc, Cmd+Z)
- [ ] Works in TextEdit, Notes, Safari, Mail
- [ ] Handles special characters and unicode
- [ ] Performance acceptable with large texts

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Cmd+Enter` | Apply action / Accept changes |
| `Cmd+E` | Edit text |
| `Cmd+Z` | Undo last replacement |
| `Cmd+Shift+Z` | Redo (future) |
| `Esc` | Cancel / Dismiss panel |
| `Cmd+W` | Close panel |
| `Cmd+C` | Copy result |

## Troubleshooting

### Text Replacement Fails

**Problem:** Text replacement doesn't work in certain apps.

**Solutions:**
1. Check Accessibility permissions in System Preferences
2. Try the clipboard-based fallback method
3. Verify the text field is actually editable
4. Check app compatibility (some apps have custom text fields)

### Undo Not Working

**Problem:** Undo button doesn't restore text.

**Solutions:**
1. Verify undo stack has items: `TextReplacer.canUndo()`
2. Check if focus is still on the same text field
3. Ensure app supports text value setting via Accessibility API

### Diff View Shows Incorrect Changes

**Problem:** Diff highlighting is inaccurate.

**Solutions:**
1. Verify both original and modified text are correct
2. Check for invisible characters (tabs vs spaces)
3. Try different diff view modes
4. For very large texts, consider using unified view

### Loading Indicator Stuck

**Problem:** Loading overlay doesn't dismiss.

**Solutions:**
1. Check backend response is received
2. Verify timeout handling is implemented
3. Ensure cancel button works
4. Check for networking issues

### Preview Panel Doesn't Show

**Problem:** Result preview panel doesn't appear.

**Solutions:**
1. Verify window level is set to `.floating`
2. Check screen bounds calculation
3. Ensure panel isn't hidden behind other windows
4. Verify `show()` method is called on main thread

## Performance Considerations

### Large Text Handling

For texts > 1000 characters:
- Use streaming for backend requests
- Implement chunking for very large texts
- Show progress indicators
- Consider lazy loading in diff view

### Diff Algorithm Optimization

For texts with > 100 lines:
- Use unified view instead of side-by-side
- Implement virtual scrolling
- Cache computed diffs
- Consider background thread calculation

### Memory Management

- Clear undo stack periodically (max 50 items)
- Release preview panels when dismissed
- Avoid retaining large strings unnecessarily
- Use weak references for delegates

## Future Enhancements

### Planned Features

1. **Batch Processing**
   - Select multiple text blocks
   - Apply same transformation to all
   - Show aggregate progress

2. **History Management**
   - Persistent transformation history
   - Reuse previous transformations
   - Favorites/saved transformations

3. **Advanced Diff**
   - Word-level highlighting within lines
   - Semantic diff (ignore whitespace changes)
   - Export diff as patch file

4. **Collaborative Editing**
   - Share transformations with others
   - Import transformation templates
   - Team-wide preferences

5. **Custom Actions**
   - User-defined transformation scripts
   - Plugin system for third-party actions
   - Macro recording and playback

## Contributing

When adding new features:

1. Follow existing code structure
2. Add comprehensive tests
3. Update this README
4. Include code examples
5. Test on multiple macOS versions
6. Verify accessibility compliance

## License

Apache 2.0 - See main project LICENSE file.

---

**Last Updated:** 2025-11-18
**Version:** 1.0.0
**Maintainer:** Voice Assistant Development Team
