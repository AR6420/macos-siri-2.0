//
//  InlineAIController.swift
//  VoiceAssistant
//
//  Coordinates all inline AI components and manages the workflow
//

import Foundation
import Cocoa

// MARK: - Inline AI Status

enum InlineAIStatus {
    case idle
    case monitoring
    case showingButton
    case showingPanel
    case processing
    case replacing
    case error(String)
}

// MARK: - Inline AI Controller Delegate

protocol InlineAIControllerDelegate: AnyObject {
    func inlineAIStatusDidChange(_ status: InlineAIStatus)
    func inlineAIDidComplete(originalText: String, processedText: String)
    func inlineAIDidFail(error: Error)
}

// MARK: - Inline AI Controller

class InlineAIController: NSObject {

    // MARK: - Singleton

    static let shared = InlineAIController()

    // MARK: - Properties

    weak var delegate: InlineAIControllerDelegate?

    private let selectionMonitor = SelectionMonitor.shared
    private var selectionButton: SelectionButtonWindow?
    private var enhancedPanel: EnhancedFloatingPanelWindow?

    // Legacy panel (deprecated but kept for compatibility)
    private var floatingPanel: FloatingPanelWindow?

    private var currentSelection: TextSelectionEvent?
    private var currentStatus: InlineAIStatus = .idle {
        didSet {
            delegate?.inlineAIStatusDidChange(currentStatus)
        }
    }

    private var isEnabled = false
    private var showOnHover = true
    private var useEnhancedUI = true // Toggle for new UI

    // MARK: - Initialization

    private override init() {
        super.init()
        setupSelectionMonitor()
    }

    // MARK: - Public Methods

    func enable() {
        guard !isEnabled else { return }

        isEnabled = true
        selectionMonitor.startMonitoring()
        currentStatus = .monitoring

        print("InlineAIController: Enabled")
    }

    func disable() {
        guard isEnabled else { return }

        isEnabled = false
        selectionMonitor.stopMonitoring()
        dismissPanel()
        currentStatus = .idle

        print("InlineAIController: Disabled")
    }

    func configure(showOnHover: Bool, useEnhancedUI: Bool = true) {
        self.showOnHover = showOnHover
        self.useEnhancedUI = useEnhancedUI
    }

    // MARK: - Selection Monitor Setup

    private func setupSelectionMonitor() {
        selectionMonitor.delegate = self
    }

    // MARK: - Panel Management

    private func showPanel(for selection: TextSelectionEvent) {
        // Dismiss any existing UI
        dismissPanel()
        dismissButton()

        // Store current selection
        currentSelection = selection

        if useEnhancedUI {
            // Show selection button (new UI)
            showButton(for: selection)
        } else {
            // Show legacy floating panel
            showLegacyPanel(for: selection)
        }
    }

    private func showButton(for selection: TextSelectionEvent) {
        let button = SelectionButtonWindow(at: selection.selectionFrame.origin)
        button.buttonDelegate = self
        selectionButton = button

        currentStatus = .showingButton

        print("InlineAIController: Showing selection button for text: \(selection.selectedText.prefix(50))...")
    }

    private func showEnhancedPanel(at position: CGPoint) {
        guard let selection = currentSelection else { return }

        // Dismiss button
        dismissButton()

        // Create enhanced panel
        let panel = EnhancedFloatingPanelWindow(
            at: position,
            selectedText: selection.selectedText
        )

        panel.panelDelegate = self
        enhancedPanel = panel

        currentStatus = .showingPanel

        print("InlineAIController: Showing enhanced panel")
    }

    private func showLegacyPanel(for selection: TextSelectionEvent) {
        let panel = FloatingPanelWindow(
            at: selection.selectionFrame.origin,
            selectedText: selection.selectedText
        )

        panel.panelDelegate = self
        floatingPanel = panel

        // Show panel
        panel.orderFront(nil)
        currentStatus = .showingPanel

        print("InlineAIController: Showing legacy panel for text: \(selection.selectedText.prefix(50))...")
    }

    private func dismissPanel() {
        floatingPanel?.dismiss()
        floatingPanel = nil

        enhancedPanel?.dismiss()
        enhancedPanel = nil

        if currentStatus == .showingPanel {
            currentStatus = .monitoring
        }
    }

    private func dismissButton() {
        selectionButton?.dismiss()
        selectionButton = nil

        if currentStatus == .showingButton {
            currentStatus = .monitoring
        }
    }

    // MARK: - Text Processing

    private func processMenuOption(_ option: MenuOption, customInput: String?) {
        guard let selection = currentSelection else {
            print("InlineAIController: No selection available")
            return
        }

        currentStatus = .processing

        // Generate command based on option
        var command = option.generateCommand(for: selection.selectedText, customInput: customInput)

        // Send to Python backend
        PythonService.shared.sendCommand(command)

        print("InlineAIController: Sent command: \(option.displayName)")
    }

    // MARK: - Legacy Processing Methods (for backwards compatibility)

