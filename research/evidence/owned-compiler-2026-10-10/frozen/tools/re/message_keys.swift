// Exact exported Swift getter symbols for the observed Xcode build.
// This uses Swift ABI, not C function pointers. No services are contacted.
import Foundation
@_silgen_name("$s21PreviewsMessagingHost14MessageTypeKeySSvg")
func messageTypeKey() -> String
@_silgen_name("$s21PreviewsMessagingHost16OneWayMessageKeySSvg")
func oneWayMessageKey() -> String
let result = ["MessageTypeKey": messageTypeKey(), "OneWayMessageKey": oneWayMessageKey()]
let data = try JSONSerialization.data(withJSONObject: result, options: [.prettyPrinted, .sortedKeys])
FileHandle.standardOutput.write(data)
print()
