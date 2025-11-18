//
//  LoadingOverlay.swift
//  VoiceAssistant
//
//  Loading states and progress indicators for text operations
//

import SwiftUI
import Cocoa

// MARK: - Loading State

enum LoadingState {
    case idle
    case loading(String)
    case progress(Double, String)
    case success(String)
    case error(String)
}

// MARK: - Loading Overlay

struct LoadingOverlay: View {

    let state: LoadingState
    let onCancel: (() -> Void)?

    @State private var animationRotation: Double = 0
    @State private var pulseScale: CGFloat = 1.0
    @State private var showSuccess = false
    @State private var showError = false

    var body: some View {
        ZStack {
            // Semi-transparent background
            Color.black.opacity(0.4)
                .edgesIgnoringSafeArea(.all)

            // Loading content
            VStack(spacing: 16) {
                switch state {
                case .idle:
                    EmptyView()

                case .loading(let message):
                    LoadingSpinner(message: message)

                case .progress(let progress, let message):
                    ProgressIndicator(progress: progress, message: message)

                case .success(let message):
                    SuccessIndicator(message: message)

                case .error(let message):
                    ErrorIndicator(message: message)
                }

                // Cancel button for loading states
                if case .loading = state, let onCancel = onCancel {
                    Button(action: onCancel) {
                        Text("Cancel")
                            .font(.system(size: 12, weight: .medium))
                            .foregroundColor(.white)
                            .padding(.horizontal, 20)
                            .padding(.vertical, 8)
                            .background(
                                Capsule()
                                    .fill(Color.red.opacity(0.8))
                            )
                    }
                    .buttonStyle(.plain)
                } else if case .progress = state, let onCancel = onCancel {
                    Button(action: onCancel) {
                        Text("Cancel")
                            .font(.system(size: 12, weight: .medium))
                            .foregroundColor(.white)
                            .padding(.horizontal, 20)
                            .padding(.vertical, 8)
                            .background(
                                Capsule()
                                    .fill(Color.red.opacity(0.8))
                            )
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(24)
            .background(
                RoundedRectangle(cornerRadius: 16)
                    .fill(Color(nsColor: .windowBackgroundColor).opacity(0.95))
                    .shadow(color: Color.black.opacity(0.3), radius: 20, x: 0, y: 10)
            )
        }
    }
}

// MARK: - Loading Spinner

struct LoadingSpinner: View {

    let message: String

    @State private var rotation: Double = 0

    var body: some View {
        VStack(spacing: 16) {
            // Animated spinner
            Circle()
                .trim(from: 0, to: 0.7)
                .stroke(
                    AngularGradient(
                        colors: [.accentColor, .accentColor.opacity(0.2)],
                        center: .center
                    ),
                    style: StrokeStyle(lineWidth: 4, lineCap: .round)
                )
                .frame(width: 50, height: 50)
                .rotationEffect(.degrees(rotation))
                .onAppear {
                    withAnimation(.linear(duration: 1).repeatForever(autoreverses: false)) {
                        rotation = 360
                    }
                }

            // Message
            Text(message)
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(.primary)
                .multilineTextAlignment(.center)
        }
        .frame(minWidth: 200)
    }
}

// MARK: - Progress Indicator

struct ProgressIndicator: View {

    let progress: Double
    let message: String

    @State private var animatedProgress: Double = 0

    var body: some View {
        VStack(spacing: 16) {
            // Circular progress
            ZStack {
                // Background circle
                Circle()
                    .stroke(Color.gray.opacity(0.2), lineWidth: 4)
                    .frame(width: 60, height: 60)

                // Progress circle
                Circle()
                    .trim(from: 0, to: CGFloat(min(animatedProgress, 1.0)))
                    .stroke(
                        Color.accentColor,
                        style: StrokeStyle(lineWidth: 4, lineCap: .round)
                    )
                    .frame(width: 60, height: 60)
                    .rotationEffect(.degrees(-90))

                // Percentage text
                Text("\(Int(animatedProgress * 100))%")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(.primary)
            }

            // Progress bar
            VStack(spacing: 8) {
                ProgressView(value: animatedProgress, total: 1.0)
                    .progressViewStyle(.linear)
                    .frame(width: 200)

                // Message
                Text(message)
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)

                // Time estimate (if progress > 0)
                if animatedProgress > 0.1 {
                    Text(estimatedTimeRemaining)
                        .font(.system(size: 10))
                        .foregroundColor(.secondary)
                }
            }
        }
        .frame(minWidth: 250)
        .onAppear {
            withAnimation(.easeInOut(duration: 0.5)) {
                animatedProgress = progress
            }
        }
        .onChange(of: progress) { _, newValue in
            withAnimation(.easeInOut(duration: 0.3)) {
                animatedProgress = newValue
            }
        }
    }

    private var estimatedTimeRemaining: String {
        if animatedProgress >= 1.0 {
            return "Completing..."
        } else if animatedProgress > 0 {
            let estimate = Int((1.0 - animatedProgress) / animatedProgress * 10)
            return "~\(estimate)s remaining"
        } else {
            return "Calculating..."
        }
    }
}

// MARK: - Success Indicator

struct SuccessIndicator: View {

    let message: String

    @State private var scale: CGFloat = 0.5
    @State private var opacity: Double = 0

    var body: some View {
        VStack(spacing: 16) {
            // Success checkmark
            ZStack {
                Circle()
                    .fill(Color.green.opacity(0.2))
                    .frame(width: 60, height: 60)

                Image(systemName: "checkmark.circle.fill")
                    .font(.system(size: 50))
                    .foregroundColor(.green)
            }
            .scaleEffect(scale)
            .opacity(opacity)

            // Message
            Text(message)
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(.primary)
                .multilineTextAlignment(.center)
                .opacity(opacity)
        }
        .frame(minWidth: 200)
        .onAppear {
            withAnimation(.spring(response: 0.6, dampingFraction: 0.6)) {
                scale = 1.0
                opacity = 1.0
            }
        }
    }
}

// MARK: - Error Indicator

struct ErrorIndicator: View {

    let message: String

    @State private var shake: Bool = false

    var body: some View {
        VStack(spacing: 16) {
            // Error icon
            ZStack {
                Circle()
                    .fill(Color.red.opacity(0.2))
                    .frame(width: 60, height: 60)

                Image(systemName: "xmark.circle.fill")
                    .font(.system(size: 50))
                    .foregroundColor(.red)
            }
            .offset(x: shake ? -10 : 0)

            // Message
            Text(message)
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(.red)
                .multilineTextAlignment(.center)
                .fixedSize(horizontal: false, vertical: true)
        }
        .frame(minWidth: 200)
        .onAppear {
            // Shake animation
            withAnimation(.easeInOut(duration: 0.1).repeatCount(3, autoreverses: true)) {
                shake.toggle()
            }
        }
    }
}

// MARK: - Operation-Specific Loading Views

struct RewriteLoadingView: View {

    let tone: String

    @State private var dotsCount = 1

    var body: some View {
        VStack(spacing: 12) {
            HStack(spacing: 8) {
                Image(systemName: "pencil.and.outline")
                    .font(.system(size: 24))
                    .foregroundColor(.accentColor)

                Text("Rewriting")
                    .font(.system(size: 16, weight: .semibold))
            }

            Text("Applying \(tone) tone\(String(repeating: ".", count: dotsCount))")
                .font(.system(size: 12))
                .foregroundColor(.secondary)
                .onAppear {
                    Timer.scheduledTimer(withTimeInterval: 0.5, repeats: true) { _ in
                        dotsCount = (dotsCount % 3) + 1
                    }
                }
        }
        .padding(24)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(nsColor: .windowBackgroundColor).opacity(0.95))
                .shadow(radius: 10)
        )
    }
}

