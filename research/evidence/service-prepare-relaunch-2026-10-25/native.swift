// Public Foundation primitive operations plus original source-guided composition.
// No private framework imports or private decoder calls.
import Foundation
enum Invalid: Error { case value }
func dictionary(_ value: Any) throws -> [String: Any] {
    guard let value = value as? [String: Any] else { throw Invalid.value }; return value
}
func text(_ d: [String: Any], _ key: String) throws -> String {
    guard let value = d[key] as? String else { throw Invalid.value }; return value
}
func bundle(_ value: Any) throws -> [String: Any] {
    let d = try dictionary(value); let id = try text(d, "bundleID")
    var out: [String: Any] = ["bundleID": id, "discriminant": "bundleID"]
    if d["path"] != nil { out["path"] = try text(d, "path"); out["discriminant"] = "pathAndBundleID" }
    return out
}
func descriptor(_ value: Any) throws -> [String: Any] {
    do {
        let d = try dictionary(value); let id = try text(d, "idAcrossRelaunches")
        guard let nested = d["bundle"] else { throw Invalid.value }
        return ["idAcrossRelaunches": id, "bundle": try bundle(nested)]
    } catch { return ["idAcrossRelaunches": "", "bundle": try bundle(value)] }
}
func prepare(_ d: [String: Any]) throws -> [String: Any] {
    let agent: [String: Any]
    do { guard let primary = d["agentDescriptor"] else { throw Invalid.value }; agent = try descriptor(primary) }
    catch { guard let legacy = d["agentIdentifier"] else { throw Invalid.value }; agent = try descriptor(legacy) }
    return ["agentDescriptor": agent, "agentIdentifier": agent["bundle"]!]
}
let b: [String: Any] = ["bundleID": "owned.bundle", "path": "/owned/🦀\n\0"]
let modern: [String: Any] = ["idAcrossRelaunches": "owned-id", "bundle": b]
let cases: [(String,[String:Any])] = [
 ("modern",["agentDescriptor":modern]),
 ("legacy-flat",["agentIdentifier":b]),
 ("legacy-modern",["agentIdentifier":modern]),
 ("primary-flat",["agentDescriptor":b]),
 ("modern-wins",["agentDescriptor":modern,"agentIdentifier":7]),
 ("invalid-primary-retries",["agentDescriptor":7,"agentIdentifier":b]),
 ("invalid-nested-retries",["agentDescriptor":["idAcrossRelaunches":"id","bundle":7],"agentIdentifier":b]),
 ("descriptor-flat-fallback",["agentDescriptor":["idAcrossRelaunches":7,"bundleID":"flat","path":""]]),
 ("nested-wins",["agentDescriptor":["idAcrossRelaunches":"id","bundle":b,"bundleID":"ignored","path":7]]),
 ("ignored-discriminant",["agentDescriptor":["bundleID":"flat","discriminant":7]]),
 ("empty-strings",["agentDescriptor":["idAcrossRelaunches":"","bundle":["bundleID":"","path":""]]]),
 ("absent-path",["agentDescriptor":["bundleID":"flat"]]),
 ("missing-both",[:]),
 ("invalid-path",["agentIdentifier":["bundleID":"bad","path":7]]),
 ("invalid-id",["agentIdentifier":["bundleID":7]]),
 ("invalid-both",["agentDescriptor":7,"agentIdentifier":8]),
 ("invalid-nested-no-flat",["agentIdentifier":["idAcrossRelaunches":"id","bundle":7]])
]
var controls = [[String:Any]]()
for (name, input) in cases {
    var row: [String:Any] = ["name":name,"input":input]
    do { row["output"] = try prepare(input); row["accepted"] = true } catch { row["accepted"] = false }
    controls.append(row)
}
let data = try PropertyListSerialization.data(fromPropertyList: controls, format: .binary, options: 0)
try data.write(to: URL(fileURLWithPath: CommandLine.arguments[1]))
print("17 public Foundation composition controls; no private decoder or relaunch action")
