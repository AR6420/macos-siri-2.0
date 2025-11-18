//
//  Configuration.swift
//  VoiceAssistant
//
//  Application configuration and settings
//

import Foundation
import Combine

enum LLMBackend: String, Codable, CaseIterable, Identifiable {
    case localGPTOSS = "local_gpt_oss"
    case openai = "openai_gpt4"
    case anthropic = "anthropic_claude"
    case openrouter = "openrouter"

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .localGPTOSS:
            return "Local (gpt-oss:120b)"
        case .openai:
            return "OpenAI (GPT-4)"
        case .anthropic:
            return "Anthropic (Claude)"
        case .openrouter:
            return "OpenRouter"
        }
    }
}

class Configuration: ObservableObject {

    // MARK: - Singleton

    static let shared = Configuration()

    // MARK: - Published Properties

    // General
    @Published var launchAtLogin: Bool {
        didSet { save() }
    }

    @Published var wakeWordEnabled: Bool {
        didSet { save() }
    }

    @Published var wakeWordSensitivity: Double {
        didSet { save() }
    }

    // LLM Backend
    @Published var llmBackend: LLMBackend {
        didSet { save() }
    }

    @Published var localGPTOSSURL: String {
        didSet { save() }
    }

    @Published var temperature: Double {
        didSet { save() }
    }

    @Published var maxTokens: Int {
        didSet { save() }
    }

    // Conversation
    @Published var maxConversationTurns: Int {
        didSet { save() }
    }

    // Logging
    @Published var enableLogging: Bool {
        didSet { save() }
    }

    // MARK: - User Defaults Keys

    private enum Keys {
        static let launchAtLogin = "launchAtLogin"
        static let wakeWordEnabled = "wakeWordEnabled"
        static let wakeWordSensitivity = "wakeWordSensitivity"
        static let llmBackend = "llmBackend"
        static let localGPTOSSURL = "localGPTOSSURL"
        static let temperature = "temperature"
        static let maxTokens = "maxTokens"
        static let maxConversationTurns = "maxConversationTurns"
        static let enableLogging = "enableLogging"
    }

    // MARK: - Initialization

    private init() {
        // Load from UserDefaults or use defaults
        self.launchAtLogin = UserDefaults.standard.bool(forKey: Keys.launchAtLogin)
        self.wakeWordEnabled = UserDefaults.standard.object(forKey: Keys.wakeWordEnabled) as? Bool ?? true
        self.wakeWordSensitivity = UserDefaults.standard.object(forKey: Keys.wakeWordSensitivity) as? Double ?? 0.5

        if let backendString = UserDefaults.standard.string(forKey: Keys.llmBackend),
           let backend = LLMBackend(rawValue: backendString) {
            self.llmBackend = backend
        } else {
            self.llmBackend = .localGPTOSS
        }

        self.localGPTOSSURL = UserDefaults.standard.string(forKey: Keys.localGPTOSSURL) ?? "http://localhost:8080"
        self.temperature = UserDefaults.standard.object(forKey: Keys.temperature) as? Double ?? 0.7
        self.maxTokens = UserDefaults.standard.object(forKey: Keys.maxTokens) as? Int ?? 1024
        self.maxConversationTurns = UserDefaults.standard.object(forKey: Keys.maxConversationTurns) as? Int ?? 10
        self.enableLogging = UserDefaults.standard.object(forKey: Keys.enableLogging) as? Bool ?? true
    }

    // MARK: - Save to UserDefaults

    func save() {
        UserDefaults.standard.set(launchAtLogin, forKey: Keys.launchAtLogin)
        UserDefaults.standard.set(wakeWordEnabled, forKey: Keys.wakeWordEnabled)
        UserDefaults.standard.set(wakeWordSensitivity, forKey: Keys.wakeWordSensitivity)
        UserDefaults.standard.set(llmBackend.rawValue, forKey: Keys.llmBackend)
        UserDefaults.standard.set(localGPTOSSURL, forKey: Keys.localGPTOSSURL)
        UserDefaults.standard.set(temperature, forKey: Keys.temperature)
        UserDefaults.standard.set(maxTokens, forKey: Keys.maxTokens)
        UserDefaults.standard.set(maxConversationTurns, forKey: Keys.maxConversationTurns)
        UserDefaults.standard.set(enableLogging, forKey: Keys.enableLogging)
    }

    // MARK: - Export to config.yaml format

    func exportToYAML() -> [String: Any] {
        return [
            "app": [
                "version": "1.0.0",
                "log_level": enableLogging ? "INFO" : "WARNING",
                "log_dir": "/tmp/voice-assistant/logs",
                "data_dir": "~/Library/Application Support/VoiceAssistant"
            ],
            "llm": [
                "backend": llmBackend.rawValue,
                "local_gpt_oss": [
                    "base_url": localGPTOSSURL,
                    "model": "gpt-oss:120b",
                    "timeout": 120,
                    "max_tokens": maxTokens,
                    "temperature": temperature
                ],
                "openai": [
                    "api_key_env": "OPENAI_API_KEY",
                    "model": "gpt-4o",
                    "timeout": 60
                ],
                "anthropic": [
                    "api_key_env": "ANTHROPIC_API_KEY",
                    "model": "claude-sonnet-4-20250514",
                    "timeout": 60
                ]
            ],
            "audio": [
                "wake_word": [
                    "enabled": wakeWordEnabled,
                    "sensitivity": wakeWordSensitivity
                ]
            ],
            "conversation": [
                "max_history_turns": maxConversationTurns
            ]
        ]
    }
}

// MARK: - Keychain Manager

class KeychainManager {

    // MARK: - Save to Keychain

    static func save(key: String, value: String) {
        let data = value.data(using: .utf8)!

        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecValueData as String: data,
            kSecAttrService as String: "com.voiceassistant.keys"
        ]

        // Delete existing item
        SecItemDelete(query as CFDictionary)

        // Add new item
        let status = SecItemAdd(query as CFDictionary, nil)

        if status != errSecSuccess {
            print("Keychain save error: \(status)")
        }
    }

    // MARK: - Retrieve from Keychain

    static func retrieve(key: String) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecAttrService as String: "com.voiceassistant.keys",
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]

        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)

        guard status == errSecSuccess,
              let data = result as? Data,
              let value = String(data: data, encoding: .utf8) else {
            return nil
        }

        return value
    }

    // MARK: - Delete from Keychain

    static func delete(key: String) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecAttrService as String: "com.voiceassistant.keys"
        ]

        SecItemDelete(query as CFDictionary)
    }
}
