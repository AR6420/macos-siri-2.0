//
//  PythonService.swift
//  VoiceAssistant
//
//  XPC service for communication with Python backend
//

import Foundation
import Cocoa

// MARK: - Service Protocol

protocol VoiceAssistantServiceProtocol {
    func start()
    func stop()
    func startListening()
    func stopListening()
    func getStatus() -> String
    func updateConfig(_ config: [String: Any])
}

// MARK: - Delegate Protocol

protocol VoiceAssistantDelegate: AnyObject {
    func didStartListening()
    func didDetectWakeWord()
    func didReceiveTranscription(_ text: String)
    func didReceiveResponse(_ text: String)
    func didEncounterError(_ error: String)
    func didChangeStatus(_ status: AssistantStatus)
}

// MARK: - Python Service

@MainActor
class PythonService: NSObject, VoiceAssistantServiceProtocol {

    // MARK: - Singleton

    static let shared = PythonService()

    // MARK: - Properties

    private var process: Process?
    private var inputPipe: Pipe?
    private var outputPipe: Pipe?
    private var errorPipe: Pipe?

    weak var delegate: VoiceAssistantDelegate?

    private var isRunning = false
    private var currentStatus: AssistantStatus = .idle {
        didSet {
            NotificationCenter.default.post(
                name: .assistantStatusDidChange,
                object: currentStatus
            )
            delegate?.didChangeStatus(currentStatus)
        }
    }

    // MARK: - Paths

    private var pythonExecutablePath: String {
        // First, try to find Python in common locations
        let paths = [
            "/usr/local/bin/python3",
            "/opt/homebrew/bin/python3",
            "/usr/bin/python3",
            Bundle.main.bundlePath + "/Contents/Resources/python3"
        ]

        for path in paths {
            if FileManager.default.fileExists(atPath: path) {
                return path
            }
        }

        return "/usr/bin/python3" // Fallback
    }

    private var pythonServicePath: String {
        // Path to Python service main.py
        let bundlePath = Bundle.main.bundlePath
        let resourcePath = bundlePath + "/Contents/Resources/python-service"

        // In development, use relative path
        if !FileManager.default.fileExists(atPath: resourcePath) {
            // Development path
            let devPath = FileManager.default.currentDirectoryPath + "/../python-service"
            return devPath
        }

        return resourcePath
    }

    // MARK: - Initialization

    private override init() {
        super.init()
    }

    // MARK: - Service Control

    func start() {
        guard !isRunning else {
            print("Python service already running")
            return
        }

        do {
            try startPythonProcess()
            isRunning = true
            print("Python service started successfully")
        } catch {
            print("Failed to start Python service: \(error)")
            currentStatus = .error("Failed to start backend service")
        }
    }

    func stop() {
        guard isRunning else { return }

        process?.terminate()
        process?.waitUntilExit()
        process = nil

        isRunning = false
        currentStatus = .idle
        print("Python service stopped")
    }

    private func startPythonProcess() throws {
        process = Process()
        inputPipe = Pipe()
        outputPipe = Pipe()
        errorPipe = Pipe()

        guard let process = process,
              let inputPipe = inputPipe,
              let outputPipe = outputPipe,
              let errorPipe = errorPipe else {
            throw NSError(domain: "PythonService", code: 1, userInfo: [
                NSLocalizedDescriptionKey: "Failed to create process or pipes"
            ])
        }

        // Configure process
        process.executableURL = URL(fileURLWithPath: pythonExecutablePath)
        process.arguments = [
            "-m", "voice_assistant.main",
            "--config", Configuration.shared.exportConfigPath()
        ]
        process.currentDirectoryURL = URL(fileURLWithPath: pythonServicePath)

        process.standardInput = inputPipe
        process.standardOutput = outputPipe
        process.standardError = errorPipe

        // Setup environment
        var environment = ProcessInfo.processInfo.environment
        environment["PYTHONUNBUFFERED"] = "1"

        // Add API keys from Keychain
        if let openAIKey = KeychainManager.retrieve(key: "OPENAI_API_KEY") {
            environment["OPENAI_API_KEY"] = openAIKey
        }
        if let anthropicKey = KeychainManager.retrieve(key: "ANTHROPIC_API_KEY") {
            environment["ANTHROPIC_API_KEY"] = anthropicKey
        }
        if let openRouterKey = KeychainManager.retrieve(key: "OPENROUTER_API_KEY") {
            environment["OPENROUTER_API_KEY"] = openRouterKey
        }
        if let porcupineKey = KeychainManager.retrieve(key: "PORCUPINE_ACCESS_KEY") {
            environment["PORCUPINE_ACCESS_KEY"] = porcupineKey
        }

        process.environment = environment

        // Setup output monitoring
        setupOutputMonitoring()

        // Start process
        try process.run()
    }

