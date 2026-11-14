import SwiftUI
@MainActor func makePreview() -> some View {
    VStack(spacing: 12) {
        Text("SwiftUI preview").font(.title2.bold())
        HStack(spacing: 12) {
            RoundedRectangle(cornerRadius: 12).fill(.blue)
            RoundedRectangle(cornerRadius: 12).fill(.orange)
        }.frame(height: 64)
        Text("Native view → portable canvas").font(.caption)
    }.padding(20).frame(maxWidth: .infinity, maxHeight: .infinity)
      .background(Color.white)
}
