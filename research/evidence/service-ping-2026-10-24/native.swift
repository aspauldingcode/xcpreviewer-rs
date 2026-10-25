import Foundation
let key = "__unique_service_message_identifier"
let controls: [[String:Any]] = [
 ["messageType":"ping","payload":[String:Any]()],
 ["messageType":"ping","payload":[key:"owned/ping/🙂"]],
 ["messageType":"ping","payload":[key:"", "ignored":Data([0,1,255])],"rootExtra":"ignored"],
 ["messageType":"ping","payload":["identifier":"wrong-payload-key"],key:"wrong-root"]
]
let data = try PropertyListSerialization.data(fromPropertyList: controls, format:.binary, options:0)
try data.write(to:URL(fileURLWithPath:CommandLine.arguments[1]))
