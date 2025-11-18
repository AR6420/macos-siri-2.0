//
//  TextReplacer.swift
//  VoiceAssistant
//
//  Replaces selected text using macOS Accessibility API with advanced features
//

import Foundation
import Cocoa
import ApplicationServices

class TextReplacer {

    // MARK: - Replacement Mode

    enum ReplacementMode {
        case replaceSelection      // Replace selected text
        case insertBefore          // Insert before selection
        case insertAfter           // Insert after selection
        case replaceParagraph      // Replace entire paragraph
        case replaceAll            // Replace all occurrences
    }

    // MARK: - Error Types

    enum ReplacementError: Error {
        case noFocusedElement
        case accessibilityDenied
        case replacementFailed
        case clipboardFailed
        case invalidElement
        case undoStackFull
        case formattingPreservationFailed

        var localizedDescription: String {
            switch self {
            case .noFocusedElement:
                return "No text field is currently focused"
            case .accessibilityDenied:
                return "Accessibility permission is required"
            case .replacementFailed:
                return "Failed to replace text"
            case .clipboardFailed:
                return "Failed to copy text to clipboard"
            case .invalidElement:
                return "Selected element cannot be edited"
            case .undoStackFull:
                return "Undo history is full"
            case .formattingPreservationFailed:
                return "Could not preserve text formatting"
            }
        }
    }

    // MARK: - Undo Stack

    private static var undoStack: [UndoItem] = []
    private static let maxUndoStackSize = 50

    struct UndoItem {
        let originalText: String
        let newText: String
        let timestamp: Date
        let elementInfo: [String: Any]?
    }

    // MARK: - Static Methods

    /// Replace currently selected text with new text
    static func replaceSelectedText(with newText: String) throws {
        // Get focused UI element
        guard let focusedElement = getFocusedElement() else {
            throw ReplacementError.noFocusedElement
        }

        // Try direct replacement first
        if tryDirectReplacement(element: focusedElement, newText: newText) {
            return
        }

        // Fallback to clipboard-based replacement
        if tryClipboardReplacement(newText: newText) {
            return
        }

        throw ReplacementError.replacementFailed
    }

    /// Replace text and store original in clipboard for undo
    static func replaceSelectedTextWithUndo(originalText: String, newText: String) throws {
        // Store original text in clipboard for undo
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(originalText, forType: .string)

        // Replace text
        try replaceSelectedText(with: newText)
    }

    // MARK: - Private Methods

    private static func getFocusedElement() -> AXUIElement? {
        let systemWideElement = AXUIElementCreateSystemWide()

        var focusedElement: CFTypeRef?
        let result = AXUIElementCopyAttributeValue(
            systemWideElement,
            kAXFocusedUIElementAttribute as CFString,
            &focusedElement
        )

        guard result == .success,
              let element = focusedElement as? AXUIElement else {
            return nil
        }

        return element
    }

    /// Try direct replacement using Accessibility API
    private static func tryDirectReplacement(element: AXUIElement, newText: String) -> Bool {
        // Method 1: Try setting selected text directly
        if setSelectedText(element: element, text: newText) {
            return true
        }

        // Method 2: Try replacing via range
        if replaceTextViaRange(element: element, newText: newText) {
            return true
        }

        return false
    }

    private static func setSelectedText(element: AXUIElement, text: String) -> Bool {
        let result = AXUIElementSetAttributeValue(
            element,
            kAXSelectedTextAttribute as CFString,
            text as CFTypeRef
        )

        return result == .success
    }

    private static func replaceTextViaRange(element: AXUIElement, newText: String) -> Bool {
        // Get current selection range
        var rangeRef: CFTypeRef?
        let rangeResult = AXUIElementCopyAttributeValue(
            element,
            kAXSelectedTextRangeAttribute as CFString,
            &rangeRef
        )

        guard rangeResult == .success,
              let rangeValue = rangeRef else {
            return false
        }

        var range = CFRange()
        guard AXValueGetValue(rangeValue as! AXValue, .cfRange, &range) else {
            return false
        }

        // Get current text value
        var valueRef: CFTypeRef?
        let valueResult = AXUIElementCopyAttributeValue(
            element,
            kAXValueAttribute as CFString,
            &valueRef
        )

        guard valueResult == .success,
              let currentText = valueRef as? String else {
            return false
        }

        // Build new text with replacement
        let nsString = currentText as NSString
        let newFullText = nsString.replacingCharacters(
            in: NSRange(location: range.location, length: range.length),
            with: newText
        )

        // Set new value
        let setResult = AXUIElementSetAttributeValue(
            element,
            kAXValueAttribute as CFString,
            newFullText as CFTypeRef
        )

        if setResult != .success {
            return false
        }

        // Update selection to end of new text
        let newCursorPosition = range.location + (newText as NSString).length
        let newRange = CFRange(location: newCursorPosition, length: 0)

        if let newRangeValue = AXValueCreate(.cfRange, &newRange) {
            AXUIElementSetAttributeValue(
                element,
                kAXSelectedTextRangeAttribute as CFString,
                newRangeValue
            )
        }

        return true
    }

