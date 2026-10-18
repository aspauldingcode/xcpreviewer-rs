import SwiftUI

struct AppearanceSentinel: View {
    @Environment(\.colorScheme) private var scheme
    var body: some View {
        ZStack {
            Color(.sRGB, red: scheme == .dark ? 1 : 0,
                  green: scheme == .dark ? 0 : 1,
                  blue: scheme == .dark ? 1 : 0, opacity: 1)
            VStack {
                Text("SENTINEL 20261015")
                Text(scheme == .dark ? "MODE DARK" : "MODE LIGHT")
            }.foregroundStyle(Color.black)
        }.frame(width: 160, height: 100)
    }
}

@main
struct PreviewLabApp: App {
    var body: some Scene { WindowGroup { AppearanceSentinel() } }
}

#Preview("Appearance sentinel", traits: .fixedLayout(width: 160, height: 100)) {
    AppearanceSentinel()
}