struct SummarizeLoadingView: View {

    @State private var progress: Double = 0

    var body: some View {
        VStack(spacing: 12) {
            HStack(spacing: 8) {
                Image(systemName: "doc.text.magnifyingglass")
                    .font(.system(size: 24))
                    .foregroundColor(.accentColor)

                Text("Summarizing")
                    .font(.system(size: 16, weight: .semibold))
            }

            ProgressView(value: progress, total: 1.0)
                .progressViewStyle(.linear)
                .frame(width: 200)

            Text("Analyzing content...")
                .font(.system(size: 12))
                .foregroundColor(.secondary)
        }
        .padding(24)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(nsColor: .windowBackgroundColor).opacity(0.95))
                .shadow(radius: 10)
        )
        .onAppear {
            // Fake progress animation
            withAnimation(.linear(duration: 3)) {
                progress = 0.8
            }
        }
    }
}

struct ProofreadLoadingView: View {

    @State private var currentStep = 0
    let steps = ["Checking grammar", "Verifying spelling", "Analyzing style", "Finalizing"]

    var body: some View {
        VStack(spacing: 12) {
            HStack(spacing: 8) {
                Image(systemName: "checkmark.seal.fill")
                    .font(.system(size: 24))
                    .foregroundColor(.accentColor)

                Text("Proofreading")
                    .font(.system(size: 16, weight: .semibold))
            }

            VStack(alignment: .leading, spacing: 6) {
                ForEach(Array(steps.enumerated()), id: \.offset) { index, step in
                    HStack(spacing: 8) {
                        if index < currentStep {
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundColor(.green)
                        } else if index == currentStep {
                            ProgressView()
                                .scaleEffect(0.7)
                        } else {
                            Image(systemName: "circle")
                                .foregroundColor(.secondary)
                        }

                        Text(step)
                            .font(.system(size: 11))
                            .foregroundColor(index <= currentStep ? .primary : .secondary)
                    }
                }
            }
            .padding(.top, 8)
        }
        .padding(24)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(nsColor: .windowBackgroundColor).opacity(0.95))
                .shadow(radius: 10)
        )
        .onAppear {
            Timer.scheduledTimer(withTimeInterval: 0.8, repeats: true) { timer in
                if currentStep < steps.count - 1 {
                    currentStep += 1
                } else {
                    timer.invalidate()
                }
            }
        }
    }
}

