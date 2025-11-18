//
//  SelectionMonitor.swift
//  VoiceAssistant
//
//  Monitors text selections across all applications using macOS Accessibility API
//

import Foundation
import Cocoa
import ApplicationServices

// MARK: - Selection Event

struct TextSelectionEvent {
    let selectedText: String
    let applicationName: String
    let applicationBundleId: String?
    let selectionFrame: CGRect
    let timestamp: Date
}

// MARK: - Selection Monitor Protocol

protocol SelectionMonitorDelegate: AnyObject {
    func didDetectTextSelection(_ event: TextSelectionEvent)
    func didClearSelection()
}

// MARK: - Selection Monitor

class SelectionMonitor {

    // MARK: - Properties

    static let shared = SelectionMonitor()

    weak var delegate: SelectionMonitorDelegate?

    private var isMonitoring = false
    private var monitorTimer: Timer?
    private var lastSelectedText: String?
    private var selectionCheckInterval: TimeInterval = 0.3 // Check every 300ms

    private var currentFocusedElement: AXUIElement?
    private var currentApplication: NSRunningApplication?

    // MARK: - Initialization

    private init() {}

    // MARK: - Monitoring Control

    func startMonitoring() {
        guard !isMonitoring else {
            print("SelectionMonitor: Already monitoring")
            return
        }

        // Check for Accessibility permission
        guard checkAccessibilityPermission() else {
            print("SelectionMonitor: Accessibility permission not granted")
            NotificationCenter.default.post(name: .accessibilityPermissionRequired, object: nil)
            return
        }

        isMonitoring = true

        // Start timer to periodically check for selections
        monitorTimer = Timer.scheduledTimer(
            withTimeInterval: selectionCheckInterval,
            repeats: true
        ) { [weak self] _ in
            self?.checkForTextSelection()
        }

        print("SelectionMonitor: Started monitoring text selections")
    }

    func stopMonitoring() {
        guard isMonitoring else { return }

        monitorTimer?.invalidate()
        monitorTimer = nil
        isMonitoring = false
        lastSelectedText = nil
        currentFocusedElement = nil
        currentApplication = nil

        print("SelectionMonitor: Stopped monitoring")
    }

    // MARK: - Permission Check

    func checkAccessibilityPermission() -> Bool {
        let options = [kAXTrustedCheckOptionPrompt.takeUnretainedValue() as String: false]
        return AXIsProcessTrustedWithOptions(options as CFDictionary)
    }

    func requestAccessibilityPermission() {
        let options = [kAXTrustedCheckOptionPrompt.takeUnretainedValue() as String: true]
        _ = AXIsProcessTrustedWithOptions(options as CFDictionary)
    }

    // MARK: - Selection Detection

    private func checkForTextSelection() {
        autoreleasepool {
            // Get currently focused application
            guard let activeApp = NSWorkspace.shared.frontmostApplication else {
                return
            }

            // Get focused UI element
            let systemWideElement = AXUIElementCreateSystemWide()
            var focusedElement: CFTypeRef?

            let result = AXUIElementCopyAttributeValue(
                systemWideElement,
                kAXFocusedUIElementAttribute as CFString,
                &focusedElement
            )

            guard result == .success,
                  let element = focusedElement else {
                return
            }

            let axElement = element as! AXUIElement

            // Try to get selected text
            if let selectedText = getSelectedText(from: axElement),
               !selectedText.isEmpty,
               selectedText != lastSelectedText {

                // Get selection bounds for UI positioning
                let selectionFrame = getSelectionFrame(from: axElement)

                // Create selection event
                let event = TextSelectionEvent(
                    selectedText: selectedText,
                    applicationName: activeApp.localizedName ?? "Unknown",
                    applicationBundleId: activeApp.bundleIdentifier,
                    selectionFrame: selectionFrame,
                    timestamp: Date()
                )

                lastSelectedText = selectedText
                currentFocusedElement = axElement
                currentApplication = activeApp

                // Notify delegate on main thread
                DispatchQueue.main.async { [weak self] in
                    self?.delegate?.didDetectTextSelection(event)
                }

            } else if selectedText?.isEmpty ?? true,
                      lastSelectedText != nil {
                // Selection was cleared
                lastSelectedText = nil
                currentFocusedElement = nil

                DispatchQueue.main.async { [weak self] in
                    self?.delegate?.didClearSelection()
                }
            }
        }
    }

    // MARK: - Text Extraction

    private func getSelectedText(from element: AXUIElement) -> String? {
        // Try to get selected text directly
        var selectedTextValue: CFTypeRef?
        let result = AXUIElementCopyAttributeValue(
            element,
            kAXSelectedTextAttribute as CFString,
            &selectedTextValue
        )

        if result == .success,
           let text = selectedTextValue as? String,
           !text.isEmpty {
            return text
        }

        // Fallback: Try to get text from value attribute with selection range
        return getSelectedTextViaRange(from: element)
    }

    private func getSelectedTextViaRange(from element: AXUIElement) -> String? {
        // Get full text value
        var valueRef: CFTypeRef?
        let valueResult = AXUIElementCopyAttributeValue(
            element,
            kAXValueAttribute as CFString,
            &valueRef
        )

        guard valueResult == .success,
              let fullText = valueRef as? String else {
            return nil
        }

        // Get selected text range
        var rangeRef: CFTypeRef?
        let rangeResult = AXUIElementCopyAttributeValue(
            element,
            kAXSelectedTextRangeAttribute as CFString,
            &rangeRef
        )

        guard rangeResult == .success,
              let rangeValue = rangeRef else {
            return nil
        }

        // Extract range
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

        // Extract selected text
        let nsString = fullText as NSString
        return nsString.substring(with: NSRange(location: range.location, length: range.length))
    }

    private func getSelectionFrame(from element: AXUIElement) -> CGRect {
        // Try to get position
        var positionRef: CFTypeRef?
        var sizeRef: CFTypeRef?

        AXUIElementCopyAttributeValue(
            element,
            kAXPositionAttribute as CFString,
            &positionRef
        )

        AXUIElementCopyAttributeValue(
            element,
            kAXSizeAttribute as CFString,
            &sizeRef
        )

        var position = CGPoint.zero
        var size = CGSize.zero

        if let positionValue = positionRef {
            AXValueGetValue(positionValue as! AXValue, .cgPoint, &position)
        }

        if let sizeValue = sizeRef {
            AXValueGetValue(sizeValue as! AXValue, .cgSize, &size)
        }

        // If we got valid bounds, try to get selected text bounds
        // For now, return element bounds as approximation
        return CGRect(origin: position, size: size)
    }

    // MARK: - Public Helpers

    func getCurrentSelection() -> TextSelectionEvent? {
        guard let text = lastSelectedText,
              let app = currentApplication else {
            return nil
        }

        let frame = currentFocusedElement != nil ?
            getSelectionFrame(from: currentFocusedElement!) :
            CGRect.zero

        return TextSelectionEvent(
            selectedText: text,
            applicationName: app.localizedName ?? "Unknown",
            applicationBundleId: app.bundleIdentifier,
            selectionFrame: frame,
            timestamp: Date()
        )
    }
}

// MARK: - Notifications

extension Notification.Name {
    static let accessibilityPermissionRequired = Notification.Name("accessibilityPermissionRequired")
}