    private func setupOutputMonitoring() {
        guard let outputPipe = outputPipe,
              let errorPipe = errorPipe else { return }

        // Monitor stdout
        outputPipe.fileHandleForReading.readabilityHandler = { [weak self] handle in
            let data = handle.availableData
            guard !data.isEmpty,
                  let output = String(data: data, encoding: .utf8) else { return }

            self?.handlePythonOutput(output)
        }

        // Monitor stderr
        errorPipe.fileHandleForReading.readabilityHandler = { [weak self] handle in
            let data = handle.availableData
            guard !data.isEmpty,
                  let error = String(data: data, encoding: .utf8) else { return }

            self?.handlePythonError(error)
        }
    }

    private func handlePythonOutput(_ output: String) {
        // Parse JSON messages from Python
        // Expected format: {"type": "status", "data": {...}}

        guard let data = output.data(using: .utf8),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let type = json["type"] as? String else {
            print("Python output: \(output)")
            return
        }

        DispatchQueue.main.async { [weak self] in
            switch type {
            case "status":
                if let status = json["status"] as? String {
                    self?.handleStatusUpdate(status)
                }

            case "wake_word":
                self?.currentStatus = .listening
                self?.delegate?.didDetectWakeWord()

            case "transcription":
                if let text = json["text"] as? String {
                    self?.delegate?.didReceiveTranscription(text)
                }

            case "response":
                if let text = json["text"] as? String {
                    self?.currentStatus = .idle
                    self?.delegate?.didReceiveResponse(text)
                }

            case "error":
                if let errorMessage = json["message"] as? String {
                    self?.currentStatus = .error(errorMessage)
                    self?.delegate?.didEncounterError(errorMessage)
                }

            case "rewrite_complete":
                // Handle inline AI rewrite completion
                if let original = json["original"] as? String,
                   let rewritten = json["rewritten"] as? String {
                    InlineAIController.shared.handleRewriteComplete(
                        original: original,
                        rewritten: rewritten
                    )
                }

            case "summarize_complete":
                // Handle inline AI summarize completion
                if let original = json["original"] as? String,
                   let summary = json["summary"] as? String {
                    InlineAIController.shared.handleSummarizeComplete(
                        original: original,
                        summary: summary
                    )
                }

            case "inline_ai_error":
                // Handle inline AI error
                if let errorMessage = json["error"] as? String {
                    InlineAIController.shared.handleInlineAIError(error: errorMessage)
                }

            default:
                print("Unknown message type: \(type)")
            }
        }
    }

    private func handlePythonError(_ error: String) {
        print("Python error: \(error)")

        DispatchQueue.main.async { [weak self] in
            self?.currentStatus = .error(error)
            self?.delegate?.didEncounterError(error)
        }
    }

    private func handleStatusUpdate(_ status: String) {
        switch status {
        case "idle":
            currentStatus = .idle
        case "listening":
            currentStatus = .listening
            delegate?.didStartListening()
        case "processing":
            currentStatus = .processing
        default:
            break
        }
    }

    // MARK: - Commands

    func startListening() {
        guard isRunning else {
            print("Cannot start listening: Python service not running")
            return
        }

        sendCommand(["command": "start_listening"])
        currentStatus = .listening
    }

    func stopListening() {
        sendCommand(["command": "stop_listening"])
        currentStatus = .idle
    }

    func getStatus() -> String {
        return "\(currentStatus)"
    }

    func updateConfig(_ config: [String: Any]) {
        sendCommand([
            "command": "update_config",
            "config": config
        ])
    }

    private func sendCommand(_ command: [String: Any]) {
        guard let inputPipe = inputPipe,
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

// MARK: - Configuration Export

extension Configuration {
    func exportConfigPath() -> String {
        let configDir = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
            .appendingPathComponent("VoiceAssistant")

        try? FileManager.default.createDirectory(at: configDir, withIntermediateDirectories: true)

        let configPath = configDir.appendingPathComponent("config.yaml")

        // Export configuration to YAML
        let configDict = exportToYAML()
        if let yamlString = convertToYAML(configDict) {
            try? yamlString.write(to: configPath, atomically: true, encoding: .utf8)
        }

        return configPath.path
    }

    private func convertToYAML(_ dict: [String: Any], indent: Int = 0) -> String? {
        var yaml = ""
        let indentString = String(repeating: "  ", count: indent)

        for (key, value) in dict {
            if let dictValue = value as? [String: Any] {
                yaml += "\(indentString)\(key):\n"
                if let nested = convertToYAML(dictValue, indent: indent + 1) {
                    yaml += nested
                }
            } else if let arrayValue = value as? [Any] {
                yaml += "\(indentString)\(key):\n"
                for item in arrayValue {
                    yaml += "\(indentString)  - \(item)\n"
                }
            } else if let stringValue = value as? String {
                yaml += "\(indentString)\(key): \"\(stringValue)\"\n"
            } else if let boolValue = value as? Bool {
                yaml += "\(indentString)\(key): \(boolValue)\n"
            } else if let numValue = value as? NSNumber {
                yaml += "\(indentString)\(key): \(numValue)\n"
            } else {
                yaml += "\(indentString)\(key): \(value)\n"
            }
        }

        return yaml
    }
}
