//
//  PreferencesWindow.swift
//  VoiceAssistant
//
//  Preferences window UI using SwiftUI
//

import SwiftUI
import Security

struct PreferencesWindow: View {

    @StateObject private var configuration = Configuration.shared
    @StateObject private var permissionManager = PermissionManager.shared

    @State private var selectedTab = 0

    var body: some View {
        TabView(selection: $selectedTab) {
            GeneralTab()
                .tabItem {
                    Label("General", systemImage: "gearshape")
                }
                .tag(0)

            LLMBackendTab()
                .tabItem {
                    Label("AI Backend", systemImage: "brain")
                }
                .tag(1)

            PermissionsTab()
                .tabItem {
                    Label("Permissions", systemImage: "lock.shield")
                }
                .tag(2)

            AdvancedTab()
                .tabItem {
                    Label("Advanced", systemImage: "slider.horizontal.3")
                }
                .tag(3)
        }
        .frame(width: 600, height: 500)
        .padding()
    }
}

// MARK: - General Tab

struct GeneralTab: View {
    @StateObject private var configuration = Configuration.shared

    var body: some View {
        Form {
            Section {
                Toggle("Launch at Login", isOn: $configuration.launchAtLogin)
                    .onChange(of: configuration.launchAtLogin) { _ in
                        configuration.save()
                        if let appDelegate = NSApp.delegate as? AppDelegate {
                            appDelegate.updateLaunchAtLoginStatus()
                        }
                    }

                Toggle("Enable Wake Word Detection", isOn: $configuration.wakeWordEnabled)
                    .onChange(of: configuration.wakeWordEnabled) { _ in
                        configuration.save()
                    }
            } header: {
                Text("General Settings")
                    .font(.headline)
            }

            Section {
                HStack {
                    Text("Hotkey:")
                    Spacer()
                    Text("⌘⇧Space")
                        .font(.system(.body, design: .monospaced))
                        .foregroundColor(.secondary)
                }
                Text("Use the hotkey to activate voice assistant without wake word")
                    .font(.caption)
                    .foregroundColor(.secondary)
            } header: {
                Text("Activation")
                    .font(.headline)
            }
        }
        .formStyle(.grouped)
    }
}

// MARK: - LLM Backend Tab

struct LLMBackendTab: View {
    @StateObject private var configuration = Configuration.shared

    @State private var openAIKey: String = ""
    @State private var anthropicKey: String = ""
    @State private var openRouterKey: String = ""

    var body: some View {
        Form {
            Section {
                Picker("Backend:", selection: $configuration.llmBackend) {
                    Text("Local (gpt-oss:120b)").tag(LLMBackend.localGPTOSS)
                    Text("OpenAI (GPT-4)").tag(LLMBackend.openai)
                    Text("Anthropic (Claude)").tag(LLMBackend.anthropic)
                    Text("OpenRouter").tag(LLMBackend.openrouter)
                }
                .onChange(of: configuration.llmBackend) { _ in
                    configuration.save()
                }
            } header: {
                Text("AI Backend Selection")
                    .font(.headline)
            }

            if configuration.llmBackend == .localGPTOSS {
                LocalGPTOSSSettings()
            } else if configuration.llmBackend == .openai {
                OpenAISettings(apiKey: $openAIKey)
            } else if configuration.llmBackend == .anthropic {
                AnthropicSettings(apiKey: $anthropicKey)
            } else if configuration.llmBackend == .openrouter {
                OpenRouterSettings(apiKey: $openRouterKey)
            }
        }
        .formStyle(.grouped)
        .onAppear {
            loadAPIKeys()
        }
    }

    private func loadAPIKeys() {
        openAIKey = KeychainManager.retrieve(key: "OPENAI_API_KEY") ?? ""
        anthropicKey = KeychainManager.retrieve(key: "ANTHROPIC_API_KEY") ?? ""
        openRouterKey = KeychainManager.retrieve(key: "OPENROUTER_API_KEY") ?? ""
    }
}

struct LocalGPTOSSSettings: View {
    @StateObject private var configuration = Configuration.shared

    var body: some View {
        Section {
            TextField("Base URL:", text: $configuration.localGPTOSSURL)
                .onChange(of: configuration.localGPTOSSURL) { _ in
                    configuration.save()
                }

            HStack {
                Slider(value: $configuration.temperature, in: 0...1, step: 0.1)
                    .onChange(of: configuration.temperature) { _ in
                        configuration.save()
                    }
                Text(String(format: "%.1f", configuration.temperature))
                    .frame(width: 40)
            }
            .padding(.vertical, 4)

            Text("Local LLM running via MLX on localhost")
                .font(.caption)
                .foregroundColor(.secondary)
        } header: {
            Text("Local GPT-OSS Settings")
                .font(.headline)
        }
    }
}

struct OpenAISettings: View {
    @Binding var apiKey: String

