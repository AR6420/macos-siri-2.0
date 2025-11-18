// swift-tools-version: 5.9
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "VoiceAssistant",
    platforms: [
        .macOS(.v14)
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
            path: "Sources",
            resources: [
                .process("Resources")
            ]
        ),
        .testTarget(
            name: "VoiceAssistantTests",
            dependencies: ["VoiceAssistant"],
            path: "Tests"
        )
    ]
)
