//
//  EnhancedFloatingPanel.swift
//  VoiceAssistant
//
//  Enhanced floating panel with comprehensive AI text operations
//  Design: Claude-inspired orange theme with sectioned layout
//

import SwiftUI
import Cocoa

// MARK: - Enhanced Floating Panel Delegate

protocol EnhancedFloatingPanelDelegate: AnyObject {
    func didSelectOption(_ option: MenuOption, customInput: String?)
    func didDismissPanel()
}

// MARK: - Enhanced Floating Panel Window

class EnhancedFloatingPanelWindow: NSPanel {

    // MARK: - Properties

    weak var panelDelegate: EnhancedFloatingPanelDelegate?
    private var autoDismissTimer: Timer?

    private let panelWidth: CGFloat = 320
    private let panelMaxHeight: CGFloat = 500

    // MARK: - Initialization

    init(at position: CGPoint, selectedText: String) {
        // Calculate initial size (will adjust based on content)
        let initialSize = CGSize(width: panelWidth, height: 400)

        // Position panel below the selection button
        let adjustedOrigin = CGPoint(
            x: position.x - 10,
            y: position.y - initialSize.height - 5
        )

        let rect = CGRect(origin: adjustedOrigin, size: initialSize)

        super.init(
            contentRect: rect,
            styleMask: [.nonactivatingPanel, .borderless],
            backing: .buffered,
            defer: false
        )

        setupWindow()
        setupContent(selectedText: selectedText)
        setupAutoDismiss()
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

    private func setupContent(selectedText: String) {
        let contentView = EnhancedFloatingPanelView(
            selectedText: selectedText,
            onOptionSelected: { [weak self] option, customInput in
                self?.handleOptionSelected(option, customInput: customInput)
            },
            onDismiss: { [weak self] in
                self?.dismiss()
            }
        )

        let hostingController = EnhancedFloatingPanelViewController(rootView: contentView)
        self.contentViewController = hostingController

        // Animate in
        animateIn()
    }

    private func setupAutoDismiss() {
        autoDismissTimer = Timer.scheduledTimer(
            withTimeInterval: 15.0,
            repeats: false
        ) { [weak self] _ in
            self?.dismiss()
        }
    }

    // MARK: - Actions

    private func handleOptionSelected(_ option: MenuOption, customInput: String?) {
        cancelAutoDismiss()
        panelDelegate?.didSelectOption(option, customInput: customInput)
        dismiss()
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
        cancelAutoDismiss()

        animateOut { [weak self] in
            self?.panelDelegate?.didDismissPanel()
            self?.orderOut(nil)
            self?.contentViewController = nil
        }
    }

    private func cancelAutoDismiss() {
        autoDismissTimer?.invalidate()
        autoDismissTimer = nil
    }

    // MARK: - Cleanup

    deinit {
        cancelAutoDismiss()
    }
}

// MARK: - Enhanced Floating Panel View Controller

class EnhancedFloatingPanelViewController: NSHostingController<EnhancedFloatingPanelView> {
    override func viewDidLoad() {
        super.viewDidLoad()
        view.wantsLayer = true
        view.layer?.backgroundColor = .clear
    }
}

// MARK: - Enhanced Floating Panel SwiftUI View

struct EnhancedFloatingPanelView: View {

    // MARK: - Properties

    let selectedText: String
    let onOptionSelected: (MenuOption, String?) -> Void
    let onDismiss: () -> Void

    @State private var customInput: String = ""
    @State private var hoveredOption: MenuOption? = nil
    @FocusState private var isInputFocused: Bool

    // MARK: - Theme Colors

    private let primaryOrange = Color(hex: "#FF6B35")
    private let secondaryPurple = Color(hex: "#8B5CF6")
    private let backgroundColor = Color.white
    private let textColor = Color(hex: "#1F2937")
    private let dividerColor = Color(hex: "#E5E7EB")
    private let hoverBackground = Color(hex: "#F9FAFB")

    // MARK: - Body

    var body: some View {
        VStack(spacing: 0) {
            // Input Section
            inputSection
                .padding(.horizontal, 16)
                .padding(.top, 16)
                .padding(.bottom, 12)

            Divider()
                .background(dividerColor)

            // Primary Actions Section
            primaryActionsSection
                .padding(.horizontal, 16)
                .padding(.vertical, 12)

            Divider()
                .background(dividerColor)

            // Style Options Section
            styleOptionsSection
                .padding(.horizontal, 16)
                .padding(.vertical, 12)

            Divider()
                .background(dividerColor)

            // Formatting Section
            formattingSection
                .padding(.horizontal, 16)
                .padding(.vertical, 12)

            Divider()
                .background(dividerColor)

            // Compose Action
            composeSection
                .padding(.horizontal, 16)
                .padding(.top, 12)
                .padding(.bottom, 16)
        }
        .frame(width: 320)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(backgroundColor)
                .shadow(color: Color.black.opacity(0.1), radius: 8, x: 0, y: 2)
        )
    }

    // MARK: - Input Section

    private var inputSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Selected Text")
                .font(.system(size: 11, weight: .medium))
                .foregroundColor(textColor.opacity(0.6))

