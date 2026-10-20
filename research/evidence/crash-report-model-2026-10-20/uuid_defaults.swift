import Foundation
let values = (0..<4).map { _ in UUID().uuidString }
let bytes = try JSONSerialization.data(withJSONObject: values, options: [])
FileHandle.standardOutput.write(bytes)
