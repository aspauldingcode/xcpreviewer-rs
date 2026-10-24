import Foundation
let destination = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
let info: [String: Any] = ["bytes": Data((0..<128).map(UInt8.init)), "nested": ["ok": true, "name": "owned/🪨"], "items": ["first", "second"]]
for (name, domain, code, userInfo) in [("empty", "", 0, [:] as [String:Any]), ("negative", "owned/error/🪨", -17, info), ("min", "owned/min", Int.min, info), ("max", "owned/max", Int.max, info)] {
    let error = NSError(domain: domain, code: code, userInfo: userInfo)
    let fields: [String: Any] = ["domain": error.domain, "code": error.code, "userInfo": error.userInfo]
    let data = try PropertyListSerialization.data(fromPropertyList: fields, format: .binary, options: 0)
    try data.write(to: destination.appendingPathComponent(name + ".bplist"))
    print("\(name)\t\(error.code)\t\(fields.count)\t\(error.userInfo.count)")
}
