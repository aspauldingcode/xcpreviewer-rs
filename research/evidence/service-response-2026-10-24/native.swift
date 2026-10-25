import Foundation
struct OwnedFailure: Error, CustomNSError {
    static var errorDomain: String { "owned.swift" }
    var errorCode: Int { -17 }
    var errorUserInfo: [String: Any] { ["reason":"owned 🪨", "bytes":Data([0,17,255])] }
}
func project(_ value: Any) -> NSError? { value as? NSError }
let ns = NSError(domain:"owned.native",code:Int.min,userInfo:["reason":"owned NSError"])
let error: any Error = OwnedFailure()
let cases: [(String,Any)] = [("NSError",ns),("SwiftError",error),("NSObject",NSObject()),("String","owned")]
var rows: [[String:Any]] = []
for (name,value) in cases {
    if let result=project(value) {
        rows.append(["input":name,"cast":true,"domain":result.domain,"code":result.code,"reason":result.userInfo["reason"] as? String ?? "", "bytes":(result.userInfo["bytes"] as? Data)?.base64EncodedString() ?? "", "same_instance": name == "NSError" && result === ns])
    } else { rows.append(["input":name,"cast":false]) }
}
let output=try JSONSerialization.data(withJSONObject:rows, options:[.sortedKeys])
print(String(decoding:output,as:UTF8.self))
