//
//  EditableTextSection.swift
//  VoiceAssistant
//
//  Editable text input section for inline AI panel
//

import SwiftUI
import Cocoa

// MARK: - Editable Text Section

struct EditableTextSection: View {

    @Binding var text: String
    @State private var isEditing = false
    @State private var showCharacterWarning = false

    let maxLength: Int = 5000
    let minLength: Int = 1
    let placeholder: String = "Enter or edit text..."

    var characterCount: Int {
        text.count
    }

    var isValid: Bool {
        characterCount >= minLength && characterCount <= maxLength
    }

    var characterCountColor: Color {
        if characterCount == 0 {
            return .gray
        } else if characterCount > maxLength {
            return .red
        } else if characterCount > maxLength - 500 {
            return .orange
        } else {
            return .secondary
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            // Header
            HStack {
                Text("Edit Text")
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundColor(.secondary)

                Spacer()

                // Quick actions
                HStack(spacing: 8) {
                    // Copy button
                    Button(action: copyText) {
                        Image(systemName: "doc.on.doc")
                            .font(.system(size: 10))
                    }
                    .buttonStyle(.plain)
                    .help("Copy text")

                    // Paste button
                    Button(action: pasteText) {
                        Image(systemName: "doc.on.clipboard")
                            .font(.system(size: 10))
                    }
                    .buttonStyle(.plain)
                    .help("Paste from clipboard")

                    // Clear button
                    if !text.isEmpty {
                        Button(action: clearText) {
                            Image(systemName: "xmark.circle.fill")
                                .font(.system(size: 10))
                                .foregroundColor(.secondary)
                        }
                        .buttonStyle(.plain)
                        .help("Clear text")
                    }
                }
                .foregroundColor(.secondary)
            }

            // Text editor
            ZStack(alignment: .topLeading) {
                // Background
                RoundedRectangle(cornerRadius: 8)
                    .fill(Color(nsColor: .textBackgroundColor))
                    .overlay(
                        RoundedRectangle(cornerRadius: 8)
                            .stroke(isEditing ? Color.accentColor : Color.gray.opacity(0.3), lineWidth: isEditing ? 2 : 1)
                    )

                // Placeholder
                if text.isEmpty {
                    Text(placeholder)
                        .font(.system(size: 12))
                        .foregroundColor(.secondary.opacity(0.5))
                        .padding(.horizontal, 12)
                        .padding(.vertical, 10)
                        .allowsHitTesting(false)
                }

                // Text editor
                TextEditor(text: $text)
                    .font(.system(size: 12))
                    .frame(minHeight: 60, maxHeight: 120)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 6)
                    .background(Color.clear)
                    .scrollContentBackground(.hidden)
                    .onTapGesture {
                        isEditing = true
                    }
                    .onChange(of: text) { oldValue, newValue in
                        // Enforce max length
                        if newValue.count > maxLength {
                            text = String(newValue.prefix(maxLength))
                            showCharacterWarning = true

                            // Hide warning after delay
                            DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                                showCharacterWarning = false
                            }
                        }
                    }
            }
            .frame(height: 120)

            // Footer with character count and warnings
            HStack(spacing: 8) {
                // Character count
                HStack(spacing: 4) {
                    Image(systemName: characterCount > maxLength ? "exclamationmark.triangle.fill" : "text.alignleft")
                        .font(.system(size: 9))

                    Text("\(characterCount) / \(maxLength)")
                        .font(.system(size: 10, weight: .medium))
                }
                .foregroundColor(characterCountColor)

                Spacer()

                // Warning message
                if showCharacterWarning {
                    Text("Maximum length reached")
                        .font(.system(size: 10, weight: .medium))
                        .foregroundColor(.red)
                        .transition(.opacity)
                        .animation(.easeInOut, value: showCharacterWarning)
                }

                // Validation status
                if characterCount > 0 {
                    HStack(spacing: 4) {
                        Image(systemName: isValid ? "checkmark.circle.fill" : "xmark.circle.fill")
                            .font(.system(size: 9))
                        Text(isValid ? "Valid" : "Invalid")
                            .font(.system(size: 10))
                    }
                    .foregroundColor(isValid ? .green : .red)
                }
            }
            .padding(.horizontal, 2)
        }
    }

    // MARK: - Actions

    private func copyText() {
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(text, forType: .string)

        // Show brief feedback
        NSHapticFeedbackManager.defaultPerformer.perform(.levelChange, performanceTime: .default)
    }

    private func pasteText() {
        let pasteboard = NSPasteboard.general
        if let clipboardText = pasteboard.string(forType: .string) {
            text = clipboardText
            NSHapticFeedbackManager.defaultPerformer.perform(.levelChange, performanceTime: .default)
        }
    }

    private func clearText() {
        text = ""
        NSHapticFeedbackManager.defaultPerformer.perform(.levelChange, performanceTime: .default)
    }
}

