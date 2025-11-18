//
//  DiffView.swift
//  VoiceAssistant
//
//  Displays text differences with inline highlighting
//

import SwiftUI
import Cocoa

// MARK: - Diff Change Type

enum DiffChangeType {
    case deletion
    case insertion
    case modification
    case unchanged
}

// MARK: - Diff Segment

struct DiffSegment: Identifiable {
    let id = UUID()
    let text: String
    let changeType: DiffChangeType
    let lineNumber: Int?

    var backgroundColor: Color {
        switch changeType {
        case .deletion:
            return Color.red.opacity(0.15)
        case .insertion:
            return Color.green.opacity(0.15)
        case .modification:
            return Color.yellow.opacity(0.15)
        case .unchanged:
            return Color.clear
        }
    }

    var borderColor: Color {
        switch changeType {
        case .deletion:
            return Color.red.opacity(0.3)
        case .insertion:
            return Color.green.opacity(0.3)
        case .modification:
            return Color.yellow.opacity(0.3)
        case .unchanged:
            return Color.clear
        }
    }

    var icon: String? {
        switch changeType {
        case .deletion:
            return "minus.circle.fill"
        case .insertion:
            return "plus.circle.fill"
        case .modification:
            return "pencil.circle.fill"
        case .unchanged:
            return nil
        }
    }

    var iconColor: Color {
        switch changeType {
        case .deletion:
            return .red
        case .insertion:
            return .green
        case .modification:
            return .orange
        case .unchanged:
            return .clear
        }
    }
}

// MARK: - Diff View

struct DiffView: View {

    let originalText: String
    let modifiedText: String
    let showLineNumbers: Bool

    @State private var diffSegments: [DiffSegment] = []
    @State private var selectedChangeIndex: Int?
    @State private var viewMode: DiffViewMode = .sideBySide

    enum DiffViewMode {
        case sideBySide
        case unified
        case inline
    }

    init(originalText: String, modifiedText: String, showLineNumbers: Bool = true) {
        self.originalText = originalText
        self.modifiedText = modifiedText
        self.showLineNumbers = showLineNumbers
    }

    var body: some View {
        VStack(spacing: 0) {
            // Header with view mode selector
            DiffViewHeader(viewMode: $viewMode)

            Divider()

            // Diff content based on view mode
            switch viewMode {
            case .sideBySide:
                SideBySideDiffView(
                    originalText: originalText,
                    modifiedText: modifiedText,
                    showLineNumbers: showLineNumbers
                )

            case .unified:
                UnifiedDiffView(
                    originalText: originalText,
                    modifiedText: modifiedText,
                    showLineNumbers: showLineNumbers
                )

            case .inline:
                InlineDiffView(
                    originalText: originalText,
                    modifiedText: modifiedText
                )
            }
        }
    }
}

// MARK: - Diff View Header

struct DiffViewHeader: View {

    @Binding var viewMode: DiffView.DiffViewMode

    var body: some View {
        HStack {
            Text("Changes Preview")
                .font(.system(size: 13, weight: .semibold))

            Spacer()

            // View mode picker
            Picker("View Mode", selection: $viewMode) {
                Text("Side by Side").tag(DiffView.DiffViewMode.sideBySide)
                Text("Unified").tag(DiffView.DiffViewMode.unified)
                Text("Inline").tag(DiffView.DiffViewMode.inline)
            }
            .pickerStyle(.segmented)
            .frame(width: 250)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 10)
        .background(Color(nsColor: .controlBackgroundColor))
    }
}

// MARK: - Side-by-Side Diff View

struct SideBySideDiffView: View {

    let originalText: String
    let modifiedText: String
    let showLineNumbers: Bool

    var body: some View {
        HStack(spacing: 0) {
            // Original text (left)
            VStack(alignment: .leading, spacing: 0) {
                // Header
                Text("Original")
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundColor(.secondary)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(Color.red.opacity(0.1))

                // Content
                ScrollView {
                    TextWithLineNumbers(
                        text: originalText,
                        showLineNumbers: showLineNumbers,
                        highlightColor: .red.opacity(0.15)
                    )
                }
            }

            Divider()

            // Modified text (right)
            VStack(alignment: .leading, spacing: 0) {
                // Header
                Text("Modified")
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundColor(.secondary)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(Color.green.opacity(0.1))

                // Content
                ScrollView {
                    TextWithLineNumbers(
                        text: modifiedText,
                        showLineNumbers: showLineNumbers,
                        highlightColor: .green.opacity(0.15)
                    )
                }
            }
        }
    }
}

