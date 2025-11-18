import XCTest
import AppKit
@testable import VoiceAssistant

/// UI tests for Enhanced Inline AI feature
class EnhancedInlineAITests: XCTestCase {

    var windowController: InlineAIWindowController!
    var mockPythonService: MockPythonService!

    override func setUp() {
        super.setUp()
        mockPythonService = MockPythonService()
        windowController = InlineAIWindowController(pythonService: mockPythonService)
    }

    override func tearDown() {
        windowController = nil
        mockPythonService = nil
        super.tearDown()
    }

    // MARK: - Button Appearance Tests

    func testButtonAppearsOnTextSelection() {
        // Given: Text is selected
        let selectedText = "Hello, world!"
        let selectionBounds = CGRect(x: 100, y: 100, width: 200, height: 30)

        // When: Selection is detected
        let startTime = CFAbsoluteTimeGetCurrent()
        windowController.handleTextSelection(selectedText, bounds: selectionBounds)
        let elapsed = CFAbsoluteTimeGetCurrent() - startTime

        // Then: Button appears quickly
        XCTAssertNotNil(windowController.floatingButton)
        XCTAssertTrue(windowController.floatingButton!.window!.isVisible)

        // Performance: Should appear within 100ms
        XCTAssertLessThan(elapsed, 0.1, "Button should appear within 100ms")
    }

    func testButtonPositionCalculation() {
        // Given: Text selection with specific bounds
        let selectionBounds = CGRect(x: 100, y: 100, width: 200, height: 30)

        // When: Button position is calculated
        let buttonPosition = windowController.calculateButtonPosition(for: selectionBounds)

        // Then: Button is positioned correctly (right edge, vertically centered)
        XCTAssertEqual(buttonPosition.x, 300 + 8) // right edge + margin
        XCTAssertEqual(buttonPosition.y, 115 - 15) // center - half button height
    }

    func testButtonDisappearsWhenSelectionCleared() {
        // Given: Button is visible
        windowController.handleTextSelection("Test", bounds: CGRect(x: 0, y: 0, width: 100, height: 20))
        XCTAssertNotNil(windowController.floatingButton)

        // When: Selection is cleared
        windowController.handleSelectionCleared()

        // Then: Button disappears
        XCTAssertNil(windowController.floatingButton)
    }

    func testButtonAutoDismissAfterTimeout() {
        // Given: Button is visible
        windowController.handleTextSelection("Test", bounds: CGRect(x: 0, y: 0, width: 100, height: 20))

        // When: Timeout period elapses
        let expectation = self.expectation(description: "Auto-dismiss")
        DispatchQueue.main.asyncAfter(deadline: .now() + 6.0) {
            expectation.fulfill()
        }

        waitForExpectations(timeout: 7.0)

        // Then: Button auto-dismisses
        XCTAssertNil(windowController.floatingButton)
    }

    // MARK: - Menu Display Tests

    func testMenuOpensOnButtonClick() {
        // Given: Button is visible
        windowController.handleTextSelection("Test", bounds: CGRect(x: 0, y: 0, width: 100, height: 20))

        // When: Button is clicked
        let startTime = CFAbsoluteTimeGetCurrent()
        windowController.floatingButton!.performClick(nil)
        let elapsed = CFAbsoluteTimeGetCurrent() - startTime

        // Then: Menu opens quickly
        XCTAssertNotNil(windowController.menuWindow)
        XCTAssertTrue(windowController.menuWindow!.isVisible)

        // Performance: Should open within 150ms
        XCTAssertLessThan(elapsed, 0.15, "Menu should open within 150ms")
    }

    func testMenuContainsAllSections() {
        // Given: Menu is open
        windowController.handleTextSelection("Test", bounds: CGRect(x: 0, y: 0, width: 100, height: 20))
        windowController.floatingButton!.performClick(nil)

        // Then: All sections are present
        let menu = windowController.menuWindow!
        XCTAssertTrue(menu.hasSection(title: "Quick Actions"))
        XCTAssertTrue(menu.hasSection(title: "Rewrite"))
        XCTAssertTrue(menu.hasSection(title: "Format"))
        XCTAssertTrue(menu.hasSection(title: "Compose"))
    }

