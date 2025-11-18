//
//  main.swift
//  VoiceAssistant
//
//  Application entry point
//

import Cocoa

// This ensures the app runs as a menu bar app without a dock icon
let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate

// Setup activation policy for menu bar app
app.setActivationPolicy(.accessory)

// Run the application
_ = NSApplicationMain(CommandLine.argc, CommandLine.unsafeArgv)
