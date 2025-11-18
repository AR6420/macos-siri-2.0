//
//  ConfigurationTests.swift
//  VoiceAssistantTests
//
//  Unit tests for Configuration model
//

import XCTest
@testable import VoiceAssistant

final class ConfigurationTests: XCTestCase {

    var configuration: Configuration!

    override func setUp() {
        super.setUp()
        // Note: Configuration is a singleton, so we're testing the shared instance
        configuration = Configuration.shared
    }

    override func tearDown() {
        // Clean up UserDefaults
        let defaults = UserDefaults.standard
        defaults.removeObject(forKey: "launchAtLogin")
        defaults.removeObject(forKey: "wakeWordEnabled")
        defaults.removeObject(forKey: "llmBackend")
        super.tearDown()
    }

    // MARK: - Default Values

    func testDefaultValues() {
        // Test that default values are set correctly
        XCTAssertFalse(configuration.launchAtLogin, "Launch at login should default to false")
        XCTAssertTrue(configuration.wakeWordEnabled, "Wake word should default to enabled")
        XCTAssertEqual(configuration.wakeWordSensitivity, 0.5, accuracy: 0.01)
        XCTAssertEqual(configuration.llmBackend, .localGPTOSS)
        XCTAssertEqual(configuration.temperature, 0.7, accuracy: 0.01)
        XCTAssertEqual(configuration.maxConversationTurns, 10)
    }

    // MARK: - Save and Load

    func testSaveAndLoad() {
        // Modify configuration
        configuration.launchAtLogin = true
        configuration.wakeWordSensitivity = 0.8
        configuration.llmBackend = .openai

        // Save
        configuration.save()

        // Verify saved to UserDefaults
        let defaults = UserDefaults.standard
        XCTAssertTrue(defaults.bool(forKey: "launchAtLogin"))
        XCTAssertEqual(defaults.double(forKey: "wakeWordSensitivity"), 0.8, accuracy: 0.01)
        XCTAssertEqual(defaults.string(forKey: "llmBackend"), "openai_gpt4")
    }

    // MARK: - YAML Export

    func testYAMLExport() {
        let yaml = configuration.exportToYAML()

        // Check top-level keys
        XCTAssertNotNil(yaml["app"])
        XCTAssertNotNil(yaml["llm"])
        XCTAssertNotNil(yaml["audio"])
        XCTAssertNotNil(yaml["conversation"])

        // Check LLM section
        if let llm = yaml["llm"] as? [String: Any] {
            XCTAssertEqual(llm["backend"] as? String, configuration.llmBackend.rawValue)
        } else {
            XCTFail("LLM section not found in YAML export")
        }
    }

    // MARK: - LLM Backend Selection

    func testLLMBackendOptions() {
        // Test all backend options
        configuration.llmBackend = .localGPTOSS
        XCTAssertEqual(configuration.llmBackend.rawValue, "local_gpt_oss")

        configuration.llmBackend = .openai
        XCTAssertEqual(configuration.llmBackend.rawValue, "openai_gpt4")

        configuration.llmBackend = .anthropic
        XCTAssertEqual(configuration.llmBackend.rawValue, "anthropic_claude")

        configuration.llmBackend = .openrouter
        XCTAssertEqual(configuration.llmBackend.rawValue, "openrouter")
    }
}

// MARK: - Keychain Tests

final class KeychainManagerTests: XCTestCase {

    let testKey = "TEST_API_KEY"
    let testValue = "sk-test123456789"

    override func tearDown() {
        // Clean up keychain
        KeychainManager.delete(key: testKey)
        super.tearDown()
    }

    func testSaveAndRetrieve() {
        // Save to keychain
        KeychainManager.save(key: testKey, value: testValue)

        // Retrieve from keychain
        let retrieved = KeychainManager.retrieve(key: testKey)

        XCTAssertEqual(retrieved, testValue, "Retrieved value should match saved value")
    }

    func testRetrieveNonExistent() {
        // Try to retrieve non-existent key
        let retrieved = KeychainManager.retrieve(key: "NONEXISTENT_KEY")

        XCTAssertNil(retrieved, "Non-existent key should return nil")
    }

    func testUpdateExisting() {
        // Save initial value
        KeychainManager.save(key: testKey, value: testValue)

        // Update with new value
        let newValue = "sk-updated987654321"
        KeychainManager.save(key: testKey, value: newValue)

        // Retrieve and verify
        let retrieved = KeychainManager.retrieve(key: testKey)
        XCTAssertEqual(retrieved, newValue, "Updated value should be retrieved")
    }

    func testDelete() {
        // Save value
        KeychainManager.save(key: testKey, value: testValue)

        // Verify it exists
        XCTAssertNotNil(KeychainManager.retrieve(key: testKey))

        // Delete
        KeychainManager.delete(key: testKey)

        // Verify it's gone
        XCTAssertNil(KeychainManager.retrieve(key: testKey))
    }
}
