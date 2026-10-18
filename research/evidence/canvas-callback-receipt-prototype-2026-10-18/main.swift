import Foundation
import Darwin

let nonce = "60fd2da461f6404ea93e47eb59d6831a"
let view = UUID(uuidString: "01234567-89ab-cdef-0123-456789abcdef")!
do {
    guard CommandLine.arguments.count == 3 else { exit(2) }
    let directory = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
    let mode = CommandLine.arguments[2]
    guard mode == "positive" || mode == "duplicate" else { exit(2) }
    try ReceiptWriter.write(directory: directory, nonce: nonce, view: view, event: .appear, sequence: 0, count: 0)
    if mode == "duplicate" {
        try ReceiptWriter.write(directory: directory, nonce: nonce, view: view, event: .increment, sequence: 0, count: 1)
    } else {
        for count in 1...3 {
            try ReceiptWriter.write(directory: directory, nonce: nonce, view: view, event: .increment, sequence: count, count: count)
        }
    }
    print("owned receipt writer completed")
} catch {
    FileHandle.standardError.write(Data(("owned receipt writer failed: \(error)\n").utf8))
    exit(1)
}