// MARK: - Unified Diff View

struct UnifiedDiffView: View {

    let originalText: String
    let modifiedText: String
    let showLineNumbers: Bool

    @State private var diffLines: [DiffLine] = []

    struct DiffLine: Identifiable {
        let id = UUID()
        let content: String
        let type: DiffChangeType
        let lineNumber: Int?
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 1) {
                ForEach(computeDiffLines()) { line in
                    HStack(spacing: 8) {
                        // Line number
                        if showLineNumbers {
                            Text(line.lineNumber.map { String($0) } ?? "-")
                                .font(.system(size: 10, design: .monospaced))
                                .foregroundColor(.secondary)
                                .frame(width: 40, alignment: .trailing)
                        }

                        // Change indicator
                        if let icon = line.icon {
                            Image(systemName: icon)
                                .font(.system(size: 10))
                                .foregroundColor(line.iconColor)
                                .frame(width: 16)
                        }

                        // Content
                        Text(line.content)
                            .font(.system(size: 11, design: .monospaced))
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                    .padding(.horizontal, 12)
                    .padding(.vertical, 4)
                    .background(line.backgroundColor)
                    .overlay(
                        Rectangle()
                            .fill(line.borderColor)
                            .frame(width: 3)
                        , alignment: .leading
                    )
                }
            }
        }
    }

    private func computeDiffLines() -> [DiffLine] {
        let originalLines = originalText.components(separatedBy: .newlines)
        let modifiedLines = modifiedText.components(separatedBy: .newlines)

        var result: [DiffLine] = []
        let diff = computeLineDiff(original: originalLines, modified: modifiedLines)

        for (index, change) in diff.enumerated() {
            switch change {
            case .deletion(let text):
                result.append(DiffLine(
                    content: text,
                    type: .deletion,
                    lineNumber: nil
                ))

            case .insertion(let text):
                result.append(DiffLine(
                    content: text,
                    type: .insertion,
                    lineNumber: index + 1
                ))

            case .unchanged(let text):
                result.append(DiffLine(
                    content: text,
                    type: .unchanged,
                    lineNumber: index + 1
                ))
            }
        }

        return result
    }
}

// MARK: - Inline Diff View

struct InlineDiffView: View {

    let originalText: String
    let modifiedText: String

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                // Show word-level differences inline
                ForEach(computeInlineDiffs(), id: \.offset) { item in
                    HStack(alignment: .top, spacing: 8) {
                        // Change type indicator
                        if let icon = item.element.icon {
                            Image(systemName: icon)
                                .font(.system(size: 12))
                                .foregroundColor(item.element.iconColor)
                        }

                        // Text with inline highlighting
                        Text(attributedString(for: item.element))
                            .font(.system(size: 12))
                            .textSelection(.enabled)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                    .padding(12)
                    .background(item.element.backgroundColor)
                    .cornerRadius(6)
                }
            }
            .padding()
        }
    }

    private func computeInlineDiffs() -> [(offset: Int, element: DiffSegment)] {
        // Simple word-level diff
        let originalWords = originalText.components(separatedBy: .whitespaces)
        let modifiedWords = modifiedText.components(separatedBy: .whitespaces)

        var segments: [DiffSegment] = []

        // Simplified diff - mark deletions and insertions
        if originalText != modifiedText {
            segments.append(DiffSegment(
                text: originalText,
                changeType: .deletion,
                lineNumber: nil
            ))

            segments.append(DiffSegment(
                text: modifiedText,
                changeType: .insertion,
                lineNumber: nil
            ))
        } else {
            segments.append(DiffSegment(
                text: originalText,
                changeType: .unchanged,
                lineNumber: nil
            ))
        }

        return Array(segments.enumerated())
    }

    private func attributedString(for segment: DiffSegment) -> AttributedString {
        var attributed = AttributedString(segment.text)
        attributed.font = .systemFont(ofSize: 12, weight: .regular)
        return attributed
    }
}