    func testMenuItemCount() {
        // Given: Menu is open
        windowController.handleTextSelection("Test", bounds: CGRect(x: 0, y: 0, width: 100, height: 20))
        windowController.floatingButton!.performClick(nil)

        // Then: Menu has 10 total items (excluding section headers)
        let menuItems = windowController.menuWindow!.getAllMenuItems()
        XCTAssertEqual(menuItems.count, 10)
    }

    func testMenuItemsHaveIcons() {
        // Given: Menu is open
        windowController.handleTextSelection("Test", bounds: CGRect(x: 0, y: 0, width: 100, height: 20))
        windowController.floatingButton!.performClick(nil)

        // Then: All menu items have SF Symbols icons
        let menuItems = windowController.menuWindow!.getAllMenuItems()
        for item in menuItems {
            XCTAssertNotNil(item.icon, "Menu item '\(item.title)' should have an icon")
        }
    }

    func testMenuItemIconsAreCorrect() {
        // Given: Menu is open
        windowController.handleTextSelection("Test", bounds: CGRect(x: 0, y: 0, width: 100, height: 20))
        windowController.floatingButton!.performClick(nil)

        // Then: Specific items have correct icons
        let menuItems = windowController.menuWindow!.getAllMenuItems()

        XCTAssertEqual(findMenuItem(menuItems, title: "Proofread")?.iconName, "checkmark.circle")
        XCTAssertEqual(findMenuItem(menuItems, title: "Summarize")?.iconName, "list.bullet.rectangle")
        XCTAssertEqual(findMenuItem(menuItems, title: "Make List")?.iconName, "list.bullet")
        XCTAssertEqual(findMenuItem(menuItems, title: "Compose...")?.iconName, "square.and.pencil")
    }

    // MARK: - Theme Tests

    func testOrangeThemeApplied() {
        // Given: Menu is open
        windowController.handleTextSelection("Test", bounds: CGRect(x: 0, y: 0, width: 100, height: 20))
        windowController.floatingButton!.performClick(nil)

        // Then: Orange theme colors are applied
        XCTAssertEqual(windowController.floatingButton!.tintColor, NSColor.orange)

        let menuItems = windowController.menuWindow!.getAllMenuItems()
        for item in menuItems {
            XCTAssertEqual(item.highlightColor, NSColor.orange.withAlphaComponent(0.1))
        }
    }

    func testHoverEffects() {
        // Given: Menu is open
        windowController.handleTextSelection("Test", bounds: CGRect(x: 0, y: 0, width: 100, height: 20))
        windowController.floatingButton!.performClick(nil)

        let menuItems = windowController.menuWindow!.getAllMenuItems()
        let firstItem = menuItems[0]

        // When: Mouse hovers over item
        firstItem.simulateMouseEnter()

        // Then: Hover effect is applied
        XCTAssertTrue(firstItem.isHighlighted)

        // When: Mouse leaves
        firstItem.simulateMouseExit()

        // Then: Hover effect is removed
        XCTAssertFalse(firstItem.isHighlighted)
    }

    // MARK: - Action Execution Tests

    func testProofreadAction() async {
        // Given: Menu is open
        windowController.handleTextSelection("Teh quick brown fox", bounds: CGRect(x: 0, y: 0, width: 100, height: 20))
        windowController.floatingButton!.performClick(nil)

        // Mock response
        mockPythonService.mockResponse = """
        {"status": "success", "result": {"text": "The quick brown fox", "original": "Teh quick brown fox"}}
        """

        // When: Proofread is selected
        let menuItems = windowController.menuWindow!.getAllMenuItems()
        let proofreadItem = findMenuItem(menuItems, title: "Proofread")!

        await proofreadItem.performAction()

        // Then: Preview is shown
        XCTAssertNotNil(windowController.previewWindow)
        XCTAssertEqual(windowController.previewWindow!.resultText, "The quick brown fox")
        XCTAssertEqual(windowController.previewWindow!.originalText, "Teh quick brown fox")
    }

