import SwiftUI

struct CanvasExamples: View {
    @State private var count = 0

    var body: some View {
        VStack(spacing: 12) {
            Text("Canvas baseline").font(.title)
            Text("Count: \(count)").monospacedDigit()
            Button("Increment") { count += 1 }
        }
        .padding(24)
        .frame(width: 320, height: 180)
        .background(Color.white)
        .foregroundStyle(Color.black)
    }
}

@main
struct PreviewLabApp: App {
    var body: some Scene {
        WindowGroup { CanvasExamples() }
    }
}

// This expression is also supported by our portable source-to-frame renderer.
#Preview("Primary layers", traits: .fixedLayout(width: 64, height: 48)) {
    ZStack {
        Color(.sRGB, red: 0, green: 0, blue: 1, opacity: 1.0)
        Color(.sRGB, red: 1, green: 0, blue: 0, opacity: 0.5)
        Color(.sRGB, red: 0, green: 1, blue: 0, opacity: 0.25)
    }.frame(width: 64, height: 48)
}

// Text, layout and persistent interactive state exceed the portable subset.
#Preview("Text and interaction", traits: .fixedLayout(width: 320, height: 180)) {
    CanvasExamples()
}

#Preview("Layout edit", traits: .fixedLayout(width: 320, height: 180)) {
    HStack(spacing: 16) {
        Rectangle().fill(.red).frame(width: 60, height: 60)
        Text("Layout baseline").foregroundStyle(Color.black)
    }.frame(width: 320, height: 180).background(Color.white)
}
