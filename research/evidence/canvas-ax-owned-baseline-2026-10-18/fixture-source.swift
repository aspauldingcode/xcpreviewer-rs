import Foundation
import Darwin

enum ReceiptEvent: String { case appear, increment }

struct ReceiptWriter {
    static func posixError() -> POSIXError {
        POSIXError(POSIXErrorCode(rawValue: errno) ?? .EIO)
    }

    // Research-only publication to an existing private, operator-owned directory.
    // Failed pending files are deliberately retained. No overwrite or retry.
    static func write(directory: URL, nonce: String, view: UUID,
                      event: ReceiptEvent, sequence: Int, count: Int) throws {
        guard nonce.count == 32, nonce.allSatisfy({ "0123456789abcdef".contains($0) }),
              (0...3).contains(sequence), (0...3).contains(count) else {
            throw CocoaError(.fileWriteInvalidFileName)
        }
        let pid = ProcessInfo.processInfo.processIdentifier
        let viewID = view.uuidString.lowercased()
        let name = "pid-\(pid)-view-\(viewID)-sequence-\(sequence).json"
        let pending = ".pending-" + name
        let bytes = Data(("{\"count\":\(count),\"event\":\"\(event.rawValue)\",\"nonce\":\"\(nonce)\",\"pid\":\(pid),\"schema\":1,\"sequence\":\(sequence),\"view\":\"\(viewID)\"}\n").utf8)
        let parent = Darwin.open(directory.path, O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC)
        guard parent >= 0 else { throw posixError() }
        defer { _ = Darwin.close(parent) }
        var info = stat()
        guard fstat(parent, &info) == 0 else { throw posixError() }
        guard info.st_uid == getuid(), info.st_mode & 0o777 == 0o700 else {
            throw CocoaError(.fileWriteNoPermission)
        }
        let fd = Darwin.openat(parent, pending, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, mode_t(0o600))
        guard fd >= 0 else { throw posixError() }
        defer { _ = Darwin.close(fd) }
        try bytes.withUnsafeBytes { (buffer: UnsafeRawBufferPointer) in
            var offset = 0
            while offset < buffer.count {
                let written = Darwin.write(fd, buffer.baseAddress!.advanced(by: offset), buffer.count - offset)
                if written < 0 && errno == EINTR { continue }
                guard written > 0 else { throw posixError() }
                offset += written
            }
        }
        guard fsync(fd) == 0 else { throw posixError() }
        guard linkat(parent, pending, parent, name, 0) == 0 else { throw posixError() }
        guard unlinkat(parent, pending, 0) == 0 else { throw posixError() }
    }
}

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
                directory: URL(fileURLWithPath: "/private/tmp/xcpreviewer-callback-24e447b779314b648597edd1dfea717e/receipts", isDirectory: true),
                nonce: "24e447b779314b648597edd1dfea717e", view: viewID,
                event: event, sequence: currentSequence, count: count)
        } catch {
            receiptError = String(describing: error)
        }
    }

    var body: some View {
        VStack(spacing: 10) {
            Text("Owned callback probe").font(.headline)
            Text(viewID.uuidString.lowercased()).font(.system(size: 9, design: .monospaced))
            Text("Count: \(count)").monospacedDigit().accessibilityIdentifier("owned.callback.count")
            Button("Increment") { count += 1; emit(.increment) }
                .disabled(receiptError != nil || count >= 3)
                .accessibilityIdentifier("owned.callback.increment").accessibilityLabel("Owned Increment")
            if let receiptError { Text("Receipt failed: \(receiptError)").font(.caption).foregroundStyle(.red) }
        }
        .padding(16).frame(width: 320, height: 220)
        .background(Color.white).foregroundStyle(Color.black)
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("owned.callback.root").accessibilityLabel("Owned callback group")
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