    private func processRewrite(tone: ToneType) {
        guard let selection = currentSelection else {
            print("InlineAIController: No selection available")
            return
        }

        currentStatus = .processing

        // Send rewrite request to Python backend
        let command: [String: Any] = [
            "command": "rewrite_text",
            "text": selection.selectedText,
            "tone": tone.rawValue
        ]

        PythonService.shared.sendCommand(command)

        print("InlineAIController: Sent rewrite request with tone: \(tone.rawValue)")
    }

    private func processSummarize() {
        guard let selection = currentSelection else {
            print("InlineAIController: No selection available")
            return
        }

        currentStatus = .processing

        // Send summarize request to Python backend
        let command: [String: Any] = [
            "command": "summarize_text",
            "text": selection.selectedText
        ]

        PythonService.shared.sendCommand(command)

        print("InlineAIController: Sent summarize request")
    }

    // MARK: - Text Replacement

    func handleRewriteComplete(original: String, rewritten: String) {
        guard original == currentSelection?.selectedText else {
            print("InlineAIController: Text mismatch, ignoring result")
            return
        }

        currentStatus = .replacing

        // Replace text in application
        do {
            try TextReplacer.replaceSelectedTextWithUndo(
                originalText: original,
                newText: rewritten
            )

            TextReplacer.showReplacementNotification(success: true)
            delegate?.inlineAIDidComplete(originalText: original, processedText: rewritten)

            print("InlineAIController: Text replaced successfully")

        } catch {
            print("InlineAIController: Text replacement failed - \(error)")
            TextReplacer.showReplacementNotification(success: false, error: error)

            currentStatus = .error(error.localizedDescription)
            delegate?.inlineAIDidFail(error: error)
        }

        // Reset to monitoring
        currentSelection = nil
        currentStatus = .monitoring
    }

    func handleSummarizeComplete(original: String, summary: String) {
        guard original == currentSelection?.selectedText else {
            print("InlineAIController: Text mismatch, ignoring result")
            return
        }

        currentStatus = .replacing

        // Replace text with summary
        do {
            try TextReplacer.replaceSelectedTextWithUndo(
                originalText: original,
                newText: summary
            )

            TextReplacer.showReplacementNotification(success: true)
            delegate?.inlineAIDidComplete(originalText: original, processedText: summary)

            print("InlineAIController: Text summarized and replaced successfully")

        } catch {
            print("InlineAIController: Text replacement failed - \(error)")
            TextReplacer.showReplacementNotification(success: false, error: error)

            currentStatus = .error(error.localizedDescription)
            delegate?.inlineAIDidFail(error: error)
        }

        // Reset to monitoring
        currentSelection = nil
        currentStatus = .monitoring
    }

    func handleInlineAIError(error: String) {
        print("InlineAIController: Backend error - \(error)")

        currentStatus = .error(error)

        // Show notification
        let notification = NSUserNotification()
        notification.title = "Inline AI Error"
        notification.informativeText = error
        NSUserNotificationCenter.default.deliver(notification)

        // Reset to monitoring
        currentSelection = nil
        currentStatus = .monitoring
    }
}

// MARK: - Selection Monitor Delegate

extension InlineAIController: SelectionMonitorDelegate {

    func didDetectTextSelection(_ event: TextSelectionEvent) {
        guard isEnabled, showOnHover else { return }

        // Only show panel if text is long enough (at least 3 characters)
        guard event.selectedText.count >= 3 else { return }

        // Show panel for this selection
        showPanel(for: event)
    }

    func didClearSelection() {
        // Dismiss panel when selection is cleared
        dismissPanel()
    }
}

// MARK: - Selection Button Delegate

extension InlineAIController: SelectionButtonDelegate {

    func selectionButtonDidClick(at position: CGPoint) {
        showEnhancedPanel(at: position)
    }
}

// MARK: - Enhanced Floating Panel Delegate

extension InlineAIController: EnhancedFloatingPanelDelegate {

    func didSelectOption(_ option: MenuOption, customInput: String?) {
        processMenuOption(option, customInput: customInput)
    }

    func didDismissPanel() {
        dismissPanel()
    }
}

// MARK: - Legacy Floating Panel Delegate

extension InlineAIController: FloatingPanelDelegate {

    func didSelectRewrite(tone: ToneType) {
        processRewrite(tone: tone)
    }

    func didSelectSummarize() {
        processSummarize()
    }

    func didDismissPanel() {
        dismissPanel()
    }
}

// MARK: - Notification Names

extension Notification.Name {
    static let inlineAIStatusDidChange = Notification.Name("inlineAIStatusDidChange")
    static let inlineAIDidComplete = Notification.Name("inlineAIDidComplete")
    static let inlineAIDidFail = Notification.Name("inlineAIDidFail")
}

// MARK: - Helper Extension for PythonService

extension PythonService {
    func sendCommand(_ command: [String: Any]) {
        guard let inputPipe = self.value(forKey: "inputPipe") as? Pipe,
              let jsonData = try? JSONSerialization.data(withJSONObject: command),
              var jsonString = String(data: jsonData, encoding: .utf8) else {
            print("Failed to encode command")
            return
        }

        jsonString += "\n"

        if let data = jsonString.data(using: .utf8) {
            inputPipe.fileHandleForWriting.write(data)
        }
    }
}