    var body: some View {
        Section {
            SecureField("API Key:", text: $apiKey)
                .onChange(of: apiKey) { newValue in
                    KeychainManager.save(key: "OPENAI_API_KEY", value: newValue)
                }

            Text("Get your API key from platform.openai.com")
                .font(.caption)
                .foregroundColor(.secondary)
        } header: {
            Text("OpenAI Settings")
                .font(.headline)
        }
    }
}

struct AnthropicSettings: View {
    @Binding var apiKey: String

    var body: some View {
        Section {
            SecureField("API Key:", text: $apiKey)
                .onChange(of: apiKey) { newValue in
                    KeychainManager.save(key: "ANTHROPIC_API_KEY", value: newValue)
                }

            Text("Get your API key from console.anthropic.com")
                .font(.caption)
                .foregroundColor(.secondary)
        } header: {
            Text("Anthropic Settings")
                .font(.headline)
        }
    }
}

struct OpenRouterSettings: View {
    @Binding var apiKey: String

    var body: some View {
        Section {
            SecureField("API Key:", text: $apiKey)
                .onChange(of: apiKey) { newValue in
                    KeychainManager.save(key: "OPENROUTER_API_KEY", value: newValue)
                }

            Text("Get your API key from openrouter.ai")
                .font(.caption)
                .foregroundColor(.secondary)
        } header: {
            Text("OpenRouter Settings")
                .font(.headline)
        }
    }
}

// MARK: - Permissions Tab

struct PermissionsTab: View {
    @StateObject private var permissionManager = PermissionManager.shared

    var body: some View {
        Form {
            Section {
                PermissionRow(
                    type: .microphone,
                    status: permissionManager.microphoneStatus,
                    onRequest: {
                        permissionManager.requestMicrophonePermission { _ in
                            permissionManager.refreshAllPermissions()
                        }
                    }
                )

                PermissionRow(
                    type: .accessibility,
                    status: permissionManager.accessibilityStatus,
                    onRequest: {
                        permissionManager.requestAccessibilityPermission()
                        DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                            permissionManager.refreshAllPermissions()
                        }
                    }
                )

                PermissionRow(
                    type: .inputMonitoring,
                    status: permissionManager.inputMonitoringStatus,
                    onRequest: {
                        permissionManager.requestInputMonitoringPermission()
                    }
                )

                PermissionRow(
                    type: .fullDiskAccess,
                    status: permissionManager.fullDiskAccessStatus,
                    onRequest: {
                        permissionManager.requestFullDiskAccessPermission()
                    }
                )
            } header: {
                Text("Required Permissions")
                    .font(.headline)
            }

            Button("Refresh All Permissions") {
                permissionManager.refreshAllPermissions()
            }
            .padding(.top, 8)
        }
        .formStyle(.grouped)
        .onAppear {
            permissionManager.refreshAllPermissions()
        }
    }
}

struct PermissionRow: View {
    let type: PermissionType
    let status: PermissionStatus
    let onRequest: () -> Void

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(type.displayName)
                    .font(.body)
                Text(type.usageDescription)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(2)
            }

            Spacer()

            if status == .authorized {
                Image(systemName: "checkmark.circle.fill")
                    .foregroundColor(.green)
            } else {
                Button("Grant") {
                    onRequest()
                }
            }
        }
        .padding(.vertical, 4)
    }
}

// MARK: - Advanced Tab

struct AdvancedTab: View {
    @StateObject private var configuration = Configuration.shared

    var body: some View {
        Form {
            Section {
                HStack {
                    Text("Wake Word Sensitivity:")
                    Spacer()
                    Slider(value: $configuration.wakeWordSensitivity, in: 0...1, step: 0.1)
                        .frame(width: 200)
                        .onChange(of: configuration.wakeWordSensitivity) { _ in
                            configuration.save()
                        }
                    Text(String(format: "%.1f", configuration.wakeWordSensitivity))
                        .frame(width: 40)
                }
            } header: {
                Text("Wake Word Settings")
                    .font(.headline)
            }

            Section {
                HStack {
                    Text("Max Conversation Turns:")
                    Spacer()
                    Stepper(value: $configuration.maxConversationTurns, in: 1...20) {
                        Text("\(configuration.maxConversationTurns)")
                            .frame(width: 40)
                    }
                    .onChange(of: configuration.maxConversationTurns) { _ in
                        configuration.save()
                    }
                }
            } header: {
                Text("Conversation Settings")
                    .font(.headline)
            }

            Section {
                Toggle("Enable Logging", isOn: $configuration.enableLogging)
                    .onChange(of: configuration.enableLogging) { _ in
                        configuration.save()
                    }

                if configuration.enableLogging {
                    HStack {
                        Text("Log Directory:")
                        Spacer()
                        Text("/tmp/voice-assistant/logs")
                            .font(.system(.caption, design: .monospaced))
                            .foregroundColor(.secondary)
                    }
                }
            } header: {
                Text("Logging")
                    .font(.headline)
            }
        }
        .formStyle(.grouped)
    }
}

// MARK: - Preview

#Preview {
    PreferencesWindow()
}
