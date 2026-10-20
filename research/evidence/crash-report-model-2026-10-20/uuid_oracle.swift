import Foundation
let cases = ["00112233-4455-6677-8899-aabbccddeeff", "00112233-4455-6677-8899-AABBCCDDEEFF", "00112233445566778899aabbccddeeff", "{00112233-4455-6677-8899-aabbccddeeff}", " 00112233-4455-6677-8899-aabbccddeeff", "00112233-4455-6677-8899-aabbccddeeff ", "00112233-4455-6677-8899-aabbccddeefg", "00000000-0000-0000-0000-000000000000", "", "00112233−4455-6677-8899-aabbccddeeff"]
let values = cases.map { value in ["input": value, "canonical": UUID(uuidString: value)?.uuidString as Any? ?? NSNull()] as [String:Any] }
let bytes = try JSONSerialization.data(withJSONObject: values, options: [.sortedKeys])
FileHandle.standardOutput.write(bytes)