    func testRewriteAction() async {
        // Given: Menu is open
        windowController.handleTextSelection("Hello", bounds: CGRect(x: 0, y: 0, width: 100, height: 20))
        windowController.floatingButton!.performClick(nil)

        mockPythonService.mockResponse = """
        {"status": "success", "result": {"text": "Greetings!"}}
        """

        // When: Rewrite Friendly is selected
        let menuItems = windowController.menuWindow!.getAllMenuItems()
        let rewriteItem = findMenuItem(menuItems, title: "Friendly")!

        await rewriteItem.performAction()

        // Then: Preview is shown
        XCTAssertNotNil(windowController.previewWindow)
        XCTAssertEqual(windowController.previewWindow!.resultText, "Greetings!")
    }

    func testMakeListAction() async {
        // Given: Menu is open
        windowController.handleTextSelection("Item 1, Item 2, Item 3", bounds: CGRect(x: 0, y: 0, width: 100, height: 20))
        windowController.floatingButton!.performClick(nil)

        mockPythonService.mockResponse = """
        {"status": "success", "result": {"text": "• Item 1\\n• Item 2\\n• Item 3"}}
        """

        // When: Make List is selected
        let menuItems = windowController.menuWindow!.getAllMenuItems()
        let listItem = findMenuItem(menuItems, title: "Make List")!

        await listItem.performAction()

        // Then: Preview is shown with formatted list
        XCTAssertNotNil(windowController.previewWindow)
        XCTAssertTrue(windowController.previewWindow!.resultText.contains("•"))
    }

    func testComposeAction() async {
        // Given: Menu is open
        windowController.handleTextSelection("", bounds: CGRect(x: 0, y: 0, width: 100, height: 20))
        windowController.floatingButton!.performClick(nil)

        // When: Compose is selected
        let menuItems = windowController.menuWindow!.getAllMenuItems()
        let composeItem = findMenuItem(menuItems, title: "Compose...")!

        composeItem.performAction()

        // Then: Input field is shown
        XCTAssertNotNil(windowController.inputWindow)
        XCTAssertTrue(windowController.inputWindow!.isVisible)
        XCTAssertEqual(windowController.inputWindow!.placeholder, "What would you like me to write?")
    }

    // MARK: - Input Field Tests

    func testInputFieldDisplay() {
        // Given: Compose action is triggered
        windowController.showInputField(for: "compose", placeholder: "Enter prompt")

        // Then: Input field is displayed correctly
        XCTAssertNotNil(windowController.inputWindow)
        XCTAssertTrue(windowController.inputWindow!.isVisible)
        XCTAssertEqual(windowController.inputWindow!.placeholder, "Enter prompt")
    }

    func testInputFieldSubmission() async {
        // Given: Input field is shown
        windowController.showInputField(for: "compose", placeholder: "Enter prompt")

        mockPythonService.mockResponse = """
        {"status": "success", "result": {"text": "Composed text based on prompt"}}
        """

        // When: User enters text and submits
        windowController.inputWindow!.textField.stringValue = "Write a thank you email"
        await windowController.inputWindow!.submitButton.performClick()

        // Then: Request is sent to Python service
        XCTAssertEqual(mockPythonService.lastCommand?["action"] as? String, "compose")
        XCTAssertEqual(mockPythonService.lastCommand?["text"] as? String, "Write a thank you email")

        // And: Preview is shown
        XCTAssertNotNil(windowController.previewWindow)
    }

    func testInputFieldCancellation() {
        // Given: Input field is shown
        windowController.showInputField(for: "compose", placeholder: "Enter prompt")

        // When: User cancels
        windowController.inputWindow!.cancelButton.performClick(nil)

        // Then: Input field closes without sending request
        XCTAssertNil(windowController.inputWindow)
        XCTAssertNil(mockPythonService.lastCommand)
    }

    // MARK: - Preview Tests

    func testPreviewDisplay() {
        // Given: Result from action
        let result = AIResult(text: "Corrected text", original: "Original text")

        // When: Preview is shown
        windowController.showPreview(result: result)

        // Then: Preview window displays correctly
        XCTAssertNotNil(windowController.previewWindow)
        XCTAssertTrue(windowController.previewWindow!.isVisible)
        XCTAssertEqual(windowController.previewWindow!.resultText, "Corrected text")
        XCTAssertEqual(windowController.previewWindow!.originalText, "Original text")
    }

