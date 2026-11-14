import SwiftUI

@MainActor func makeMyPreview() -> some View {
    VStack(spacing: 12) {
        Text("SwiftUI preview").font(.title2.bold())
        HStack(spacing: 12) {
            RoundedRectangle(cornerRadius: 12).fill(.gray)
            RoundedRectangle(cornerRadius: 12).fill(.green)
        }.frame(height: 64)
        SimpleCounterView()
        Text("Native view → portable canvas").font(.caption)
    }.padding(20).frame(maxWidth: .infinity, maxHeight: .infinity)
      .background(Color.yellow)
}

private struct SimpleCounterView: View {
    @State private var count = 0
    var body: some View {
        HStack(spacing: 20) {
            Button { count -= 1 } label: {
                Image(systemName: "minus").frame(minWidth: 44, minHeight: 44)
            }.accessibilityLabel("Decrease count")
            Text(count, format: .number).font(.title.bold()).monospacedDigit()
                .accessibilityLabel("Count: \(count)")
            Button { count += 1 } label: {
                Image(systemName: "plus").frame(minWidth: 44, minHeight: 44)
            }.accessibilityLabel("Increase count")
        }.buttonStyle(.borderedProminent)
    }
}
#Preview("My Preview") { makeMyPreview() }
