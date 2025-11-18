//
//  MenuBarController.swift
//  VoiceAssistant
//
//  Manages menu bar icon and status menu
//

import Cocoa
import SwiftUI

enum AssistantStatus {
    case idle
    case listening
    case processing
    case error(String)

    var iconName: String {
        switch self {
        case .idle:
            return "mic.fill"
        case .listening:
            return "waveform"
        case .processing:
            return "hourglass"
        case .error:
            return "exclamationmark.triangle.fill"
        }
    }

    var color: NSColor {
        switch self {
        case .idle:
            return .systemGray
        case .listening:
            return .systemBlue
        case .processing:
            return .systemOrange
        case .error:
            return .systemRed
        }
    }
}

class MenuBarController: NSObject {

    // MARK: - Properties

    private var statusItem: NSStatusItem!
    private var menu: NSMenu!
    private var currentStatus: AssistantStatus = .idle {
        didSet {
            updateStatusIcon()
        }
    }

    // MARK: - Initialization

    override init() {
        super.init()
        setupStatusItem()
        setupMenu()
        setupObservers()
    }

    deinit {
        NotificationCenter.default.removeObserver(self)
    }

    // MARK: - Setup

    private func setupStatusItem() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)

        if let button = statusItem.button {
            updateStatusIcon()
            button.action = #selector(statusBarButtonClicked)
            button.sendAction(on: [.leftMouseUp, .rightMouseUp])
        }
    }

    private func setupMenu() {
        menu = NSMenu()

        // Status indicator
        let statusMenuItem = NSMenuItem(title: "Status: Idle", action: nil, keyEquivalent: "")
        statusMenuItem.tag = 1000 // Tag to identify for updates
        menu.addItem(statusMenuItem)

        menu.addItem(NSMenuItem.separator())

        // Activate
        let activateItem = NSMenuItem(
            title: "Activate Voice Assistant",
            action: #selector(activateAssistant),
            keyEquivalent: " "
        )
        activateItem.keyEquivalentModifierMask = [.command, .shift]
        activateItem.target = self
        menu.addItem(activateItem)

        menu.addItem(NSMenuItem.separator())

        // Preferences
        let preferencesItem = NSMenuItem(
            title: "Preferences...",
            action: #selector(showPreferences),
            keyEquivalent: ","
        )
        preferencesItem.target = self
        menu.addItem(preferencesItem)

        // About
        let aboutItem = NSMenuItem(
            title: "About Voice Assistant",
            action: #selector(showAbout),
            keyEquivalent: ""
        )
        aboutItem.target = self
        menu.addItem(aboutItem)

        menu.addItem(NSMenuItem.separator())

        // Quit
        let quitItem = NSMenuItem(
            title: "Quit Voice Assistant",
            action: #selector(quitApplication),
            keyEquivalent: "q"
        )
        quitItem.target = self
        menu.addItem(quitItem)
    }

    private func setupObservers() {
        // Listen for status updates from Python service
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(handleStatusUpdate(_:)),
            name: .assistantStatusDidChange,
            object: nil
        )
    }

    // MARK: - Status Icon

    private func updateStatusIcon() {
        guard let button = statusItem.button else { return }

        // Create SF Symbol image
        let config = NSImage.SymbolConfiguration(pointSize: 16, weight: .medium)
        let image = NSImage(systemSymbolName: currentStatus.iconName, accessibilityDescription: nil)?
            .withSymbolConfiguration(config)

        // Tint the image
        image?.isTemplate = true

        button.image = image
        button.contentTintColor = currentStatus.color

        // Update status text in menu
        if let statusMenuItem = menu.item(withTag: 1000) {
            statusMenuItem.title = "Status: \(statusText)"
        }
    }

    private var statusText: String {
        switch currentStatus {
        case .idle:
            return "Idle"
        case .listening:
            return "Listening..."
        case .processing:
            return "Processing..."
        case .error(let message):
            return "Error: \(message)"
        }
    }

    // MARK: - Actions

    @objc private func statusBarButtonClicked() {
        guard let event = NSApp.currentEvent else { return }

        if event.type == .rightMouseUp {
            // Right click - show menu
            statusItem.menu = menu
            statusItem.button?.performClick(nil)
            statusItem.menu = nil
        } else {
            // Left click - activate assistant
            activateAssistant()
        }
    }

    @objc private func activateAssistant() {
        PythonService.shared.startListening()
    }

    @objc private func showPreferences() {
        if let appDelegate = NSApp.delegate as? AppDelegate {
            appDelegate.showPreferences()
        }
    }

    @objc private func showAbout() {
        if let appDelegate = NSApp.delegate as? AppDelegate {
            appDelegate.showAbout()
        }
    }

    @objc private func quitApplication() {
        if let appDelegate = NSApp.delegate as? AppDelegate {
            appDelegate.quitApplication()
        }
    }

    // MARK: - Notifications

    @objc private func handleStatusUpdate(_ notification: Notification) {
        guard let status = notification.object as? AssistantStatus else { return }

        DispatchQueue.main.async { [weak self] in
            self?.currentStatus = status
        }
    }

    // MARK: - Public Methods

    func updateStatus(_ status: AssistantStatus) {
        currentStatus = status
    }
}

// MARK: - Notification Names

extension Notification.Name {
    static let assistantStatusDidChange = Notification.Name("assistantStatusDidChange")
}