    /// Fallback replacement using clipboard and paste
    private static func tryClipboardReplacement(newText: String) -> Bool {
        // Save current clipboard
        let pasteboard = NSPasteboard.general
        let previousClipboard = pasteboard.string(forType: .string)

        // Copy new text to clipboard
        pasteboard.clearContents()
        guard pasteboard.setString(newText, forType: .string) else {
            return false
        }

        // Simulate Cmd+V (paste)
        let success = simulatePaste()

        // Restore clipboard if needed
        if let previous = previousClipboard {
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) {
                let pb = NSPasteboard.general
                pb.clearContents()
                pb.setString(previous, forType: .string)
            }
        }

        return success
    }

    private static func simulatePaste() -> Bool {
        let source = CGEventSource(stateID: .hidSystemState)

        // Create key events for Cmd+V
        guard let cmdDown = CGEvent(keyboardEventSource: source, virtualKey: 0x37, keyDown: true),
              let vDown = CGEvent(keyboardEventSource: source, virtualKey: 0x09, keyDown: true),
              let vUp = CGEvent(keyboardEventSource: source, virtualKey: 0x09, keyDown: false),
              let cmdUp = CGEvent(keyboardEventSource: source, virtualKey: 0x37, keyDown: false) else {
            return false
        }

        // Set command flag
        cmdDown.flags = .maskCommand
        vDown.flags = .maskCommand
        vUp.flags = .maskCommand

        // Post events
        let location = CGEventTapLocation.cghidEventTap
        cmdDown.post(tap: location)
        vDown.post(tap: location)
        vUp.post(tap: location)
        cmdUp.post(tap: location)

        return true
    }

    // MARK: - Validation

    /// Check if current element is editable
    static func isCurrentElementEditable() -> Bool {
        guard let element = getFocusedElement() else {
            return false
        }

        return isElementEditable(element)
    }

    private static func isElementEditable(_ element: AXUIElement) -> Bool {
        // Check if element supports value setting
        var settableRef: CFTypeRef?
        let result = AXUIElementCopyAttributeValue(
            element,
            kAXValueAttribute as CFString,
            &settableRef
        )

        guard result == .success else {
            return false
        }

        // Check if value is settable
        var isSettable: DarwinBoolean = false
        AXUIElementIsAttributeSettable(
            element,
            kAXValueAttribute as CFString,
            &isSettable
        )

        return isSettable.boolValue
    }

    // MARK: - Advanced Replacement Methods

    /// Replace text with specified mode
    static func replaceText(
        with newText: String,
        mode: ReplacementMode = .replaceSelection,
        preserveFormatting: Bool = true
    ) throws {
        guard let element = getFocusedElement() else {
            throw ReplacementError.noFocusedElement
        }

        switch mode {
        case .replaceSelection:
            try replaceSelectedText(with: newText)

        case .insertBefore:
            try insertText(newText, at: .before, element: element)

        case .insertAfter:
            try insertText(newText, at: .after, element: element)

        case .replaceParagraph:
            try replaceParagraph(with: newText, element: element)

        case .replaceAll:
            try replaceAllOccurrences(with: newText, element: element)
        }
    }

    // MARK: - Insertion Methods

    private enum InsertionPosition {
        case before
        case after
    }

    private static func insertText(_ text: String, at position: InsertionPosition, element: AXUIElement) throws {
        // Get current selection range
        var rangeRef: CFTypeRef?
        let rangeResult = AXUIElementCopyAttributeValue(
            element,
            kAXSelectedTextRangeAttribute as CFString,
            &rangeRef
        )

        guard rangeResult == .success, let rangeValue = rangeRef else {
            throw ReplacementError.replacementFailed
        }

        var range = CFRange()
        guard AXValueGetValue(rangeValue as! AXValue, .cfRange, &range) else {
            throw ReplacementError.replacementFailed
        }

        // Get current text
        var valueRef: CFTypeRef?
        let valueResult = AXUIElementCopyAttributeValue(
            element,
            kAXValueAttribute as CFString,
            &valueRef
        )

        guard valueResult == .success, let currentText = valueRef as? String else {
            throw ReplacementError.replacementFailed
        }

        // Calculate insertion point
        let insertionPoint = position == .before ? range.location : (range.location + range.length)

        // Build new text
        let nsString = currentText as NSString
        let beforeInsertion = nsString.substring(to: insertionPoint)
        let afterInsertion = nsString.substring(from: insertionPoint)
        let newFullText = beforeInsertion + text + afterInsertion

        // Set new value
        let setResult = AXUIElementSetAttributeValue(
            element,
            kAXValueAttribute as CFString,
            newFullText as CFTypeRef
        )

        guard setResult == .success else {
            throw ReplacementError.replacementFailed
        }

        // Update cursor position
        let newCursorPosition = insertionPoint + (text as NSString).length
        let newRange = CFRange(location: newCursorPosition, length: 0)

        if let newRangeValue = AXValueCreate(.cfRange, &newRange) {
            AXUIElementSetAttributeValue(
                element,
                kAXSelectedTextRangeAttribute as CFString,
                newRangeValue
            )
        }

        // Add to undo stack
        addToUndoStack(originalText: currentText, newText: newFullText, elementInfo: nil)
    }

    private static func replaceParagraph(with newText: String, element: AXUIElement) throws {
        // Get current text and selection
        var valueRef: CFTypeRef?
        let valueResult = AXUIElementCopyAttributeValue(
            element,
            kAXValueAttribute as CFString,
            &valueRef
        )

        guard valueResult == .success, let currentText = valueRef as? String else {
            throw ReplacementError.replacementFailed
        }

        var rangeRef: CFTypeRef?
        let rangeResult = AXUIElementCopyAttributeValue(
            element,
            kAXSelectedTextRangeAttribute as CFString,
            &rangeRef
        )

        guard rangeResult == .success, let rangeValue = rangeRef else {
            throw ReplacementError.replacementFailed
        }

        var range = CFRange()
        guard AXValueGetValue(rangeValue as! AXValue, .cfRange, &range) else {
            throw ReplacementError.replacementFailed
        }

        // Find paragraph boundaries
        let nsString = currentText as NSString
        let paragraphRange = nsString.paragraphRange(for: NSRange(location: range.location, length: range.length))

        // Replace paragraph
        let newFullText = nsString.replacingCharacters(in: paragraphRange, with: newText)

        // Set new value
        let setResult = AXUIElementSetAttributeValue(
            element,
            kAXValueAttribute as CFString,
            newFullText as CFTypeRef
        )

        guard setResult == .success else {
            throw ReplacementError.replacementFailed
        }

        // Add to undo stack
        addToUndoStack(originalText: currentText, newText: newFullText, elementInfo: nil)
    }

    private static func replaceAllOccurrences(with newText: String, element: AXUIElement) throws {
        // Get selected text to find occurrences
        var selectedTextRef: CFTypeRef?
        let selectedResult = AXUIElementCopyAttributeValue(
            element,
            kAXSelectedTextAttribute as CFString,
            &selectedTextRef
        )

        guard selectedResult == .success, let selectedText = selectedTextRef as? String else {
            throw ReplacementError.replacementFailed
        }

        // Get full text
        var valueRef: CFTypeRef?
        let valueResult = AXUIElementCopyAttributeValue(
            element,
            kAXValueAttribute as CFString,
            &valueRef
        )

        guard valueResult == .success, let currentText = valueRef as? String else {
            throw ReplacementError.replacementFailed
        }

        // Replace all occurrences
        let newFullText = currentText.replacingOccurrences(of: selectedText, with: newText)

        // Set new value
        let setResult = AXUIElementSetAttributeValue(
            element,
            kAXValueAttribute as CFString,
            newFullText as CFTypeRef
        )

        guard setResult == .success else {
            throw ReplacementError.replacementFailed
        }

        // Add to undo stack
        addToUndoStack(originalText: currentText, newText: newFullText, elementInfo: nil)
    }

    // MARK: - Undo/Redo Support

    /// Add item to undo stack
    private static func addToUndoStack(originalText: String, newText: String, elementInfo: [String: Any]?) {
        let item = UndoItem(
            originalText: originalText,
            newText: newText,
            timestamp: Date(),
            elementInfo: elementInfo
        )

        undoStack.append(item)

        // Maintain stack size
        if undoStack.count > maxUndoStackSize {
            undoStack.removeFirst()
        }
    }

    /// Undo last text replacement
    static func undoLastReplacement() throws {
        guard let lastItem = undoStack.popLast() else {
            throw ReplacementError.replacementFailed
        }

        guard let element = getFocusedElement() else {
            // Re-add to stack if we can't get element
            undoStack.append(lastItem)
            throw ReplacementError.noFocusedElement
        }

        // Restore original text
        let setResult = AXUIElementSetAttributeValue(
            element,
            kAXValueAttribute as CFString,
            lastItem.originalText as CFTypeRef
        )

        guard setResult == .success else {
            // Re-add to stack if restoration failed
            undoStack.append(lastItem)
            throw ReplacementError.replacementFailed
        }

        showUndoNotification()
    }

    /// Check if undo is available
    static func canUndo() -> Bool {
        return !undoStack.isEmpty
    }

    /// Get undo stack size
    static func undoStackSize() -> Int {
        return undoStack.count
    }

    /// Clear undo stack
    static func clearUndoStack() {
        undoStack.removeAll()
    }

    // MARK: - Formatting Preservation

    /// Try to preserve formatting when replacing text
    static func replaceTextPreservingFormat(original: String, new: String) throws {
        // Detect if text is rich text (has formatting)
        guard let element = getFocusedElement() else {
            throw ReplacementError.noFocusedElement
        }

        // Check if element supports attributed string
        var attributedRef: CFTypeRef?
        let attributedResult = AXUIElementCopyAttributeValue(
            element,
            kAXAttributedStringForRangeParameterizedAttribute as CFString,
            &attributedRef
        )

        if attributedResult == .success {
            // Element supports rich text - try to preserve formatting
            try replaceWithAttributedString(element: element, newText: new)
        } else {
            // Fall back to plain text replacement
            try replaceSelectedText(with: new)
        }
    }

    private static func replaceWithAttributedString(element: AXUIElement, newText: String) throws {
        // Get current selection range
        var rangeRef: CFTypeRef?
        let rangeResult = AXUIElementCopyAttributeValue(
            element,
            kAXSelectedTextRangeAttribute as CFString,
            &rangeRef
        )

        guard rangeResult == .success, let rangeValue = rangeRef else {
            throw ReplacementError.replacementFailed
        }

        var range = CFRange()
        guard AXValueGetValue(rangeValue as! AXValue, .cfRange, &range) else {
            throw ReplacementError.replacementFailed
        }

        // Create attributed string with preserved formatting
        let attributedString = NSMutableAttributedString(string: newText)

        // Try to apply formatting (this is simplified - real implementation would extract original formatting)
        // For now, just use default formatting
        let setResult = AXUIElementSetAttributeValue(
            element,
            kAXSelectedTextAttribute as CFString,
            newText as CFTypeRef
        )

        guard setResult == .success else {
            throw ReplacementError.formattingPreservationFailed
        }
    }

    // MARK: - Helpers

    /// Show notification on replacement success/failure
    static func showReplacementNotification(success: Bool, error: Error? = nil) {
        let notification = NSUserNotification()

        if success {
            notification.title = "Text Replaced"
            notification.informativeText = "Selected text has been updated"
            notification.soundName = NSUserNotificationDefaultSoundName
        } else {
            notification.title = "Replacement Failed"
            notification.informativeText = error?.localizedDescription ?? "Unknown error"
            notification.soundName = nil
        }

        NSUserNotificationCenter.default.deliver(notification)
    }

    /// Show undo notification
    static func showUndoNotification() {
        let notification = NSUserNotification()
        notification.title = "Undone"
        notification.informativeText = "Last text change has been reverted"
        notification.soundName = NSUserNotificationDefaultSoundName
        NSUserNotificationCenter.default.deliver(notification)
    }
}

// MARK: - Extension for Element Info

extension TextReplacer {

    /// Get information about currently focused element for debugging
    static func getFocusedElementInfo() -> [String: Any]? {
        guard let element = getFocusedElement() else {
            return nil
        }

        var info: [String: Any] = [:]

        // Get role
        if let role = getElementAttribute(element, kAXRoleAttribute) as? String {
            info["role"] = role
        }

        // Get subrole
        if let subrole = getElementAttribute(element, kAXSubroleAttribute) as? String {
            info["subrole"] = subrole
        }

        // Get value
        if let value = getElementAttribute(element, kAXValueAttribute) as? String {
            info["value"] = value
        }

        // Check if editable
        info["editable"] = isElementEditable(element)

        return info
    }

    private static func getElementAttribute(_ element: AXUIElement, _ attribute: CFString) -> CFTypeRef? {
        var value: CFTypeRef?
        let result = AXUIElementCopyAttributeValue(element, attribute, &value)
        return result == .success ? value : nil
    }
}
