import Foundation
let cases: [(String, Any)] = [
    ("integer", NSNumber(value: Int64(-17))),
    ("bool", NSNumber(value: true)),
    ("false", NSNumber(value: false)),
    ("min_integer", NSNumber(value: Int64.min)),
    ("max_integer", NSNumber(value: Int64.max)),
    ("min_real", NSNumber(value: Double(Int64.min))),
    ("above_real_max", NSNumber(value: Double(9223372036854775808.0))),
    ("high_next_up", NSNumber(value: Double(9223372036854775808.0).nextUp)),
    ("low_next_down", NSNumber(value: Double(Int64.min).nextDown)),
    ("huge_real", NSNumber(value: Double(18446744073709551616.0))),
    ("integral_real", NSNumber(value: 3.0)),
    ("fraction", NSNumber(value: 3.5)),
    ("negative_zero", NSNumber(value: -0.0)),
    ("nan", NSNumber(value: Double.nan)),
    ("infinity", NSNumber(value: Double.infinity)),
    ("uint64_max", NSNumber(value: UInt64.max)),
    ("string", "3")
]
var out: [String: Any] = [:]
for (name, value) in cases {
    let dictionary = NSDictionary(dictionary: ["code": value]) as! [String: Any]
    out[name] = (dictionary["code"] as? Int).map { String($0) } ?? NSNull() as Any
}
let data = try JSONSerialization.data(withJSONObject: out, options: [.sortedKeys])
print(String(data: data, encoding: .utf8)!)
