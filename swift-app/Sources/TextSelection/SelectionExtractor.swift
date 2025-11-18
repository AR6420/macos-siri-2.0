//
//  SelectionExtractor.swift
//  VoiceAssistant
//
//  Utility functions for extracting selected text from various applications
//

import Foundation
import Cocoa
import ApplicationServices

class SelectionExtractor {

    // MARK: - Static Methods

    /// Extract selected text from the currently focused application
    static func extractSelectedText() -> String? {
        // Get system-wide UI element
        let systemWideElement = AXUIElementCreateSystemWide()

        // Get focused UI element
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

        return extractSelectedText(from: element)
    }

    /// Extract selected text from a specific UI element
    static func extractSelectedText(from element: AXUIElement) -> String? {
        // Method 1: Try kAXSelectedTextAttribute
        if let text = getAttributeValue(element, kAXSelectedTextAttribute) as? String,
           !text.isEmpty {
            return text.trimmingCharacters(in: .whitespacesAndNewlines)
        }

        // Method 2: Try getting range-based selection
        if let text = extractSelectedTextViaRange(from: element) {
            return text.trimmingCharacters(in: .whitespacesAndNewlines)
        }

        // Method 3: Try clipboard as fallback (requires Cmd+C)
        // Note: This is a last resort and may not be reliable
        return nil
    }

    /// Extract selected text using range-based approach
    private static func extractSelectedTextViaRange(from element: AXUIElement) -> String? {
        // Get full text value
        guard let fullText = getAttributeValue(element, kAXValueAttribute) as? String else {
            return nil
        }

        // Get selected text range
        guard let rangeValue = getAttributeValue(element, kAXSelectedTextRangeAttribute) else {
            return nil
        }

        var range = CFRange()
        guard AXValueGetValue(rangeValue as! AXValue, .cfRange, &range) else {
            return nil
        }

        // Validate range
        guard range.location >= 0,
              range.length > 0,
              range.location + range.length <= fullText.count else {
            return nil
        }

        // Extract substring
        let nsString = fullText as NSString
        return nsString.substring(with: NSRange(location: range.location, length: range.length))
    }

    /// Get attribute value from UI element
    private static func getAttributeValue(_ element: AXUIElement, _ attribute: CFString) -> CFTypeRef? {
        var value: CFTypeRef?
        let result = AXUIElementCopyAttributeValue(element, attribute, &value)
        return result == .success ? value : nil
    }

    // MARK: - Clipboard Fallback

    /// Extract text from clipboard (fallback method)
    static func extractFromClipboard() -> String? {
        guard let clipboardContent = NSPasteboard.general.string(forType: .string),
              !clipboardContent.isEmpty else {
            return nil
        }

        return clipboardContent.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    /// Copy current selection to clipboard and extract
    /// Note: This simulates Cmd+C keystroke
    static func copySelectionToClipboard() -> String? {
        // Store current clipboard content
        let previousClipboard = NSPasteboard.general.string(forType: .string)

        // Clear clipboard
        NSPasteboard.general.clearContents()

        // Simulate Cmd+C
        let source = CGEventSource(stateID: .hidSystemState)

        // Key down: Command
        let cmdDown = CGEvent(keyboardEventSource: source, virtualKey: 0x37, keyDown: true)
        cmdDown?.flags = .maskCommand

        // Key down: C
        let cDown = CGEvent(keyboardEventSource: source, virtualKey: 0x08, keyDown: true)
        cDown?.flags = .maskCommand

        // Key up: C
        let cUp = CGEvent(keyboardEventSource: source, virtualKey: 0x08, keyDown: false)
        cUp?.flags = .maskCommand

        // Key up: Command
        let cmdUp = CGEvent(keyboardEventSource: source, virtualKey: 0x37, keyDown: false)

        // Post events
        let location = CGEventTapLocation.cghidEventTap
        cmdDown?.post(tap: location)
        cDown?.post(tap: location)
        cUp?.post(tap: location)
        cmdUp?.post(tap: location)

        // Wait for clipboard update
        Thread.sleep(forTimeInterval: 0.1)

        // Get new clipboard content
        let selectedText = NSPasteboard.general.string(forType: .string)

        // Restore previous clipboard if nothing was copied
        if selectedText == nil || selectedText?.isEmpty == true {
            if let previous = previousClipboard {
                NSPasteboard.general.clearContents()
                NSPasteboard.general.setString(previous, forType: .string)
            }
            return nil
        }

        return selectedText?.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    // MARK: - Position Helpers

    /// Get the screen position of selected text
    static func getSelectionPosition(from element: AXUIElement) -> CGRect? {
        var positionRef: CFTypeRef?
        var sizeRef: CFTypeRef?

        let posResult = AXUIElementCopyAttributeValue(
            element,
            kAXPositionAttribute as CFString,
            &positionRef
        )

        let sizeResult = AXUIElementCopyAttributeValue(
            element,
            kAXSizeAttribute as CFString,
            &sizeRef
        )

        guard posResult == .success,
              sizeResult == .success,
              let posValue = positionRef,
              let sizeValue = sizeRef else {
            return nil
        }

        var position = CGPoint.zero
        var size = CGSize.zero

        guard AXValueGetValue(posValue as! AXValue, .cgPoint, &position),
              AXValueGetValue(sizeValue as! AXValue, .cgSize, &size) else {
            return nil
        }

        return CGRect(origin: position, size: size)
    }

    /// Get cursor position in currently focused element
    static func getCursorPosition() -> CGPoint? {
        let systemWideElement = AXUIElementCreateSystemWide()

        var focusedElement: CFTypeRef?
        guard AXUIElementCopyAttributeValue(
            systemWideElement,
            kAXFocusedUIElementAttribute as CFString,
            &focusedElement
        ) == .success,
              let element = focusedElement as? AXUIElement else {
            return nil
        }

        return getSelectionPosition(from: element)?.origin
    }
}