// MARK: - Text with Line Numbers

struct TextWithLineNumbers: View {

    let text: String
    let showLineNumbers: Bool
    let highlightColor: Color

    var lines: [String] {
        text.components(separatedBy: .newlines)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            ForEach(Array(lines.enumerated()), id: \.offset) { index, line in
                HStack(spacing: 8) {
                    if showLineNumbers {
                        Text("\(index + 1)")
                            .font(.system(size: 10, design: .monospaced))
                            .foregroundColor(.secondary)
                            .frame(width: 40, alignment: .trailing)
                    }

                    Text(line.isEmpty ? " " : line)
                        .font(.system(size: 11, design: .monospaced))
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 2)
                .background(highlightColor)
            }
        }
    }
}

// MARK: - Diff Algorithm Helpers

enum DiffChange {
    case deletion(String)
    case insertion(String)
    case unchanged(String)
}

extension DiffLine {
    var backgroundColor: Color {
        switch type {
        case .deletion:
            return Color.red.opacity(0.15)
        case .insertion:
            return Color.green.opacity(0.15)
        case .modification:
            return Color.yellow.opacity(0.15)
        case .unchanged:
            return Color.clear
        }
    }

    var borderColor: Color {
        switch type {
        case .deletion:
            return Color.red.opacity(0.5)
        case .insertion:
            return Color.green.opacity(0.5)
        case .modification:
            return Color.yellow.opacity(0.5)
        case .unchanged:
            return Color.clear
        }
    }

    var icon: String? {
        switch type {
        case .deletion:
            return "minus.circle.fill"
        case .insertion:
            return "plus.circle.fill"
        case .modification:
            return "pencil.circle.fill"
        case .unchanged:
            return nil
        }
    }

    var iconColor: Color {
        switch type {
        case .deletion:
            return .red
        case .insertion:
            return .green
        case .modification:
            return .orange
        case .unchanged:
            return .clear
        }
    }
}

func computeLineDiff(original: [String], modified: [String]) -> [DiffChange] {
    // Simple line-by-line diff using LCS algorithm
    var result: [DiffChange] = []

    let lcs = longestCommonSubsequence(original, modified)
    var origIndex = 0
    var modIndex = 0
    var lcsIndex = 0

    while origIndex < original.count || modIndex < modified.count {
        if lcsIndex < lcs.count && origIndex < original.count && original[origIndex] == lcs[lcsIndex] {
            result.append(.unchanged(original[origIndex]))
            origIndex += 1
            modIndex += 1
            lcsIndex += 1
        } else if origIndex < original.count && (lcsIndex >= lcs.count || original[origIndex] != lcs[lcsIndex]) {
            result.append(.deletion(original[origIndex]))
            origIndex += 1
        } else if modIndex < modified.count {
            result.append(.insertion(modified[modIndex]))
            modIndex += 1
        }
    }

    return result
}

func longestCommonSubsequence<T: Equatable>(_ a: [T], _ b: [T]) -> [T] {
    let m = a.count
    let n = b.count

    var dp = Array(repeating: Array(repeating: 0, count: n + 1), count: m + 1)

    for i in 1...m {
        for j in 1...n {
            if a[i - 1] == b[j - 1] {
                dp[i][j] = dp[i - 1][j - 1] + 1
            } else {
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
            }
        }
    }

    // Backtrack to find LCS
    var lcs: [T] = []
    var i = m
    var j = n

    while i > 0 && j > 0 {
        if a[i - 1] == b[j - 1] {
            lcs.insert(a[i - 1], at: 0)
            i -= 1
            j -= 1
        } else if dp[i - 1][j] > dp[i][j - 1] {
            i -= 1
        } else {
            j -= 1
        }
    }

    return lcs
}

// MARK: - Preview

struct DiffView_Previews: PreviewProvider {
    static var previews: some View {
        DiffView(
            originalText: "Hello world!\nThis is a test.\nOriginal text here.",
            modifiedText: "Hello world!\nThis is a modified test.\nNew text here.",
            showLineNumbers: true
        )
        .frame(width: 800, height: 500)
    }
}
