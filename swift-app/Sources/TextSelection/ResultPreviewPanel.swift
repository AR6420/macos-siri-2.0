//
//  ResultPreviewPanel.swift
//  VoiceAssistant
//
//  Preview panel for text transformation results
//

import SwiftUI
import Cocoa

// MARK: - Preview Action

enum PreviewAction {
    case accept
    case reject
    case editFurther
    case copyResult
}

// MARK: - Result Preview Panel Window

class ResultPreviewPanelWindow: NSPanel {

    weak var actionHandler: ((PreviewAction) -> Void)?
    private var contentViewController: ResultPreviewViewController?

    init(originalText: String, modifiedText: String, operationType: String) {
        // Calculate window size based on content
        let windowSize = CGSize(width: 700, height: 500)

        // Center window on screen
        guard let screen = NSScreen.main else {
            super.init(
                contentRect: CGRect(origin: .zero, size: windowSize),
                styleMask: [.titled, .closable, .resizable],
                backing: .buffered,
                defer: false
            )
            return
        }

        let screenRect = screen.visibleFrame
        let originX = screenRect.midX - windowSize.width / 2
        let originY = screenRect.midY - windowSize.height / 2
        let rect = CGRect(
            x: originX,
            y: originY,
            width: windowSize.width,
            height: windowSize.height
        )

        super.init(
            contentRect: rect,
            styleMask: [.titled, .closable, .resizable],
            backing: .buffered,
            defer: false
        )

        // Configure panel
        self.title = "Preview Changes - \(operationType)"
        self.level = .floating
        self.isOpaque = true
        self.backgroundColor = .windowBackgroundColor
        self.hasShadow = true
        self.isMovableByWindowBackground = true
        self.minSize = CGSize(width: 500, height: 400)

        // Create SwiftUI view
        let contentView = ResultPreviewView(
            originalText: originalText,
            modifiedText: modifiedText,
            operationType: operationType
        ) { [weak self] action in
            self?.handleAction(action)
        }

        // Create hosting controller
        contentViewController = ResultPreviewViewController(rootView: contentView)
        self.contentViewController = contentViewController
    }

    private func handleAction(_ action: PreviewAction) {
        actionHandler?(action)

        // Close panel for accept/reject
        if action == .accept || action == .reject {
            close()
        }
    }

    func show() {
        makeKeyAndOrderFront(nil)
        center()
    }
}

// MARK: - Result Preview View Controller

class ResultPreviewViewController: NSHostingController<ResultPreviewView> {
    override func viewDidLoad() {
        super.viewDidLoad()
    }
}

// MARK: - Result Preview View

struct ResultPreviewView: View {

    let originalText: String
    let modifiedText: String
    let operationType: String
    let onAction: (PreviewAction) -> Void

    @State private var viewMode: ViewMode = .sideBySide
    @State private var editedText: String
    @State private var isEditing = false
    @State private var showCopyConfirmation = false

    enum ViewMode {
        case sideBySide
        case diff
        case modifiedOnly
    }

    init(originalText: String, modifiedText: String, operationType: String, onAction: @escaping (PreviewAction) -> Void) {
        self.originalText = originalText
        self.modifiedText = modifiedText
        self.operationType = operationType
        self.onAction = onAction
        self._editedText = State(initialValue: modifiedText)
    }

    var body: some View {
        VStack(spacing: 0) {
            // Header
            headerView

            Divider()

            // Content based on view mode
            contentView

            Divider()

            // Footer with actions
            footerView
        }
        .frame(minWidth: 500, minHeight: 400)
    }

    // MARK: - Header

    private var headerView: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("Preview: \(operationType)")
                    .font(.system(size: 16, weight: .semibold))

