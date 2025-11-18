//
//  AppDelegate.swift
//  VoiceAssistant
//
//  Main application lifecycle management
//

import Cocoa
import ServiceManagement

class AppDelegate: NSObject, NSApplicationDelegate {

    // MARK: - Properties

    private var menuBarController: MenuBarController!
    private var preferencesWindowController: NSWindowController?
    private var aboutWindowController: NSWindowController?

    // MARK: - Application Lifecycle

    func applicationDidFinishLaunching(_ notification: Notification) {
        // Initialize menu bar controller
        menuBarController = MenuBarController()

        // Check and request permissions on first launch
        if !UserDefaults.standard.bool(forKey: "HasLaunchedBefore") {
            UserDefaults.standard.set(true, forKey: "HasLaunchedBefore")
            showInitialPermissionsSetup()
        }

        // Start Python backend service
        PythonService.shared.start()

        // Setup launch at login if enabled
        updateLaunchAtLoginStatus()
    }

    func applicationWillTerminate(_ notification: Notification) {
        // Clean shutdown of Python service
        PythonService.shared.stop()
    }

    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
        if !flag {
            showPreferences()
        }
        return true
    }

    // MARK: - Window Management

    func showPreferences() {
        if preferencesWindowController == nil {
            let preferencesWindow = PreferencesWindow()
            let window = NSWindow(
                contentRect: NSRect(x: 0, y: 0, width: 600, height: 500),
                styleMask: [.titled, .closable, .miniaturizable],
                backing: .buffered,
                defer: false
            )
            window.title = "Voice Assistant Preferences"
            window.contentView = NSHostingView(rootView: preferencesWindow)
            window.center()
            window.setFrameAutosaveName("PreferencesWindow")

            preferencesWindowController = NSWindowController(window: window)
        }

        preferencesWindowController?.showWindow(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    func showAbout() {
        if aboutWindowController == nil {
            let aboutView = AboutView()
            let window = NSWindow(
                contentRect: NSRect(x: 0, y: 0, width: 400, height: 300),
                styleMask: [.titled, .closable],
                backing: .buffered,
                defer: false
            )
            window.title = "About Voice Assistant"
            window.contentView = NSHostingView(rootView: aboutView)
            window.center()

            aboutWindowController = NSWindowController(window: window)
        }

        aboutWindowController?.showWindow(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    func quitApplication() {
        NSApplication.shared.terminate(nil)
    }

    // MARK: - Permissions Setup

    private func showInitialPermissionsSetup() {
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { [weak self] in
            self?.showPreferences()
        }
    }

    // MARK: - Launch at Login

    func updateLaunchAtLoginStatus() {
        let configuration = Configuration.shared

        if #available(macOS 13.0, *) {
            do {
                if configuration.launchAtLogin {
                    try SMAppService.mainApp.register()
                } else {
                    try SMAppService.mainApp.unregister()
                }
            } catch {
                print("Failed to update launch at login status: \(error)")
            }
        }
    }
}

// MARK: - About View

import SwiftUI

struct AboutView: View {
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "mic.fill")
                .resizable()
                .frame(width: 64, height: 64)
                .foregroundColor(.blue)

            Text("Voice Assistant for macOS")
                .font(.title2)
                .fontWeight(.bold)

            Text("Version 1.0.0")
                .font(.subheadline)
                .foregroundColor(.secondary)

            VStack(alignment: .leading, spacing: 8) {
                Text("Privacy-first voice assistant with local AI processing")
                    .font(.body)
                Text("Powered by whisper.cpp and gpt-oss")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .multilineTextAlignment(.center)
            .padding()

            Spacer()

            Text("© 2025 · Open Source (Apache 2.0)")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding()
        .frame(width: 400, height: 300)
    }
}
