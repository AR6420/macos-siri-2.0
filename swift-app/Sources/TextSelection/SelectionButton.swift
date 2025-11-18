//
//  SelectionButton.swift
//  VoiceAssistant
//
//  Orange selection button that appears at the end of text selection
//

import Cocoa
import SwiftUI

// MARK: - Selection Button Delegate

protocol SelectionButtonDelegate: AnyObject {
    func selectionButtonDidClick(at position: CGPoint)
}

// MARK: - Selection Button Window

class SelectionButtonWindow: NSPanel {

    // MARK: - Properties

    weak var buttonDelegate: SelectionButtonDelegate?

    private let buttonSize: CGFloat = 36
    private var contentViewController: SelectionButtonViewController?

    // MARK: - Initialization

    init(at position: CGPoint) {
        // Calculate position (appear at end of selection with slight offset)
        let buttonOrigin = CGPoint(
            x: position.x + 5,
            y: position.y - buttonSize - 5
        )

        let rect = CGRect(
            origin: buttonOrigin,
            size: CGSize(width: buttonSize, height: buttonSize)
        )

        super.init(
            contentRect: rect,
            styleMask: [.nonactivatingPanel, .borderless],
            backing: .buffered,
            defer: false
        )

        setupWindow()
        setupContent()
        animateIn()
    }

    // MARK: - Setup

    private func setupWindow() {
        self.level = .floating
        self.isFloatingPanel = true
        self.isOpaque = false
        self.backgroundColor = .clear
        self.hasShadow = true
        self.isMovableByWindowBackground = false
        self.hidesOnDeactivate = false
        self.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
    }

    private func setupContent() {
        let contentView = SelectionButtonView { [weak self] in
            self?.handleButtonClick()
        }

        contentViewController = SelectionButtonViewController(rootView: contentView)
        self.contentViewController = contentViewController
    }

    // MARK: - Actions

    private func handleButtonClick() {
        guard let frame = self.contentView?.window?.frame else { return }

        // Calculate position for menu (below button)
        let menuPosition = CGPoint(
            x: frame.origin.x,
            y: frame.origin.y - 10
        )

        buttonDelegate?.selectionButtonDidClick(at: menuPosition)

        // Animate out and dismiss
        animateOut {
            self.dismiss()
        }
    }

    // MARK: - Animation

    private func animateIn() {
        self.alphaValue = 0.0
        self.orderFront(nil)

        NSAnimationContext.runAnimationGroup({ context in
            context.duration = 0.2
            context.timingFunction = CAMediaTimingFunction(name: .easeOut)
            self.animator().alphaValue = 1.0
        })
    }

    private func animateOut(completion: @escaping () -> Void) {
        NSAnimationContext.runAnimationGroup({ context in
            context.duration = 0.15
            context.timingFunction = CAMediaTimingFunction(name: .easeIn)
            self.animator().alphaValue = 0.0
        }, completionHandler: completion)
    }

    // MARK: - Dismiss

    func dismiss() {
        self.orderOut(nil)
        self.contentViewController = nil
    }

    // MARK: - Position Update

    func updatePosition(_ position: CGPoint) {
        let newOrigin = CGPoint(
            x: position.x + 5,
            y: position.y - buttonSize - 5
        )

        NSAnimationContext.runAnimationGroup({ context in
            context.duration = 0.1
            context.timingFunction = CAMediaTimingFunction(name: .easeOut)
            self.animator().setFrame(
                CGRect(origin: newOrigin, size: self.frame.size),
                display: true
            )
        })
    }
}

// MARK: - Selection Button View Controller

class SelectionButtonViewController: NSHostingController<SelectionButtonView> {
    override func viewDidLoad() {
        super.viewDidLoad()
        view.wantsLayer = true
        view.layer?.backgroundColor = .clear
    }
}

// MARK: - Selection Button SwiftUI View

struct SelectionButtonView: View {

    let onTap: () -> Void

    @State private var isHovered = false

    var body: some View {
        Button(action: onTap) {
            ZStack {
                // Background circle
                Circle()
                    .fill(
                        LinearGradient(
                            gradient: Gradient(colors: [
                                Color(hex: "#FF8C5A"),
                                Color(hex: "#FF6B35")
                            ]),
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .shadow(
                        color: Color(hex: "#FF6B35").opacity(0.4),
                        radius: isHovered ? 8 : 4,
                        x: 0,
                        y: 2
                    )

                // Sparkle icon
                Image(systemName: "sparkles")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(.white)
                    .scaleEffect(isHovered ? 1.1 : 1.0)
            }
            .frame(width: 36, height: 36)
        }
        .buttonStyle(PlainButtonStyle())
        .onHover { hovering in
            withAnimation(.easeInOut(duration: 0.15)) {
                isHovered = hovering
            }
        }
        .help("AI Assistant")
    }
}

// MARK: - Color Extension

extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 3: // RGB (12-bit)
            (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6: // RGB (24-bit)
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8: // ARGB (32-bit)
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (255, 0, 0, 0)
        }

        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue:  Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}

// MARK: - Preview

struct SelectionButtonView_Previews: PreviewProvider {
    static var previews: some View {
        SelectionButtonView {
            print("Button tapped")
        }
        .frame(width: 50, height: 50)
        .background(Color.gray.opacity(0.2))
    }
}
