import SwiftUI
@MainActor func makePreview() -> some View {
    Text("Adaptive SwiftUI")
        .font(.largeTitle.bold())
        .foregroundStyle(.primary)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(.background)
}
