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

// Independent whole-view controls: no text, font, stack or app-state dependency.
#Preview("Solid red") {
    Color(.sRGB, red: 1, green: 0, blue: 0, opacity: 1)
        .frame(width: 320, height: 160)
}
#Preview("Solid blue") {
    Color(.sRGB, red: 0, green: 0, blue: 1, opacity: 1)
        .frame(width: 320, height: 160)
}