                HStack(spacing: 12) {
                    Label("\(originalText.count) chars", systemImage: "doc.text")
                    Image(systemName: "arrow.right")
                        .foregroundColor(.secondary)
                    Label("\(editedText.count) chars", systemImage: "doc.text.fill")

                    if originalText.count != editedText.count {
                        let diff = editedText.count - originalText.count
                        Text(diff > 0 ? "+\(diff)" : "\(diff)")
                            .font(.system(size: 11, weight: .medium))
                            .foregroundColor(diff > 0 ? .green : .red)
                    }
                }
                .font(.system(size: 11))
                .foregroundColor(.secondary)
            }

            Spacer()

            // View mode picker
            Picker("View Mode", selection: $viewMode) {
                Label("Side by Side", systemImage: "rectangle.split.2x1")
                    .tag(ViewMode.sideBySide)
                Label("Show Changes", systemImage: "doc.text.magnifyingglass")
                    .tag(ViewMode.diff)
                Label("Result Only", systemImage: "doc.text")
                    .tag(ViewMode.modifiedOnly)
            }
            .pickerStyle(.segmented)
            .frame(width: 320)
        }
        .padding()
        .background(Color(nsColor: .controlBackgroundColor))
    }

    // MARK: - Content

    @ViewBuilder
    private var contentView: some View {
        switch viewMode {
        case .sideBySide:
            sideBySideView

        case .diff:
            diffView

        case .modifiedOnly:
            modifiedOnlyView
        }
    }

    private var sideBySideView: some View {
        HStack(spacing: 0) {
            // Original text (left)
            VStack(alignment: .leading, spacing: 0) {
                Text("Original")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundColor(.secondary)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(Color(nsColor: .controlBackgroundColor))

                ScrollView {
                    Text(originalText)
                        .font(.system(size: 12, design: .monospaced))
                        .textSelection(.enabled)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding()
                }
            }

            Divider()

            // Modified text (right)
            VStack(alignment: .leading, spacing: 0) {
                HStack {
                    Text(isEditing ? "Editing Result" : "Result")
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundColor(.secondary)

                    Spacer()

                    Button(action: { isEditing.toggle() }) {
                        Image(systemName: isEditing ? "checkmark.circle.fill" : "pencil.circle")
                            .font(.system(size: 14))
                    }
                    .buttonStyle(.plain)
                    .help(isEditing ? "Finish editing" : "Edit result")
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(Color(nsColor: .controlBackgroundColor))

                if isEditing {
                    TextEditor(text: $editedText)
                        .font(.system(size: 12, design: .monospaced))
                        .padding(12)
                        .scrollContentBackground(.hidden)
                } else {
                    ScrollView {
                        Text(editedText)
                            .font(.system(size: 12, design: .monospaced))
                            .textSelection(.enabled)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .padding()
                    }
                }
            }
        }
    }

    private var diffView: some View {
        DiffView(
            originalText: originalText,
            modifiedText: editedText,
            showLineNumbers: true
        )
    }

    private var modifiedOnlyView: some View {
        VStack(alignment: .leading, spacing: 0) {
            HStack {
                Text(isEditing ? "Editing Result" : "Result")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundColor(.secondary)

                Spacer()

                Button(action: { isEditing.toggle() }) {
                    HStack(spacing: 4) {
                        Image(systemName: isEditing ? "checkmark.circle.fill" : "pencil")
                        Text(isEditing ? "Done" : "Edit")
                            .font(.system(size: 11))
                    }
                    .foregroundColor(.accentColor)
                }
                .buttonStyle(.plain)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(Color(nsColor: .controlBackgroundColor))

            if isEditing {
                VStack(spacing: 0) {
                    TextEditor(text: $editedText)
                        .font(.system(size: 13))
                        .padding(16)
                        .scrollContentBackground(.hidden)

                    // Character count
                    HStack {
                        Text("\(editedText.count) characters")
                            .font(.system(size: 10))
                            .foregroundColor(.secondary)

                        Spacer()
                    }
                    .padding(.horizontal, 16)
                    .padding(.bottom, 8)
                }
            } else {
                ScrollView {
                    Text(editedText)
                        .font(.system(size: 13))
                        .textSelection(.enabled)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(16)
                }
            }
        }
    }

    // MARK: - Footer

    private var footerView: some View {
        HStack(spacing: 12) {
            // Statistics
            VStack(alignment: .leading, spacing: 2) {
                if originalText != editedText {
                    Text("\(changesCount) changes")
                        .font(.system(size: 11))
                        .foregroundColor(.secondary)
                } else {
                    Text("No changes")
                        .font(.system(size: 11))
                        .foregroundColor(.secondary)
                }
            }

            Spacer()

            // Copy button
            Button(action: copyResult) {
                HStack(spacing: 6) {
                    Image(systemName: showCopyConfirmation ? "checkmark" : "doc.on.doc")
                    Text(showCopyConfirmation ? "Copied!" : "Copy")
                }
                .font(.system(size: 12, weight: .medium))
            }
            .buttonStyle(.borderless)

            // Edit further button
            Button(action: {
                onAction(.editFurther)
            }) {
                Text("Edit Further")
                    .font(.system(size: 12, weight: .medium))
            }
            .buttonStyle(.borderless)

            // Reject button
            Button(action: {
                onAction(.reject)
            }) {
                Text("Reject")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(.secondary)
            }
            .buttonStyle(.borderless)
            .keyboardShortcut(.cancelAction)

            // Accept button
            Button(action: {
                onAction(.accept)
            }) {
                Text("Accept & Replace")
                    .font(.system(size: 12, weight: .semibold))
            }
            .buttonStyle(.borderedProminent)
            .keyboardShortcut(.defaultAction)
        }
        .padding()
        .background(Color(nsColor: .controlBackgroundColor))
    }

    // MARK: - Actions

    private func copyResult() {
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(editedText, forType: .string)

        showCopyConfirmation = true
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
            showCopyConfirmation = false
        }

        onAction(.copyResult)
    }

    private var changesCount: Int {
        // Simple character diff count
        let originalChars = Set(originalText)
        let modifiedChars = Set(editedText)
        return originalChars.symmetricDifference(modifiedChars).count
    }
}

