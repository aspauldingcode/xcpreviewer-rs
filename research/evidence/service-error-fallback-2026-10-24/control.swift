import Foundation
let output = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
let reason = "Failed to encode full userInfo due to incompatible types"
for (name, domain, code) in [("negative", "owned/fallback/🪨", -17), ("min", "owned/min", Int.min), ("max", "owned/max", Int.max)] {
    let error = NSError(domain: domain, code: code, userInfo: [NSLocalizedDescriptionKey: "owned failure 🪨", "incompatible": NSObject()])
    let original: [String:Any] = ["domain":error.domain,"code":error.code,"userInfo":error.userInfo]
    precondition(!PropertyListSerialization.propertyList(original, isValidFor: .binary))
    do {
        _ = try PropertyListSerialization.data(fromPropertyList: original, format: .binary, options: 0)
        fatalError("Unexpected valid original userInfo")
    } catch { print("\(name) original Foundation encoding rejected") }
    let retry: [String:Any] = ["domain":error.domain,"code":error.code,"userInfo":[NSLocalizedDescriptionKey:error.localizedDescription, NSDebugDescriptionErrorKey:reason]]
    let bytes = try PropertyListSerialization.data(fromPropertyList: retry, format: .binary, options: 0)
    try bytes.write(to:output.appendingPathComponent(name + ".bplist"))
}
print("keys\t\(NSLocalizedDescriptionKey)\t\(NSDebugDescriptionErrorKey)")
