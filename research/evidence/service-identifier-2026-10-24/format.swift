import Foundation
let values: [UInt64] = [0, 1, 9, 10, 999, 4294967296, 9223372036854775808, UInt64.max]
let result = values.map { $0.description }
let data = try JSONSerialization.data(withJSONObject: result, options: [.sortedKeys])
print(String(data: data, encoding: .utf8)!)