// MARK: - Mini Loading Indicator

struct MiniLoadingIndicator: View {

    @State private var rotation: Double = 0

    var body: some View {
        Circle()
            .trim(from: 0, to: 0.7)
            .stroke(Color.accentColor, style: StrokeStyle(lineWidth: 2, lineCap: .round))
            .frame(width: 16, height: 16)
            .rotationEffect(.degrees(rotation))
            .onAppear {
                withAnimation(.linear(duration: 1).repeatForever(autoreverses: false)) {
                    rotation = 360
                }
            }
    }
}

// MARK: - Preview

struct LoadingOverlay_Previews: PreviewProvider {
    static var previews: some View {
        Group {
            LoadingOverlay(state: .loading("Processing your text..."), onCancel: {})
                .previewDisplayName("Loading")

            LoadingOverlay(state: .progress(0.65, "Analyzing content..."), onCancel: {})
                .previewDisplayName("Progress")

            LoadingOverlay(state: .success("Text updated successfully!"), onCancel: nil)
                .previewDisplayName("Success")

            LoadingOverlay(state: .error("Failed to process text. Please try again."), onCancel: nil)
                .previewDisplayName("Error")

            RewriteLoadingView(tone: "professional")
                .previewDisplayName("Rewrite")

            ProofreadLoadingView()
                .previewDisplayName("Proofread")
        }
        .frame(width: 400, height: 300)
    }
}
