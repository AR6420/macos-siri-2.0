//
//  PermissionManager.swift
//  VoiceAssistant
//
//  Manages macOS permissions (Microphone, Accessibility, Input Monitoring, Full Disk Access)
//

import Cocoa
import AVFoundation
import ApplicationServices

enum PermissionType {
    case microphone
    case accessibility
    case inputMonitoring
    case fullDiskAccess

    var displayName: String {
        switch self {
        case .microphone:
            return "Microphone"
        case .accessibility:
            return "Accessibility"
        case .inputMonitoring:
            return "Input Monitoring"
        case .fullDiskAccess:
            return "Full Disk Access"
        }
    }

    var usageDescription: String {
        switch self {
        case .microphone:
            return "Voice Assistant needs microphone access to listen for wake word and voice commands."
        case .accessibility:
            return "Voice Assistant needs accessibility access to control applications and automate tasks."
        case .inputMonitoring:
            return "Voice Assistant needs input monitoring to detect the activation hotkey (Cmd+Shift+Space)."
        case .fullDiskAccess:
            return "Voice Assistant needs full disk access to send messages via the Messages app (optional)."
        }
    }
}

enum PermissionStatus {
    case notDetermined
    case denied
    case authorized
    case restricted
}

class PermissionManager: ObservableObject {

    // MARK: - Singleton

    static let shared = PermissionManager()

    // MARK: - Published Properties

    @Published var microphoneStatus: PermissionStatus = .notDetermined
    @Published var accessibilityStatus: PermissionStatus = .notDetermined
    @Published var inputMonitoringStatus: PermissionStatus = .notDetermined
    @Published var fullDiskAccessStatus: PermissionStatus = .notDetermined

    // MARK: - Initialization

    private init() {
        refreshAllPermissions()
    }

    // MARK: - Refresh All

    func refreshAllPermissions() {
        microphoneStatus = checkMicrophonePermission()
        accessibilityStatus = checkAccessibilityPermission()
        inputMonitoringStatus = checkInputMonitoringPermission()
        fullDiskAccessStatus = checkFullDiskAccessPermission()
    }

    // MARK: - Microphone Permission

    func checkMicrophonePermission() -> PermissionStatus {
        switch AVCaptureDevice.authorizationStatus(for: .audio) {
        case .notDetermined:
            return .notDetermined
        case .denied, .restricted:
            return .denied
        case .authorized:
            return .authorized
        @unknown default:
            return .notDetermined
        }
    }

    func requestMicrophonePermission(completion: @escaping (Bool) -> Void) {
        AVCaptureDevice.requestAccess(for: .audio) { [weak self] granted in
            DispatchQueue.main.async {
                self?.microphoneStatus = granted ? .authorized : .denied
                completion(granted)
            }
        }
    }

    // MARK: - Accessibility Permission

    func checkAccessibilityPermission() -> PermissionStatus {
        let options: NSDictionary = [kAXTrustedCheckOptionPrompt.takeRetainedValue() as String: false]
        let accessEnabled = AXIsProcessTrustedWithOptions(options)
        return accessEnabled ? .authorized : .denied
    }

    func requestAccessibilityPermission() {
        let options: NSDictionary = [kAXTrustedCheckOptionPrompt.takeRetainedValue() as String: true]
        _ = AXIsProcessTrustedWithOptions(options)

        // Open System Preferences to Privacy & Security > Accessibility
        if let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility") {
            NSWorkspace.shared.open(url)
        }
    }

    // MARK: - Input Monitoring Permission

    func checkInputMonitoringPermission() -> PermissionStatus {
        // Input Monitoring is checked by attempting to monitor events
        // If we can get the current keyboard modifier state, we have permission
        let eventSource = CGEventSource(stateID: .hidSystemState)

        if eventSource != nil {
            // Try to create an event monitor
            let canMonitor = CGEvent.tapCreate(
                tap: .cgSessionEventTap,
                place: .headInsertEventTap,
                options: .listenOnly,
                eventsOfInterest: CGEventMask(1 << CGEventType.keyDown.rawValue),
                callback: { _, _, _, _ in return nil },
                userInfo: nil
            ) != nil

            return canMonitor ? .authorized : .denied
        }

        return .denied
    }

    func requestInputMonitoringPermission() {
        // Open System Preferences to Privacy & Security > Input Monitoring
        if let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_ListenEvent") {
            NSWorkspace.shared.open(url)
        }

        // Show alert explaining the user needs to manually enable this
        showInputMonitoringAlert()
    }

    private func showInputMonitoringAlert() {
        let alert = NSAlert()
        alert.messageText = "Input Monitoring Permission Required"
        alert.informativeText = """
        Voice Assistant needs Input Monitoring permission to detect the hotkey (Cmd+Shift+Space).

        Please:
        1. Open System Settings > Privacy & Security > Input Monitoring
        2. Enable Voice Assistant
        3. Restart the app
        """
        alert.alertStyle = .informational
        alert.addButton(withTitle: "Open System Settings")
        alert.addButton(withTitle: "Cancel")

        if alert.runModal() == .alertFirstButtonReturn {
            if let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_ListenEvent") {
                NSWorkspace.shared.open(url)
            }
        }
    }

    // MARK: - Full Disk Access Permission

    func checkFullDiskAccessPermission() -> PermissionStatus {
        // Check if we can access Messages database
        let messagesDbPath = FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent("Library/Messages/chat.db")

        let fileManager = FileManager.default

        // Try to check if file is readable
        if fileManager.fileExists(atPath: messagesDbPath.path) {
            return fileManager.isReadableFile(atPath: messagesDbPath.path) ? .authorized : .denied
        }

        return .denied
    }

    func requestFullDiskAccessPermission() {
        // Open System Preferences to Privacy & Security > Full Disk Access
        if let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles") {
            NSWorkspace.shared.open(url)
        }

        // Show alert explaining the user needs to manually enable this
        showFullDiskAccessAlert()
    }

    private func showFullDiskAccessAlert() {
        let alert = NSAlert()
        alert.messageText = "Full Disk Access Permission (Optional)"
        alert.informativeText = """
        Voice Assistant needs Full Disk Access to send messages via the Messages app.

        This permission is optional but required for messaging features.

        Please:
        1. Open System Settings > Privacy & Security > Full Disk Access
        2. Click the + button and add Voice Assistant
        3. Restart the app
        """
        alert.alertStyle = .informational
        alert.addButton(withTitle: "Open System Settings")
        alert.addButton(withTitle: "Skip")

        if alert.runModal() == .alertFirstButtonReturn {
            if let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles") {
                NSWorkspace.shared.open(url)
            }
        }
    }

    // MARK: - Permission Status Helpers

    func isPermissionGranted(_ type: PermissionType) -> Bool {
        let status: PermissionStatus

        switch type {
        case .microphone:
            status = microphoneStatus
        case .accessibility:
            status = accessibilityStatus
        case .inputMonitoring:
            status = inputMonitoringStatus
        case .fullDiskAccess:
            status = fullDiskAccessStatus
        }

        return status == .authorized
    }

    func allRequiredPermissionsGranted() -> Bool {
        return microphoneStatus == .authorized &&
               accessibilityStatus == .authorized
    }

    func allPermissionsGranted() -> Bool {
        return microphoneStatus == .authorized &&
               accessibilityStatus == .authorized &&
               inputMonitoringStatus == .authorized &&
               fullDiskAccessStatus == .authorized
    }
}
