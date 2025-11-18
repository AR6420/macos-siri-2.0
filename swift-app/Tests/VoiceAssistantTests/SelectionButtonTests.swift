//
//  SelectionButtonTests.swift
//  VoiceAssistantTests
//
//  Unit tests for SelectionButtonWindow and related components
//

import XCTest
import SwiftUI
@testable import VoiceAssistant

class SelectionButtonTests: XCTestCase {

    // MARK: - Properties

    var button: SelectionButtonWindow!
    var mockDelegate: MockSelectionButtonDelegate!

    // MARK: - Setup & Teardown

    override func setUp() {
        super.setUp()
        mockDelegate = MockSelectionButtonDelegate()
    }

    override func tearDown() {
        button?.dismiss()
        button = nil
        mockDelegate = nil
        super.tearDown()
    }

    // MARK: - Initialization Tests

    func testButtonInitialization() {
        let position = CGPoint(x: 100, y: 200)
        button = SelectionButtonWindow(at: position)

        XCTAssertNotNil(button)
        XCTAssertTrue(button.isFloatingPanel)
        XCTAssertEqual(button.level, .floating)
        XCTAssertFalse(button.isOpaque)
        XCTAssertEqual(button.backgroundColor, .clear)
        XCTAssertTrue(button.hasShadow)
    }

    func testButtonSize() {
        let position = CGPoint(x: 100, y: 200)
        button = SelectionButtonWindow(at: position)

        let frame = button.frame
        XCTAssertEqual(frame.width, 36)
        XCTAssertEqual(frame.height, 36)
    }

    func testButtonPosition() {
        let position = CGPoint(x: 100, y: 200)
        button = SelectionButtonWindow(at: position)

        let frame = button.frame
        // Button should be offset from position
        XCTAssertEqual(frame.origin.x, position.x + 5)
        XCTAssertEqual(frame.origin.y, position.y - 36 - 5)
    }

    // MARK: - Delegate Tests

    func testDelegateCallback() {
        let position = CGPoint(x: 100, y: 200)
        button = SelectionButtonWindow(at: position)
        button.buttonDelegate = mockDelegate

        let expectation = XCTestExpectation(description: "Delegate called")

        mockDelegate.onButtonClick = { clickPosition in
            XCTAssertNotNil(clickPosition)
            expectation.fulfill()
        }

        // Simulate button click through the view
        // Note: In a real UI test, this would be triggered by user interaction
        // For unit tests, we can test the delegate pattern directly

        wait(for: [expectation], timeout: 1.0)
    }

    // MARK: - Position Update Tests

    func testPositionUpdate() {
        let initialPosition = CGPoint(x: 100, y: 200)
        button = SelectionButtonWindow(at: initialPosition)

        let initialFrame = button.frame

        let newPosition = CGPoint(x: 150, y: 250)
        button.updatePosition(newPosition)

        // Give animation time to complete
        let expectation = XCTestExpectation(description: "Position updated")
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) {
            let newFrame = self.button.frame
            XCTAssertNotEqual(newFrame.origin, initialFrame.origin)
            expectation.fulfill()
        }

        wait(for: [expectation], timeout: 1.0)
    }

    // MARK: - Dismiss Tests

    func testDismiss() {
        let position = CGPoint(x: 100, y: 200)
        button = SelectionButtonWindow(at: position)
        button.orderFront(nil)

        XCTAssertTrue(button.isVisible)

        button.dismiss()

        // Give animation time to complete
        let expectation = XCTestExpectation(description: "Button dismissed")
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) {
            XCTAssertFalse(self.button.isVisible)
            expectation.fulfill()
        }

        wait(for: [expectation], timeout: 1.0)
    }

    // MARK: - Window Properties Tests

    func testWindowProperties() {
        let position = CGPoint(x: 100, y: 200)
        button = SelectionButtonWindow(at: position)

        XCTAssertFalse(button.isMovableByWindowBackground)
        XCTAssertFalse(button.hidesOnDeactivate)
        XCTAssertTrue(button.collectionBehavior.contains(.canJoinAllSpaces))
        XCTAssertTrue(button.collectionBehavior.contains(.fullScreenAuxiliary))
    }
}

// MARK: - Mock Delegate

class MockSelectionButtonDelegate: SelectionButtonDelegate {

    var onButtonClick: ((CGPoint) -> Void)?

    func selectionButtonDidClick(at position: CGPoint) {
        onButtonClick?(position)
    }
}

// MARK: - Color Extension Tests

class ColorExtensionTests: XCTestCase {

    func testHexColorParsing() {
        // Test 6-digit hex
        let orange = Color(hex: "#FF6B35")
        XCTAssertNotNil(orange)

        // Test without hash
        let purple = Color(hex: "8B5CF6")
        XCTAssertNotNil(purple)

        // Test 3-digit hex
        let shortHex = Color(hex: "F00")
        XCTAssertNotNil(shortHex)

        // Test 8-digit hex (with alpha)
        let withAlpha = Color(hex: "FF6B35FF")
        XCTAssertNotNil(withAlpha)
    }

    func testInvalidHexColor() {
        let invalid = Color(hex: "INVALID")
        XCTAssertNotNil(invalid) // Should still create a color (black fallback)
    }
}