            TextField("Edit or add instructions...", text: $customInput)
                .textFieldStyle(CustomTextFieldStyle())
                .focused($isInputFocused)
                .frame(height: 36)
        }
    }

    // MARK: - Primary Actions Section

    private var primaryActionsSection: some View {
        HStack(spacing: 8) {
            ForEach(MenuOption.primaryOptions, id: \.self) { option in
                primaryActionButton(for: option)
            }
        }
    }

    private func primaryActionButton(for option: MenuOption) -> some View {
        Button(action: {
            handleOptionTap(option)
        }) {
            HStack(spacing: 6) {
                Image(systemName: option.icon)
                    .font(.system(size: 14, weight: .medium))
                Text(option.displayName)
                    .font(.system(size: 13, weight: .medium))
            }
            .foregroundColor(.white)
            .frame(maxWidth: .infinity)
            .frame(height: 36)
            .background(
                RoundedRectangle(cornerRadius: 8)
                    .fill(primaryOrange)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(
                        hoveredOption == option ? Color.white.opacity(0.3) : Color.clear,
                        lineWidth: 2
                    )
            )
        }
        .buttonStyle(PlainButtonStyle())
        .onHover { hovering in
            hoveredOption = hovering ? option : nil
        }
    }

    // MARK: - Style Options Section

    private var styleOptionsSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Style")
                .font(.system(size: 11, weight: .medium))
                .foregroundColor(textColor.opacity(0.6))

            HStack(spacing: 8) {
                ForEach(MenuOption.styleOptions, id: \.self) { option in
                    styleOptionButton(for: option)
                }
            }
        }
    }

    private func styleOptionButton(for option: MenuOption) -> some View {
        Button(action: {
            handleOptionTap(option)
        }) {
            VStack(spacing: 4) {
                Image(systemName: option.icon)
                    .font(.system(size: 18, weight: .regular))
                Text(option.displayName)
                    .font(.system(size: 11, weight: .medium))
            }
            .foregroundColor(hoveredOption == option ? primaryOrange : textColor)
            .frame(maxWidth: .infinity)
            .frame(height: 60)
            .background(
                RoundedRectangle(cornerRadius: 8)
                    .fill(hoveredOption == option ? hoverBackground : Color.clear)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(dividerColor, lineWidth: 1)
            )
        }
        .buttonStyle(PlainButtonStyle())
        .onHover { hovering in
            hoveredOption = hovering ? option : nil
        }
    }

    // MARK: - Formatting Section

    private var formattingSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Format")
                .font(.system(size: 11, weight: .medium))
                .foregroundColor(textColor.opacity(0.6))

            LazyVGrid(
                columns: [
                    GridItem(.flexible(), spacing: 8),
                    GridItem(.flexible(), spacing: 8)
                ],
                spacing: 8
            ) {
                ForEach(MenuOption.formattingOptions, id: \.self) { option in
                    formattingOptionButton(for: option)
                }
            }
        }
    }

    private func formattingOptionButton(for option: MenuOption) -> some View {
        Button(action: {
            handleOptionTap(option)
        }) {
            HStack(spacing: 6) {
                Image(systemName: option.icon)
                    .font(.system(size: 14, weight: .medium))
                Text(option.displayName)
                    .font(.system(size: 12, weight: .medium))
                Spacer()
            }
            .foregroundColor(hoveredOption == option ? primaryOrange : textColor)
            .padding(.horizontal, 10)
            .frame(height: 36)
            .background(
                RoundedRectangle(cornerRadius: 8)
                    .fill(hoveredOption == option ? hoverBackground : Color.clear)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(dividerColor, lineWidth: 1)
            )
        }
        .buttonStyle(PlainButtonStyle())
        .onHover { hovering in
            hoveredOption = hovering ? option : nil
        }
    }

    // MARK: - Compose Section

    private var composeSection: some View {
        Button(action: {
            handleOptionTap(.compose)
        }) {
            HStack(spacing: 8) {
                Image(systemName: MenuOption.compose.icon)
                    .font(.system(size: 14, weight: .medium))
                Text(MenuOption.compose.displayName)
                    .font(.system(size: 13, weight: .medium))
                Spacer()
                Image(systemName: "chevron.right")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(textColor.opacity(0.4))
            }
            .foregroundColor(secondaryPurple)
            .padding(.horizontal, 12)
            .frame(height: 40)
            .background(
                RoundedRectangle(cornerRadius: 8)
                    .fill(hoveredOption == .compose ? hoverBackground : Color.clear)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(secondaryPurple.opacity(0.3), lineWidth: 1)
            )
        }
        .buttonStyle(PlainButtonStyle())
        .onHover { hovering in
            hoveredOption = hovering ? .compose : nil
        }
    }

    // MARK: - Actions

    private func handleOptionTap(_ option: MenuOption) {
        let input = customInput.isEmpty ? nil : customInput
        onOptionSelected(option, input)
    }
}

// MARK: - Custom Text Field Style

struct CustomTextFieldStyle: TextFieldStyle {
    func _body(configuration: TextField<Self._Label>) -> some View {
        configuration
            .font(.system(size: 14))
            .padding(.horizontal, 10)
            .padding(.vertical, 8)
            .background(
                RoundedRectangle(cornerRadius: 6)
                    .fill(Color(hex: "#F9FAFB"))
            )
            .overlay(
                RoundedRectangle(cornerRadius: 6)
                    .stroke(Color(hex: "#E5E7EB"), lineWidth: 1)
            )
    }
}

// MARK: - Preview

struct EnhancedFloatingPanelView_Previews: PreviewProvider {
    static var previews: some View {
        EnhancedFloatingPanelView(
            selectedText: "Sample selected text",
            onOptionSelected: { option, input in
                print("Selected: \(option.displayName), Input: \(input ?? "none")")
            },
            onDismiss: {
                print("Dismissed")
            }
        )
        .frame(width: 320)
        .background(Color.gray.opacity(0.2))
    }
}
