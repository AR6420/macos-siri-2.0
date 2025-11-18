//
//  MenuOption.swift
//  VoiceAssistant
//
//  Menu options for the enhanced inline AI interface
//

import Foundation

// MARK: - Menu Option

enum MenuOption: String, CaseIterable {
    // Primary actions
    case proofread
    case rewrite

    // Style options
    case friendly
    case professional
    case concise

    // Formatting/Structure
    case summary
    case keyPoints
    case list
    case table

    // Compose
    case compose

    // MARK: - Display Properties

    var displayName: String {
        switch self {
        case .proofread:
            return "Proofread"
        case .rewrite:
            return "Rewrite"
        case .friendly:
            return "Friendly"
        case .professional:
            return "Professional"
        case .concise:
            return "Concise"
        case .summary:
            return "Summary"
        case .keyPoints:
            return "Key Points"
        case .list:
            return "List"
        case .table:
            return "Table"
        case .compose:
            return "Compose..."
        }
    }

    var icon: String {
        switch self {
        case .proofread:
            return "magnifyingglass"
        case .rewrite:
            return "arrow.clockwise"
        case .friendly:
            return "face.smiling"
        case .professional:
            return "briefcase.fill"
        case .concise:
            return "equal"
        case .summary:
            return "list.bullet"
        case .keyPoints:
            return "list.bullet.circle"
        case .list:
            return "checklist"
        case .table:
            return "tablecells"
        case .compose:
            return "pencil.line"
        }
    }

    var section: MenuSection {
        switch self {
        case .proofread, .rewrite:
            return .primary
        case .friendly, .professional, .concise:
            return .style
        case .summary, .keyPoints, .list, .table:
            return .formatting
        case .compose:
            return .compose
        }
    }

    // MARK: - Command Generation

    func generateCommand(for text: String, customInput: String? = nil) -> [String: Any] {
        var command: [String: Any] = [
            "command": commandName,
            "text": text
        ]

        // Add custom input if provided
        if let input = customInput, !input.isEmpty {
            command["custom_input"] = input
        }

        // Add style parameter for style options
        if section == .style {
            command["style"] = rawValue
        }

        return command
    }

    private var commandName: String {
        switch self {
        case .proofread:
            return "proofread_text"
        case .rewrite:
            return "rewrite_text"
        case .friendly, .professional, .concise:
            return "change_style"
        case .summary:
            return "summarize_text"
        case .keyPoints:
            return "extract_key_points"
        case .list:
            return "convert_to_list"
        case .table:
            return "convert_to_table"
        case .compose:
            return "compose_text"
        }
    }
}

// MARK: - Menu Section

enum MenuSection: Int, CaseIterable {
    case input = 0
    case primary = 1
    case style = 2
    case formatting = 3
    case compose = 4

    var title: String? {
        switch self {
        case .input:
            return nil
        case .primary:
            return nil
        case .style:
            return "Style"
        case .formatting:
            return "Format"
        case .compose:
            return nil
        }
    }

    var showDividerBefore: Bool {
        switch self {
        case .input, .primary:
            return false
        case .style, .formatting, .compose:
            return true
        }
    }
}

// MARK: - Menu Option Extensions

extension MenuOption {

    /// Primary action options (shown at top)
    static var primaryOptions: [MenuOption] {
        [.proofread, .rewrite]
    }

    /// Style options (horizontal row)
    static var styleOptions: [MenuOption] {
        [.friendly, .professional, .concise]
    }

    /// Formatting options (2x2 grid)
    static var formattingOptions: [MenuOption] {
        [.summary, .keyPoints, .list, .table]
    }

    /// Compose option (bottom)
    static var composeOption: MenuOption {
        .compose
    }
}
