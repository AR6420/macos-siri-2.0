//
//  EnhancedFloatingPanelTests.swift
//  VoiceAssistantTests
//
//  Unit tests for EnhancedFloatingPanelWindow and related components
//

import XCTest
import SwiftUI
@testable import VoiceAssistant

class EnhancedFloatingPanelTests: XCTestCase {

    // MARK: - Properties

    var panel: EnhancedFloatingPanelWindow!
    var mockDelegate: MockEnhancedFloatingPanelDelegate!

    // MARK: - Setup & Teardown

    override func setUp() {
        super.setUp()
        mockDelegate = MockEnhancedFloatingPanelDelegate()
    }

    override func tearDown() {
        panel?.dismiss()
        panel = nil
        mockDelegate = nil
        super.tearDown()
    }

    // MARK: - Initialization Tests

    func testPanelInitialization() {
        let position = CGPoint(x: 100, y: 300)
        let selectedText = "This is a test text selection"

        panel = EnhancedFloatingPanelWindow(at: position, selectedText: selectedText)

        XCTAssertNotNil(panel)
        XCTAssertTrue(panel.isFloatingPanel)
        XCTAssertEqual(panel.level, .floating)
        XCTAssertFalse(panel.isOpaque)
        XCTAssertEqual(panel.backgroundColor, .clear)
        XCTAssertTrue(panel.hasShadow)
    }

    func testPanelSize() {
        let position = CGPoint(x: 100, y: 300)
        let selectedText = "Test"

        panel = EnhancedFloatingPanelWindow(at: position, selectedText: selectedText)

        let frame = panel.frame
        XCTAssertEqual(frame.width, 320)
        XCTAssertGreaterThan(frame.height, 0)
        XCTAssertLessThanOrEqual(frame.height, 500)
    }

    func testPanelPosition() {
        let position = CGPoint(x: 100, y: 300)
        let selectedText = "Test"

        panel = EnhancedFloatingPanelWindow(at: position, selectedText: selectedText)

        let frame = panel.frame
        // Panel should be positioned below the button
        XCTAssertEqual(frame.origin.x, position.x - 10)
        XCTAssertLessThan(frame.origin.y, position.y)
    }

    // MARK: - Auto Dismiss Tests

    func testAutoDismissTimer() {
        let position = CGPoint(x: 100, y: 300)
        panel = EnhancedFloatingPanelWindow(at: position, selectedText: "Test")
        panel.panelDelegate = mockDelegate

        let expectation = XCTestExpectation(description: "Panel auto-dismissed")

        mockDelegate.onDismiss = {
            expectation.fulfill()
        }

        // Wait for auto-dismiss (15 seconds)
        wait(for: [expectation], timeout: 16.0)
    }

    func testAutoDismissCancelsOnManualDismiss() {
        let position = CGPoint(x: 100, y: 300)
        panel = EnhancedFloatingPanelWindow(at: position, selectedText: "Test")
        panel.panelDelegate = mockDelegate

        var dismissCount = 0
        mockDelegate.onDismiss = {
            dismissCount += 1
        }

        // Manually dismiss
        panel.dismiss()

        // Wait to ensure auto-dismiss doesn't fire
        let expectation = XCTestExpectation(description: "Wait for potential auto-dismiss")
        DispatchQueue.main.asyncAfter(deadline: .now() + 16.0) {
            expectation.fulfill()
        }

        wait(for: [expectation], timeout: 17.0)

        // Should only dismiss once (manual dismiss)
        XCTAssertEqual(dismissCount, 1)
    }

    // MARK: - Delegate Tests

    func testOptionSelectedDelegate() {
        let position = CGPoint(x: 100, y: 300)
        panel = EnhancedFloatingPanelWindow(at: position, selectedText: "Test")
        panel.panelDelegate = mockDelegate

        let expectation = XCTestExpectation(description: "Option selected")

        mockDelegate.onOptionSelected = { option, customInput in
            XCTAssertNotNil(option)
            expectation.fulfill()
        }

        // Note: In a real test, this would be triggered by UI interaction
        // For unit tests, we verify the delegate pattern

        wait(for: [expectation], timeout: 1.0)
    }

    func testDismissDelegate() {
        let position = CGPoint(x: 100, y: 300)
        panel = EnhancedFloatingPanelWindow(at: position, selectedText: "Test")
        panel.panelDelegate = mockDelegate

        let expectation = XCTestExpectation(description: "Panel dismissed")

        mockDelegate.onDismiss = {
            expectation.fulfill()
        }

        panel.dismiss()

        wait(for: [expectation], timeout: 1.0)
    }

    // MARK: - Window Properties Tests

    func testWindowProperties() {
        let position = CGPoint(x: 100, y: 300)
        panel = EnhancedFloatingPanelWindow(at: position, selectedText: "Test")

        XCTAssertFalse(panel.isMovableByWindowBackground)
        XCTAssertFalse(panel.hidesOnDeactivate)
        XCTAssertTrue(panel.collectionBehavior.contains(.canJoinAllSpaces))
        XCTAssertTrue(panel.collectionBehavior.contains(.fullScreenAuxiliary))
    }

    // MARK: - Animation Tests

    func testAnimateIn() {
        let position = CGPoint(x: 100, y: 300)
        panel = EnhancedFloatingPanelWindow(at: position, selectedText: "Test")

        // Initial alpha should be 0, then animate to 1
        let expectation = XCTestExpectation(description: "Panel animated in")

        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
            XCTAssertEqual(self.panel.alphaValue, 1.0, accuracy: 0.1)
            expectation.fulfill()
        }

        wait(for: [expectation], timeout: 1.0)
    }
}

// MARK: - Mock Delegate

class MockEnhancedFloatingPanelDelegate: EnhancedFloatingPanelDelegate {

    var onOptionSelected: ((MenuOption, String?) -> Void)?
    var onDismiss: (() -> Void)?

    func didSelectOption(_ option: MenuOption, customInput: String?) {
        onOptionSelected?(option, customInput)
    }

    func didDismissPanel() {
        onDismiss?()
    }
}

// MARK: - SwiftUI View Tests

class EnhancedFloatingPanelViewTests: XCTestCase {

    func testViewCreation() {
        let view = EnhancedFloatingPanelView(
            selectedText: "Test text",
            onOptionSelected: { _, _ in },
            onDismiss: { }
        )

        XCTAssertNotNil(view)
    }

    func testViewWithLongText() {
        let longText = String(repeating: "Test ", count: 100)
        let view = EnhancedFloatingPanelView(
            selectedText: longText,
            onOptionSelected: { _, _ in },
            onDismiss: { }
        )

        XCTAssertNotNil(view)
    }

    func testViewWithEmptyText() {
        let view = EnhancedFloatingPanelView(
            selectedText: "",
            onOptionSelected: { _, _ in },
            onDismiss: { }
        )

        XCTAssertNotNil(view)
    }
}

// MARK: - Custom Text Field Style Tests

class CustomTextFieldStyleTests: XCTestCase {

    func testCustomTextFieldStyleCreation() {
        let style = CustomTextFieldStyle()
        XCTAssertNotNil(style)
    }
}
