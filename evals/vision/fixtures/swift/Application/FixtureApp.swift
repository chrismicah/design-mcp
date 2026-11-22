import SwiftUI

@main
struct FixtureApp: App {
    var body: some Scene {
        WindowGroup("Desk review fixture") {
            FixtureControls()
        }
    }
}

private struct FixtureControls: View {
    @State private var revealed = false

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Desk review fixture").font(.title)
            Button("Reveal control") { revealed = true }
                .accessibilityIdentifier("reveal")
            Text(revealed ? "Control revealed" : "Control hidden")
            SecureField("Local note", text: .constant("swift-review-fixture-private-marker"))
            if revealed {
                Button("Revealed control") {}
                    .accessibilityIdentifier("revealed")
            }
        }
        .padding(24)
        .frame(width: 460, height: 250)
    }
}
