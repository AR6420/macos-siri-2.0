//
//  TextReplacer.swift
//  VoiceAssistant
//
//  Replaces selected text using macOS Accessibility API
//

import Foundation
import Cocoa
import ApplicationServices

class TextReplacer {

    // MARK: - Error Types

    enum ReplacementError: Error {
        case noFocusedElement
        case accessibilityDenied
        case replacementFailed
        case clipboardFailed
        case invalidElement

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
            }
        }
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
