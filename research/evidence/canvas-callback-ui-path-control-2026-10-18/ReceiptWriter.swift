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
