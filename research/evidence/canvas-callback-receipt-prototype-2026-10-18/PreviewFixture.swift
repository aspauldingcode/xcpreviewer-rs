import SwiftUI

// Diagnostic I/O is deliberate instrumentation, not product preview behavior.
@MainActor
struct CallbackProbe: View {
    @State private var count = 0
    @State private var viewID = UUID()
    @State private var sequence = 0
    @State private var receiptError: String?

    private func emit(_ event: ReceiptEvent) {
        let currentSequence = sequence
        sequence += 1 // A failed write leaves a visible gap; never retry silently.
        do {
            try ReceiptWriter.write(
                directory: URL(fileURLWithPath: "/private/tmp/xcpreviewer-callback-60fd2da461f6404ea93e47eb59d6831a/receipts", isDirectory: true),
                nonce: "60fd2da461f6404ea93e47eb59d6831a", view: viewID,
                event: event, sequence: currentSequence, count: count)
        } catch {
            receiptError = String(describing: error)
        }
    }

    var body: some View {
        VStack(spacing: 10) {
            Text("Owned callback probe").font(.headline)
            Text(viewID.uuidString.lowercased()).font(.system(size: 9, design: .monospaced))
            Text("Count: \(count)").monospacedDigit()
            Button("Increment") { count += 1; emit(.increment) }
                .disabled(receiptError != nil || count >= 3)
            if let receiptError { Text("Receipt failed: \(receiptError)").font(.caption).foregroundStyle(.red) }
        }
        .padding(16).frame(width: 320, height: 220)
        .background(Color.white).foregroundStyle(Color.black)
        .onAppear { if receiptError == nil { emit(.appear) } }
    }
}

@main
struct PreviewLabApp: App {
    var body: some Scene { WindowGroup { Text("Owned probe container") } }
}
#Preview("Primary layers", traits: .fixedLayout(width: 64, height: 48)) {
    Color.blue.frame(width: 64, height: 48)
}
#Preview("Text and interaction", traits: .fixedLayout(width: 320, height: 220)) {
    CallbackProbe().environment(\.colorScheme, .light)
}
#Preview("Layout edit", traits: .fixedLayout(width: 320, height: 180)) {
    Text("Owned layout reference").frame(width: 320, height: 180).background(.white).foregroundStyle(.black)
}
