//
//  MenuOptionTests.swift
//  VoiceAssistantTests
//
//  Unit tests for MenuOption enum and command generation
//

import XCTest
@testable import VoiceAssistant

class MenuOptionTests: XCTestCase {

    // MARK: - Display Properties Tests

    func testDisplayNames() {
        XCTAssertEqual(MenuOption.proofread.displayName, "Proofread")
        XCTAssertEqual(MenuOption.rewrite.displayName, "Rewrite")
        XCTAssertEqual(MenuOption.friendly.displayName, "Friendly")
        XCTAssertEqual(MenuOption.professional.displayName, "Professional")
        XCTAssertEqual(MenuOption.concise.displayName, "Concise")
        XCTAssertEqual(MenuOption.summary.displayName, "Summary")
        XCTAssertEqual(MenuOption.keyPoints.displayName, "Key Points")
        XCTAssertEqual(MenuOption.list.displayName, "List")
        XCTAssertEqual(MenuOption.table.displayName, "Table")
        XCTAssertEqual(MenuOption.compose.displayName, "Compose...")
    }

    func testIcons() {
        XCTAssertEqual(MenuOption.proofread.icon, "magnifyingglass")
        XCTAssertEqual(MenuOption.rewrite.icon, "arrow.clockwise")
        XCTAssertEqual(MenuOption.friendly.icon, "face.smiling")
        XCTAssertEqual(MenuOption.professional.icon, "briefcase.fill")
        XCTAssertEqual(MenuOption.concise.icon, "equal")
        XCTAssertEqual(MenuOption.summary.icon, "list.bullet")
        XCTAssertEqual(MenuOption.keyPoints.icon, "list.bullet.circle")
        XCTAssertEqual(MenuOption.list.icon, "checklist")
        XCTAssertEqual(MenuOption.table.icon, "tablecells")
        XCTAssertEqual(MenuOption.compose.icon, "pencil.line")
    }

    // MARK: - Section Tests

    func testSections() {
        XCTAssertEqual(MenuOption.proofread.section, .primary)
        XCTAssertEqual(MenuOption.rewrite.section, .primary)
        XCTAssertEqual(MenuOption.friendly.section, .style)
        XCTAssertEqual(MenuOption.professional.section, .style)
        XCTAssertEqual(MenuOption.concise.section, .style)
        XCTAssertEqual(MenuOption.summary.section, .formatting)
        XCTAssertEqual(MenuOption.keyPoints.section, .formatting)
        XCTAssertEqual(MenuOption.list.section, .formatting)
        XCTAssertEqual(MenuOption.table.section, .formatting)
        XCTAssertEqual(MenuOption.compose.section, .compose)
    }

    // MARK: - Command Generation Tests

    func testProofreadCommand() {
        let text = "This is a test text with some errors."
        let command = MenuOption.proofread.generateCommand(for: text)

        XCTAssertEqual(command["command"] as? String, "proofread_text")
        XCTAssertEqual(command["text"] as? String, text)
        XCTAssertNil(command["custom_input"])
    }

    func testRewriteCommand() {
        let text = "This is a test text."
        let command = MenuOption.rewrite.generateCommand(for: text)

        XCTAssertEqual(command["command"] as? String, "rewrite_text")
        XCTAssertEqual(command["text"] as? String, text)
    }

    func testStyleCommands() {
        let text = "This is a test text."

        let friendlyCommand = MenuOption.friendly.generateCommand(for: text)
        XCTAssertEqual(friendlyCommand["command"] as? String, "change_style")
        XCTAssertEqual(friendlyCommand["style"] as? String, "friendly")

        let professionalCommand = MenuOption.professional.generateCommand(for: text)
        XCTAssertEqual(professionalCommand["command"] as? String, "change_style")
        XCTAssertEqual(professionalCommand["style"] as? String, "professional")

        let conciseCommand = MenuOption.concise.generateCommand(for: text)
        XCTAssertEqual(conciseCommand["command"] as? String, "change_style")
        XCTAssertEqual(conciseCommand["style"] as? String, "concise")
    }