    func testPreviewAccept() {
        // Given: Preview is shown
        let result = AIResult(text: "New text", original: "Old text")
        windowController.showPreview(result: result)

        // When: User accepts
        windowController.previewWindow!.acceptButton.performClick(nil)

        // Then: Text is replaced in original location
        XCTAssertEqual(mockPythonService.replacedText, "New text")

        // And: Preview closes
        XCTAssertNil(windowController.previewWindow)
    }

    func testPreviewCancel() {
        // Given: Preview is shown
        let result = AIResult(text: "New text", original: "Old text")
        windowController.showPreview(result: result)

        // When: User cancels
        windowController.previewWindow!.cancelButton.performClick(nil)

        // Then: Text is not replaced
        XCTAssertNil(mockPythonService.replacedText)

        // And: Preview closes
        XCTAssertNil(windowController.previewWindow)
    }

    func testPreviewShowsDiff() {
        // Given: Result with changes
        let result = AIResult(text: "The quick brown fox", original: "Teh quick brown fox")

        // When: Preview is shown
        windowController.showPreview(result: result)

        // Then: Diff highlighting is applied
        let diffView = windowController.previewWindow!.diffView
        XCTAssertTrue(diffView.hasHighlighting)
        XCTAssertTrue(diffView.highlightedRanges.count > 0)
    }

    // MARK: - Undo Tests

    func testUndoTracking() {
        // Given: Text replacement occurs
        let original = "Original"
        let replacement = "Replaced"

        windowController.replaceText(original: original, with: replacement)

        // Then: Undo entry is created
        XCTAssertTrue(windowController.hasUndoEntry)
        XCTAssertEqual(windowController.lastUndoOriginal, original)
    }

    func testUndoExecution() {
        // Given: Text was replaced
        let original = "Original"
        let replacement = "Replaced"
        windowController.replaceText(original: original, with: replacement)

        // When: Undo is triggered (Cmd+Z)
        windowController.performUndo()

        // Then: Original text is restored
        XCTAssertEqual(mockPythonService.replacedText, original)
    }

    // MARK: - Animation Tests

    func testButtonFadeInAnimation() {
        // Given: Text is selected
        let expectation = self.expectation(description: "Fade in")

        // When: Button appears
        windowController.handleTextSelection("Test", bounds: CGRect(x: 0, y: 0, width: 100, height: 20))

        // Then: Fade in animation is smooth
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
            XCTAssertEqual(self.windowController.floatingButton!.alphaValue, 1.0)
            expectation.fulfill()
        }

