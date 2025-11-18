//
//  FloatingPanel.swift
//  VoiceAssistant
//
//  Floating UI panel for inline AI text operations
//

import SwiftUI
import Cocoa

// MARK: - Tone Type

enum ToneType: String, CaseIterable {
    case professional = "professional"
    case friendly = "friendly"
    case concise = "concise"

    var displayName: String {
        switch self {
        case .professional:
            return "Professional"
        case .friendly:
            return "Friendly"
        case .concise:
            return "Concise"
        }
    }

    var icon: String {
        switch self {
        case .professional:
            return "briefcase.fill"
        case .friendly:
            return "heart.fill"
        case .concise:
            return "text.alignleft"
        }
    }
}

// MARK: - Floating Panel Delegate

protocol FloatingPanelDelegate: AnyObject {
    func didSelectRewrite(tone: ToneType)
    func didSelectSummarize()
    func didDismissPanel()
}

// MARK: - Floating Panel Window

class FloatingPanelWindow: NSPanel {

    weak var panelDelegate: FloatingPanelDelegate?
    private var contentViewController: FloatingPanelViewController?

    init(at position: CGPoint, selectedText: String) {
        // Calculate window size
        let windowSize = CGSize(width: 280, height: 80)

        // Adjust position to be below selection
        let adjustedOrigin = CGPoint(
            x: position.x - windowSize.width / 2,
            y: position.y - windowSize.height - 5
        )

        let rect = CGRect(origin: adjustedOrigin, size: windowSize)

        super.init(
            contentRect: rect,
            styleMask: [.nonactivatingPanel, .borderless],
            backing: .buffered,
            defer: false
        )

        // Configure panel
        self.level = .floating
        self.isFloatingPanel = true
        self.isOpaque = false
        self.backgroundColor = .clear
        self.hasShadow = true
        self.isMovableByWindowBackground = false
        self.hidesOnDeactivate = false
        self.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]

        // Create SwiftUI view
        let contentView = FloatingPanelView(selectedText: selectedText) { [weak self] action in
            self?.handleAction(action)
        }

        // Create hosting controller
        contentViewController = FloatingPanelViewController(rootView: contentView)
        self.contentViewController = contentViewController

        // Auto-dismiss after delay
        DispatchQueue.main.asyncAfter(deadline: .now() + 10) { [weak self] in
            self?.dismiss()
        }
    }

    private func handleAction(_ action: FloatingPanelAction) {
        switch action {
        case .rewrite(let tone):
            panelDelegate?.didSelectRewrite(tone: tone)
            dismiss()

        case .summarize:
            panelDelegate?.didSelectSummarize()
            dismiss()

        case .dismiss:
            dismiss()
        }
    }

    func dismiss() {
        panelDelegate?.didDismissPanel()
        self.orderOut(nil)
        self.contentViewController = nil
    }

    override func resignKey() {
        super.resignKey()
        // Don't auto-dismiss on resign - user might be clicking menus
    }
}

// MARK: - Floating Panel View Controller

class FloatingPanelViewController: NSHostingController<FloatingPanelView> {
    override func viewDidLoad() {
        super.viewDidLoad()
        view.wantsLayer = true
        view.layer?.backgroundColor = .clear
    }
}

// MARK: - Panel Action

enum FloatingPanelAction {
    case rewrite(ToneType)
    case summarize
    case dismiss
}

// MARK: - SwiftUI View

struct FloatingPanelView: View {

    let selectedText: String
    let onAction: (FloatingPanelAction) -> Void

    @State private var showToneMenu = false
    @State private var isProcessing = false

    var body: some View {
        HStack(spacing: 12) {
            // Rewrite button with dropdown
            Menu {
                ForEach(ToneType.allCases, id: \.self) { tone in
                    Button(action: {
                        onAction(.rewrite(tone))
                    }) {
                        Label(tone.displayName, systemImage: tone.icon)
                    }
                }
            } label: {
                HStack(spacing: 6) {
                    Image(systemName: "pencil.and.outline")
                        .font(.system(size: 14))
                    Text("Tone")
                        .font(.system(size: 13, weight: .medium))
                    Image(systemName: "chevron.down")
                        .font(.system(size: 10))
                }
                .foregroundColor(.white)
                .padding(.horizontal, 14)
                .padding(.vertical, 10)
                .background(
                    RoundedRectangle(cornerRadius: 8)
                        .fill(Color.blue)
                )
            }
            .menuStyle(.borderlessButton)
            .frame(height: 36)

            // Summarize button
            Button(action: {
                onAction(.summarize)
            }) {
                HStack(spacing: 6) {
                    Image(systemName: "doc.text.magnifyingglass")
                        .font(.system(size: 14))
                    Text("Summarize")
                        .font(.system(size: 13, weight: .medium))
                }
                .foregroundColor(.white)
                .padding(.horizontal, 14)
                .padding(.vertical, 10)
                .background(
                    RoundedRectangle(cornerRadius: 8)
                        .fill(Color.blue)
                )
            }
            .buttonStyle(.plain)
            .frame(height: 36)
        }
        .padding(12)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(nsColor: .windowBackgroundColor))
                .shadow(color: Color.black.opacity(0.2), radius: 10, x: 0, y: 5)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color.gray.opacity(0.2), lineWidth: 0.5)
        )
    }
}

// MARK: - Loading Overlay

struct LoadingOverlayView: View {
    var body: some View {
        ZStack {
            Color.black.opacity(0.3)
                .cornerRadius(12)

            VStack(spacing: 8) {
                ProgressView()
                    .scaleEffect(0.8)
                Text("Processing...")
                    .font(.system(size: 11, weight: .medium))
                    .foregroundColor(.white)
            }
            .padding(16)
            .background(
                RoundedRectangle(cornerRadius: 8)
                    .fill(Color(nsColor: .windowBackgroundColor).opacity(0.95))
            )
        }
    }
}

// MARK: - Preview

struct FloatingPanelView_Previews: PreviewProvider {
    static var previews: some View {
        FloatingPanelView(selectedText: "Sample text") { action in
            print("Action: \(action)")
        }
        .frame(width: 280, height: 80)
    }
}
