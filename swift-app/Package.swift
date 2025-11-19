// swift-tools-version: 6.0
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "VoiceAssistant",
    platforms: [
        .macOS(.v15)
    ],
    products: [
        .executable(
            name: "VoiceAssistant",
            targets: ["VoiceAssistant"]
        )
    ],
    dependencies: [
        // No external dependencies - using native macOS frameworks only
    ],
    targets: [
        .executableTarget(
            name: "VoiceAssistant",
            dependencies: [],
            path: "Sources"
        ),
        .testTarget(
            name: "VoiceAssistantTests",
            dependencies: ["VoiceAssistant"],
            path: "Tests"
        )
    ]
)