    func testSummaryCommand() {
        let text = "This is a long text that needs to be summarized."
        let command = MenuOption.summary.generateCommand(for: text)

        XCTAssertEqual(command["command"] as? String, "summarize_text")
        XCTAssertEqual(command["text"] as? String, text)
    }

    func testKeyPointsCommand() {
        let text = "This text has multiple key points to extract."
        let command = MenuOption.keyPoints.generateCommand(for: text)

        XCTAssertEqual(command["command"] as? String, "extract_key_points")
        XCTAssertEqual(command["text"] as? String, text)
    }

    func testListCommand() {
        let text = "First item. Second item. Third item."
        let command = MenuOption.list.generateCommand(for: text)

        XCTAssertEqual(command["command"] as? String, "convert_to_list")
        XCTAssertEqual(command["text"] as? String, text)
    }

    func testTableCommand() {
        let text = "Data that should be in table format."
        let command = MenuOption.table.generateCommand(for: text)

        XCTAssertEqual(command["command"] as? String, "convert_to_table")
        XCTAssertEqual(command["text"] as? String, text)
    }

    func testComposeCommand() {
        let text = "Selected text for context"
        let customInput = "Write a poem about nature"
        let command = MenuOption.compose.generateCommand(for: text, customInput: customInput)

        XCTAssertEqual(command["command"] as? String, "compose_text")
        XCTAssertEqual(command["text"] as? String, text)
        XCTAssertEqual(command["custom_input"] as? String, customInput)
    }

    func testCustomInputIncluded() {
        let text = "Some text"
        let customInput = "Make it funny"
        let command = MenuOption.rewrite.generateCommand(for: text, customInput: customInput)

        XCTAssertEqual(command["custom_input"] as? String, customInput)
    }

    func testCustomInputOmittedWhenEmpty() {
        let text = "Some text"
        let command = MenuOption.rewrite.generateCommand(for: text, customInput: "")

        XCTAssertNil(command["custom_input"])
    }

    func testCustomInputOmittedWhenNil() {
        let text = "Some text"
        let command = MenuOption.rewrite.generateCommand(for: text, customInput: nil)

        XCTAssertNil(command["custom_input"])
    }

    // MARK: - Static Collections Tests

    func testPrimaryOptions() {
        let primary = MenuOption.primaryOptions
        XCTAssertEqual(primary.count, 2)
        XCTAssertTrue(primary.contains(.proofread))
        XCTAssertTrue(primary.contains(.rewrite))
    }

    func testStyleOptions() {
        let style = MenuOption.styleOptions
        XCTAssertEqual(style.count, 3)
        XCTAssertTrue(style.contains(.friendly))
        XCTAssertTrue(style.contains(.professional))
        XCTAssertTrue(style.contains(.concise))
    }

    func testFormattingOptions() {
        let formatting = MenuOption.formattingOptions
        XCTAssertEqual(formatting.count, 4)
        XCTAssertTrue(formatting.contains(.summary))
        XCTAssertTrue(formatting.contains(.keyPoints))
        XCTAssertTrue(formatting.contains(.list))
        XCTAssertTrue(formatting.contains(.table))
    }

    func testComposeOptionStatic() {
        XCTAssertEqual(MenuOption.composeOption, .compose)
    }

    // MARK: - Menu Section Tests

    func testMenuSectionTitles() {
        XCTAssertNil(MenuSection.input.title)
        XCTAssertNil(MenuSection.primary.title)
        XCTAssertEqual(MenuSection.style.title, "Style")
        XCTAssertEqual(MenuSection.formatting.title, "Format")
        XCTAssertNil(MenuSection.compose.title)
    }

    func testMenuSectionDividers() {
        XCTAssertFalse(MenuSection.input.showDividerBefore)
        XCTAssertFalse(MenuSection.primary.showDividerBefore)
        XCTAssertTrue(MenuSection.style.showDividerBefore)
        XCTAssertTrue(MenuSection.formatting.showDividerBefore)
        XCTAssertTrue(MenuSection.compose.showDividerBefore)
    }

    // MARK: - All Cases Test

    func testAllCasesCount() {
        XCTAssertEqual(MenuOption.allCases.count, 10)
    }
}
