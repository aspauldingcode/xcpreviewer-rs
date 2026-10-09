import SwiftUI

struct ProbeView: View {
    let label: String
    var body: some View {
        VStack(spacing: 12) {
            Text(label).font(.title)
            Text("Owned canvas fixture").foregroundStyle(.secondary)
        }
        .frame(width: 320, height: 160)
        .background(Color.white)
    }
}

@main
struct PreviewLabApp: App {
    var body: some Scene {
        WindowGroup { ProbeView(label: "Preview baseline") }
    }
}

#Preview("Baseline") { ProbeView(label: "Preview baseline") }
#Preview("Literal change") { ProbeView(label: "Preview changed") }