// MARK: - Compact Preview View

struct CompactPreviewView: View {

    let originalText: String
    let modifiedText: String
    let onAccept: () -> Void
    let onReject: () -> Void

    var body: some View {
        VStack(spacing: 12) {
            // Header
            HStack {
                Image(systemName: "sparkles")
                    .foregroundColor(.accentColor)
                Text("Preview Changes")
                    .font(.system(size: 13, weight: .semibold))

                Spacer()

                Button(action: onReject) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(.secondary)
                }
                .buttonStyle(.plain)
            }

            // Before/After
            VStack(spacing: 8) {
                previewBox(title: "Before", text: originalText, color: .red)
                Image(systemName: "arrow.down")
                    .foregroundColor(.secondary)
                previewBox(title: "After", text: modifiedText, color: .green)
            }

            // Actions
            HStack(spacing: 12) {
                Button("Reject") {
                    onReject()
                }
                .buttonStyle(.bordered)

                Button("Accept") {
                    onAccept()
                }
                .buttonStyle(.borderedProminent)
            }
        }
        .padding(16)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(nsColor: .windowBackgroundColor))
                .shadow(radius: 10)
        )
        .frame(width: 350)
    }

    private func previewBox(title: String, text: String, color: Color) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.system(size: 10, weight: .semibold))
                .foregroundColor(.secondary)

            Text(text)
                .font(.system(size: 11, design: .monospaced))
                .lineLimit(3)
                .truncationMode(.tail)
                .padding(8)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(
                    RoundedRectangle(cornerRadius: 6)
                        .fill(color.opacity(0.1))
                        .overlay(
                            RoundedRectangle(cornerRadius: 6)
                                .stroke(color.opacity(0.3), lineWidth: 1)
                        )
                )
        }
    }
}

// MARK: - Preview

struct ResultPreviewView_Previews: PreviewProvider {
    static var previews: some View {
        Group {
            ResultPreviewView(
                originalText: "This is the original text that needs to be improved. It might contain some errors or could be better written.",
                modifiedText: "This is the improved text with better clarity and structure. All errors have been corrected for better readability.",
                operationType: "Rewrite (Professional)",
                onAction: { _ in }
            )
            .previewDisplayName("Full Preview")

            CompactPreviewView(
                originalText: "Original text here",
                modifiedText: "Modified text here with improvements",
                onAccept: {},
                onReject: {}
            )
            .previewDisplayName("Compact Preview")
        }
    }
}
