//
//  EnhancedUIPreviews.swift
//  VoiceAssistant
//
//  SwiftUI previews for testing and developing the enhanced UI components
//  Open this file in Xcode and use the preview canvas to see all UI states
//

import SwiftUI

// MARK: - Selection Button Preview

struct SelectionButtonPreview: View {

    @State private var isHovered = false

    var body: some View {
        VStack(spacing: 40) {
            Text("Selection Button States")
                .font(.title2)
                .fontWeight(.bold)

            // Normal state
            VStack(spacing: 8) {
                Text("Normal")
                    .font(.caption)
                    .foregroundColor(.secondary)

                SelectionButtonView {
                    print("Button tapped")
                }
            }

            // Hovered state (simulated)
            VStack(spacing: 8) {
                Text("Hovered")
                    .font(.caption)
                    .foregroundColor(.secondary)

                Button(action: {}) {
                    ZStack {
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
                                radius: 8,
                                x: 0,
                                y: 2
                            )

                        Image(systemName: "sparkles")
                            .font(.system(size: 16, weight: .semibold))
                            .foregroundColor(.white)
                            .scaleEffect(1.1)
                    }
                    .frame(width: 36, height: 36)
                }
                .buttonStyle(PlainButtonStyle())
            }

            // Different positions
            VStack(spacing: 8) {
                Text("In Context")
                    .font(.caption)
                    .foregroundColor(.secondary)

                HStack {
                    Text("Some selected text")
                        .padding(8)
                        .background(Color.blue.opacity(0.2))
                        .cornerRadius(4)

                    SelectionButtonView {
                        print("Button tapped")
                    }

                    Spacer()
                }
            }
        }
        .padding(40)
        .frame(width: 400, height: 600)
    }
}

// MARK: - Enhanced Floating Panel Preview

struct EnhancedFloatingPanelPreview: View {

    @State private var selectedOption: MenuOption? = nil
    @State private var customInput: String = ""

    var body: some View {
        ScrollView {
            VStack(spacing: 40) {
                Text("Enhanced Floating Panel")
                    .font(.title2)
                    .fontWeight(.bold)

                // Full panel
                VStack(alignment: .leading, spacing: 8) {
                    Text("Full Panel")
                        .font(.caption)
                        .foregroundColor(.secondary)

                    EnhancedFloatingPanelView(
                        selectedText: "This is some sample text that was selected by the user",
                        onOptionSelected: { option, input in
                            selectedOption = option
                            customInput = input ?? ""
                            print("Selected: \(option.displayName)")
                            if let input = input {
                                print("Input: \(input)")
                            }
                        },
                        onDismiss: {
                            print("Panel dismissed")
                        }
                    )
                }

                // Status display
                if let option = selectedOption {
                    VStack(spacing: 4) {
                        Text("Last Selected Option")
                            .font(.caption)
                            .foregroundColor(.secondary)

                        Text(option.displayName)
                            .font(.headline)

                        if !customInput.isEmpty {
                            Text("Custom Input: \(customInput)")
                                .font(.caption)
                                .foregroundColor(.blue)
                        }
                    }
                    .padding()
                    .background(Color.gray.opacity(0.1))
                    .cornerRadius(8)
                }
            }
            .padding(40)
        }
        .frame(width: 450, height: 800)
    }
}

// MARK: - Individual Section Previews

struct PrimaryActionsSectionPreview: View {

    @State private var hoveredOption: MenuOption? = nil

    var body: some View {
        VStack(spacing: 20) {
            Text("Primary Actions")
                .font(.title3)
                .fontWeight(.bold)

            HStack(spacing: 8) {
                ForEach(MenuOption.primaryOptions, id: \.self) { option in
                    Button(action: {
                        print("Tapped: \(option.displayName)")
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
                                .fill(Color(hex: "#FF6B35"))
                        )
                    }
                    .buttonStyle(PlainButtonStyle())
                }
            }
            .padding()
        }
        .frame(width: 320)
    }
}

struct StyleOptionsSectionPreview: View {

    @State private var selectedStyle: MenuOption? = nil

    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("Style Options")
                .font(.title3)
                .fontWeight(.bold)

            VStack(alignment: .leading, spacing: 8) {
                Text("Style")
                    .font(.system(size: 11, weight: .medium))
                    .foregroundColor(Color(hex: "#1F2937").opacity(0.6))

                HStack(spacing: 8) {
                    ForEach(MenuOption.styleOptions, id: \.self) { option in
                        Button(action: {
                            selectedStyle = option
                        }) {
                            VStack(spacing: 4) {
                                Image(systemName: option.icon)
                                    .font(.system(size: 18, weight: .regular))
                                Text(option.displayName)
                                    .font(.system(size: 11, weight: .medium))
                            }
                            .foregroundColor(
                                selectedStyle == option ?
                                    Color(hex: "#FF6B35") :
                                    Color(hex: "#1F2937")
                            )
                            .frame(maxWidth: .infinity)
                            .frame(height: 60)
                            .background(
                                RoundedRectangle(cornerRadius: 8)
                                    .fill(
                                        selectedStyle == option ?
                                            Color(hex: "#F9FAFB") :
                                            Color.clear
                                    )
                            )
                            .overlay(
                                RoundedRectangle(cornerRadius: 8)
                                    .stroke(Color(hex: "#E5E7EB"), lineWidth: 1)
                            )
                        }
                        .buttonStyle(PlainButtonStyle())
                    }
                }
            }
            .padding()
        }
        .frame(width: 320)
    }
}

struct FormattingOptionsSectionPreview: View {

    @State private var selectedFormat: MenuOption? = nil

    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("Formatting Options")
                .font(.title3)
                .fontWeight(.bold)