// MARK: - Compact Editable Text Section

struct CompactEditableTextSection: View {

    @Binding var text: String
    @State private var isExpanded = false

    let maxLength: Int = 5000

    var characterCount: Int {
        text.count
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            // Collapsed view - one line
            if !isExpanded {
                HStack(spacing: 8) {
                    Text(text.isEmpty ? "No text selected" : text)
                        .font(.system(size: 11))
                        .foregroundColor(text.isEmpty ? .secondary : .primary)
                        .lineLimit(1)
                        .truncationMode(.tail)

                    Spacer()

                    Button(action: { isExpanded = true }) {
                        Image(systemName: "pencil.circle.fill")
                            .font(.system(size: 14))
                            .foregroundColor(.accentColor)
                    }
                    .buttonStyle(.plain)
                    .help("Edit text")
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(
                    RoundedRectangle(cornerRadius: 6)
                        .fill(Color.gray.opacity(0.1))
                )
                .onTapGesture {
                    isExpanded = true
                }
            }

            // Expanded view - full editor
            if isExpanded {
                VStack(spacing: 8) {
                    EditableTextSection(text: $text)

                    HStack {
                        Spacer()

                        Button("Done") {
                            isExpanded = false
                        }
                        .buttonStyle(.borderedProminent)
                        .controlSize(.small)
                    }
                }
                .padding(8)
                .background(
                    RoundedRectangle(cornerRadius: 8)
                        .fill(Color(nsColor: .windowBackgroundColor))
                        .shadow(radius: 4)
                )
            }
        }
        .animation(.easeInOut(duration: 0.2), value: isExpanded)
    }
}

// MARK: - Multi-line Text Field (NSTextView wrapper)

struct MultilineTextField: NSViewRepresentable {

    @Binding var text: String
    var font: NSFont = .systemFont(ofSize: 12)
    var isEditable: Bool = true
    var placeholder: String = ""

    func makeNSView(context: Context) -> NSScrollView {
        let scrollView = NSScrollView()
        scrollView.hasVerticalScroller = true
        scrollView.autohidesScrollers = true
        scrollView.borderType = .noBorder

        let textView = NSTextView()
        textView.delegate = context.coordinator
        textView.isEditable = isEditable
        textView.isSelectable = true
        textView.font = font
        textView.textColor = .textColor
        textView.backgroundColor = .clear
        textView.drawsBackground = false
        textView.isRichText = false
        textView.allowsUndo = true
        textView.usesFontPanel = false
        textView.textContainerInset = NSSize(width: 8, height: 8)

        // Enable text wrapping
        textView.isHorizontallyResizable = false
        textView.isVerticallyResizable = true
        textView.textContainer?.widthTracksTextView = true
        textView.textContainer?.containerSize = NSSize(width: scrollView.contentSize.width, height: .greatestFiniteMagnitude)

        scrollView.documentView = textView

        return scrollView
    }

    func updateNSView(_ scrollView: NSScrollView, context: Context) {
        guard let textView = scrollView.documentView as? NSTextView else { return }

        if textView.string != text {
            textView.string = text
        }
    }

    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }

    class Coordinator: NSObject, NSTextViewDelegate {
        var parent: MultilineTextField

        init(_ parent: MultilineTextField) {
            self.parent = parent
        }

        func textDidChange(_ notification: Notification) {
            guard let textView = notification.object as? NSTextView else { return }
            parent.text = textView.string
        }
    }
}

// MARK: - Preview

struct EditableTextSection_Previews: PreviewProvider {
    static var previews: some View {
        VStack(spacing: 20) {
            EditableTextSection(text: .constant("Sample text to edit"))
                .frame(width: 400)

            CompactEditableTextSection(text: .constant("This is a sample text that can be edited"))
                .frame(width: 400)
        }
        .padding()
    }
}
