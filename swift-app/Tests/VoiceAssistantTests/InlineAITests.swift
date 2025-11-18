//
//  InlineAITests.swift
//  VoiceAssistantTests
//
//  Unit tests for Inline AI components
//

import XCTest
@testable import VoiceAssistant

class SelectionExtractorTests: XCTestCase {

    func testExtractFromClipboard() {
        // Setup test clipboard content
        let testText = "Test clipboard content"
        NSPasteboard.general.clearContents()
        NSPasteboard.general.setString(testText, forType: .string)

        // Extract from clipboard
        let extracted = SelectionExtractor.extractFromClipboard()

        XCTAssertEqual(extracted, testText)
    }

    func testExtractFromClipboardEmpty() {
        // Clear clipboard
        NSPasteboard.general.clearContents()

        // Extract should return nil
        let extracted = SelectionExtractor.extractFromClipboard()

        XCTAssertNil(extracted)
    }

    func testExtractFromClipboardTrimsWhitespace() {
        // Setup clipboard with whitespace
        let testText = "  Test with whitespace  \n"
        NSPasteboard.general.clearContents()
        NSPasteboard.general.setString(testText, forType: .string)

        // Extract should trim whitespace
        let extracted = SelectionExtractor.extractFromClipboard()

        XCTAssertEqual(extracted, "Test with whitespace")
    }
}

class TextReplacerTests: XCTestCase {

    func testReplacementError() {
        // Test error descriptions
        let errors: [TextReplacer.ReplacementError] = [
            .noFocusedElement,
            .accessibilityDenied,
            .replacementFailed,
            .clipboardFailed,
            .invalidElement
        ]

        for error in errors {
            XCTAssertFalse(error.localizedDescription.isEmpty)
        }
    }
}

class FloatingPanelTests: XCTestCase {

    func testToneTypeDisplayNames() {
        XCTAssertEqual(ToneType.professional.displayName, "Professional")
        XCTAssertEqual(ToneType.friendly.displayName, "Friendly")
        XCTAssertEqual(ToneType.concise.displayName, "Concise")
    }

    func testToneTypeIcons() {
        // Verify all tone types have icons
        for tone in ToneType.allCases {
            XCTAssertFalse(tone.icon.isEmpty)
        }
    }

    func testToneTypeRawValues() {
        XCTAssertEqual(ToneType.professional.rawValue, "professional")
        XCTAssertEqual(ToneType.friendly.rawValue, "friendly")
        XCTAssertEqual(ToneType.concise.rawValue, "concise")
    }
}

class InlineAIControllerTests: XCTestCase {

    var controller: InlineAIController!

    override func setUp() {
        super.setUp()
        controller = InlineAIController.shared
    }

    override func tearDown() {
        controller.disable()
        super.tearDown()
    }

    func testEnableDisable() {
        // Initially should be disabled
        controller.disable()

        // Enable
        controller.enable()
        // Note: In test environment, we can't verify monitoring is actually running
        // without full Accessibility API access

        // Disable
        controller.disable()
    }

    func testConfiguration() {
        // Test configuration
        controller.configure(showOnHover: false)
        controller.configure(showOnHover: true)

        // Should not crash
        XCTAssert(true)
    }
}

class TextSelectionEventTests: XCTestCase {

    func testTextSelectionEventCreation() {
        let event = TextSelectionEvent(
            selectedText: "Test text",
            applicationName: "TestApp",
            applicationBundleId: "com.test.app",
            selectionFrame: CGRect(x: 100, y: 100, width: 200, height: 50),
            timestamp: Date()
        )

        XCTAssertEqual(event.selectedText, "Test text")
        XCTAssertEqual(event.applicationName, "TestApp")
        XCTAssertEqual(event.applicationBundleId, "com.test.app")
        XCTAssertEqual(event.selectionFrame.width, 200)
        XCTAssertEqual(event.selectionFrame.height, 50)
    }
}

class InlineAIStatusTests: XCTestCase {

    func testInlineAIStatusTypes() {
        let statuses: [InlineAIStatus] = [
            .idle,
            .monitoring,
            .showingPanel,
            .processing,
            .replacing,
            .error("Test error")
        ]

        // Verify all status types can be created
        XCTAssertEqual(statuses.count, 6)
    }
}