            VStack(alignment: .leading, spacing: 8) {
                Text("Format")
                    .font(.system(size: 11, weight: .medium))
                    .foregroundColor(Color(hex: "#1F2937").opacity(0.6))

                LazyVGrid(
                    columns: [
                        GridItem(.flexible(), spacing: 8),
                        GridItem(.flexible(), spacing: 8)
                    ],
                    spacing: 8
                ) {
                    ForEach(MenuOption.formattingOptions, id: \.self) { option in
                        Button(action: {
                            selectedFormat = option
                        }) {
                            HStack(spacing: 6) {
                                Image(systemName: option.icon)
                                    .font(.system(size: 14, weight: .medium))
                                Text(option.displayName)
                                    .font(.system(size: 12, weight: .medium))
                                Spacer()
                            }
                            .foregroundColor(
                                selectedFormat == option ?
                                    Color(hex: "#FF6B35") :
                                    Color(hex: "#1F2937")
                            )
                            .padding(.horizontal, 10)
                            .frame(height: 36)
                            .background(
                                RoundedRectangle(cornerRadius: 8)
                                    .fill(
                                        selectedFormat == option ?
                                            Color(hex: "#F9FAFB") :
                                            Color.clear
                                    )
                            )
                            .overlay(
                                RoundedRectangle(cornerRadius: 8)
                                    .stroke(Color(hex: "#E5E7EB"), lineWidth: 1)
                            )
                        }
                        .buttonStyle(PlainButtonStyle())
                    }
                }
            }
            .padding()
        }
        .frame(width: 320)
    }
}

struct ComposeSectionPreview: View {

    @State private var isHovered = false

    var body: some View {
        VStack(spacing: 20) {
            Text("Compose Action")
                .font(.title3)
                .fontWeight(.bold)

            Button(action: {
                print("Compose tapped")
            }) {
                HStack(spacing: 8) {
                    Image(systemName: "pencil.line")
                        .font(.system(size: 14, weight: .medium))
                    Text("Compose...")
                        .font(.system(size: 13, weight: .medium))
                    Spacer()
                    Image(systemName: "chevron.right")
                        .font(.system(size: 10, weight: .semibold))
                        .foregroundColor(Color(hex: "#1F2937").opacity(0.4))
                }
                .foregroundColor(Color(hex: "#8B5CF6"))
                .padding(.horizontal, 12)
                .frame(height: 40)
                .background(
                    RoundedRectangle(cornerRadius: 8)
                        .fill(isHovered ? Color(hex: "#F9FAFB") : Color.clear)
                )
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(Color(hex: "#8B5CF6").opacity(0.3), lineWidth: 1)
                )
            }
            .buttonStyle(PlainButtonStyle())
            .onHover { hovering in
                isHovered = hovering
            }
            .padding()
        }
        .frame(width: 320)
    }
}

// MARK: - Color Palette Preview

struct ColorPalettePreview: View {

    var body: some View {
        VStack(spacing: 20) {
            Text("Claude Theme Colors")
                .font(.title2)
                .fontWeight(.bold)

            VStack(spacing: 12) {
                colorSwatch("Primary Orange", "#FF6B35")
                colorSwatch("Secondary Purple", "#8B5CF6")
                colorSwatch("Text Dark", "#1F2937")
                colorSwatch("Divider", "#E5E7EB")
                colorSwatch("Hover Background", "#F9FAFB")
            }
        }
        .padding(40)
        .frame(width: 400)
    }

    private func colorSwatch(_ name: String, _ hex: String) -> some View {
        HStack {
            RoundedRectangle(cornerRadius: 8)
                .fill(Color(hex: hex))
                .frame(width: 60, height: 40)
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(Color.gray.opacity(0.3), lineWidth: 1)
                )

            VStack(alignment: .leading, spacing: 2) {
                Text(name)
                    .font(.system(size: 13, weight: .medium))
                Text(hex)
                    .font(.system(size: 11))
                    .foregroundColor(.secondary)
            }

            Spacer()
        }
    }
}

// MARK: - Preview Providers

struct SelectionButtonPreview_Previews: PreviewProvider {
    static var previews: some View {
        SelectionButtonPreview()
    }
}

struct EnhancedFloatingPanelPreview_Previews: PreviewProvider {
    static var previews: some View {
        EnhancedFloatingPanelPreview()
    }
}

struct PrimaryActionsSectionPreview_Previews: PreviewProvider {
    static var previews: some View {
        PrimaryActionsSectionPreview()
    }
}

struct StyleOptionsSectionPreview_Previews: PreviewProvider {
    static var previews: some View {
        StyleOptionsSectionPreview()
    }
}

struct FormattingOptionsSectionPreview_Previews: PreviewProvider {
    static var previews: some View {
        FormattingOptionsSectionPreview()
    }
}

struct ComposeSectionPreview_Previews: PreviewProvider {
    static var previews: some View {
        ComposeSectionPreview()
    }
}

struct ColorPalettePreview_Previews: PreviewProvider {
    static var previews: some View {
        ColorPalettePreview()
    }
}

// MARK: - Combined Preview

struct AllComponentsPreview: View {

    var body: some View {
        ScrollView {
            VStack(spacing: 40) {
                SelectionButtonPreview()
                Divider()
                PrimaryActionsSectionPreview()
                Divider()
                StyleOptionsSectionPreview()
                Divider()
                FormattingOptionsSectionPreview()
                Divider()
                ComposeSectionPreview()
                Divider()
                ColorPalettePreview()
            }
            .padding()
        }
    }
}

struct AllComponentsPreview_Previews: PreviewProvider {
    static var previews: some View {
        AllComponentsPreview()
            .frame(width: 500, height: 1200)
    }
}