        waitForExpectations(timeout: 0.5)
    }

    func testMenuSlideDownAnimation() {
        // Given: Button is clicked
        windowController.handleTextSelection("Test", bounds: CGRect(x: 0, y: 0, width: 100, height: 20))

        let expectation = self.expectation(description: "Slide down")

        // When: Menu opens
        windowController.floatingButton!.performClick(nil)

        // Then: Slide down animation occurs
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
            XCTAssertEqual(self.windowController.menuWindow!.alphaValue, 1.0)
            expectation.fulfill()
        }

        waitForExpectations(timeout: 0.5)
    }

    // MARK: - Accessibility Tests

    func testVoiceOverSupport() {
        // Given: Menu is open
        windowController.handleTextSelection("Test", bounds: CGRect(x: 0, y: 0, width: 100, height: 20))
        windowController.floatingButton!.performClick(nil)

        // Then: All elements have accessibility labels
        XCTAssertNotNil(windowController.floatingButton!.accessibilityLabel())
        XCTAssertEqual(windowController.floatingButton!.accessibilityLabel(), "AI Assistant")

        let menuItems = windowController.menuWindow!.getAllMenuItems()
        for item in menuItems {
            XCTAssertNotNil(item.accessibilityLabel(), "Menu item '\(item.title)' missing accessibility label")
        }
    }

    func testKeyboardNavigation() {
        // Given: Menu is open
        windowController.handleTextSelection("Test", bounds: CGRect(x: 0, y: 0, width: 100, height: 20))
        windowController.floatingButton!.performClick(nil)

        // When: User presses down arrow
        windowController.menuWindow!.keyDown(with: NSEvent.keyEvent(
            with: .keyDown,
            location: .zero,
            modifierFlags: [],
            timestamp: 0,
            windowNumber: 0,
            context: nil,
            characters: "",
            charactersIgnoringModifiers: "",
            isARepeat: false,
            keyCode: 125 // Down arrow
        )!)

        // Then: Next item is focused
        XCTAssertEqual(windowController.menuWindow!.selectedItemIndex, 1)
    }

    func testHighContrastMode() {
        // Given: High contrast mode is enabled
        NSWorkspace.shared.accessibilityDisplayShouldIncreaseContrast = true

        // When: Menu is opened
        windowController.handleTextSelection("Test", bounds: CGRect(x: 0, y: 0, width: 100, height: 20))
        windowController.floatingButton!.performClick(nil)

        // Then: High contrast colors are used
        let menuItems = windowController.menuWindow!.getAllMenuItems()
        for item in menuItems {
            XCTAssertTrue(item.usesHighContrastColors)
        }
    }

    // MARK: - Error Handling Tests

    func testErrorDisplay() async {
        // Given: Menu is open
        windowController.handleTextSelection("Test", bounds: CGRect(x: 0, y: 0, width: 100, height: 20))
        windowController.floatingButton!.performClick(nil)

        // Mock error response
        mockPythonService.mockResponse = """
        {"status": "error", "message": "LLM timeout"}
        """

        // When: Action fails
        let menuItems = windowController.menuWindow!.getAllMenuItems()
        let proofreadItem = findMenuItem(menuItems, title: "Proofread")!
        await proofreadItem.performAction()

        // Then: Error dialog is shown
        XCTAssertNotNil(windowController.errorAlert)
        XCTAssertTrue(windowController.errorAlert!.messageText.contains("timeout"))
    }

    func testNetworkErrorRecovery() async {
        // Given: Network error occurs
        mockPythonService.shouldSimulateError = true

        windowController.handleTextSelection("Test", bounds: CGRect(x: 0, y: 0, width: 100, height: 20))
        windowController.floatingButton!.performClick(nil)

        // When: User retries
        let menuItems = windowController.menuWindow!.getAllMenuItems()
        let proofreadItem = findMenuItem(menuItems, title: "Proofread")!

        await proofreadItem.performAction()

        // Then: Error is shown with retry option
        XCTAssertNotNil(windowController.errorAlert)
        XCTAssertTrue(windowController.errorAlert!.hasRetryButton)
    }

    // MARK: - Performance Tests

    func testButtonAppearancePerformance() {
        measure {
            for _ in 0..<100 {
                windowController.handleTextSelection("Test", bounds: CGRect(x: 0, y: 0, width: 100, height: 20))
                windowController.handleSelectionCleared()
            }
        }
    }

    func testMenuOpenPerformance() {
        windowController.handleTextSelection("Test", bounds: CGRect(x: 0, y: 0, width: 100, height: 20))

        measure {
            for _ in 0..<50 {
                windowController.floatingButton!.performClick(nil)
                windowController.closeMenu()
            }
        }
    }

    // MARK: - Helper Methods

    private func findMenuItem(_ items: [MenuItem], title: String) -> MenuItem? {
        return items.first { $0.title == title }
    }
}

// MARK: - Mock Classes

class MockPythonService {
    var mockResponse: String?
    var lastCommand: [String: Any]?
    var replacedText: String?
    var shouldSimulateError = false

    func sendCommand(_ command: [String: Any]) async -> String {
        lastCommand = command

        if shouldSimulateError {
            return """
            {"status": "error", "message": "Network error"}
            """
        }

        return mockResponse ?? """
        {"status": "success", "result": {"text": "Default response"}}
        """
    }

    func replaceSelectedText(with text: String) {
        replacedText = text
    }
}

// MARK: - Test Extensions

extension InlineAIWindowController {
    var hasUndoEntry: Bool {
        return undoManager?.canUndo ?? false
    }

    var lastUndoOriginal: String? {
        // Implementation would retrieve last undo entry
        return nil // Placeholder
    }
}

extension MenuItem {
    func simulateMouseEnter() {
        // Simulate mouse enter event
        isHighlighted = true
    }

    func simulateMouseExit() {
        // Simulate mouse exit event
        isHighlighted = false
    }
}

extension MenuWindow {
    func hasSection(title: String) -> Bool {
        // Check if section with title exists
        return sections.contains { $0.title == title }
    }

    func getAllMenuItems() -> [MenuItem] {
        return sections.flatMap { $0.items }
    }
}
