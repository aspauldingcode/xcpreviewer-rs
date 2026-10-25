import Foundation
let controls: [[String:Any]] = [
 ["workspaceID":"owned/workspace/🙂"],
 ["workspaceID":"","killAgents":false],
 ["workspaceID":"owned","killAgents":true],
 ["workspaceID":"owned","killAgents":0],
 ["workspaceID":"owned","killAgents":1],
 ["workspaceID":"owned","killAgents":2],
 ["workspaceID":"owned","killAgents":"true"],
 ["killAgents":true],
 ["workspaceID":42,"killAgents":true],
 ["workspaceID":"owned","killAgents":NSNumber(value:UInt64.max)],
 ["workspaceID":"owned","killAgents":NSNumber(value:1.0),"extra":Data([0,1])]
]
var rows: [[String:Any]] = []
for input in controls {
 let bytes=try PropertyListSerialization.data(fromPropertyList:input,format:.binary,options:0)
 let decoded=try PropertyListSerialization.propertyList(from:bytes,options:[],format:nil) as! [String:Any]
 var canonical:[String:Any]? = nil
 if let workspace=decoded["workspaceID"] as? String {
  if let input=decoded["killAgents"] {if let flag=input as? Bool {canonical=["workspaceID":workspace,"killAgents":flag]}}
  else {canonical=["workspaceID":workspace,"killAgents":false]}
 }
 var row:[String:Any] = ["input":decoded,"accepted":canonical != nil]
 if let canonical {row["canonical"]=canonical};rows.append(row)
}
try PropertyListSerialization.data(fromPropertyList:rows,format:.binary,options:0).write(to:URL(fileURLWithPath:CommandLine.arguments[1]))
func optionalBytes(_ input: Bool?) -> [UInt8] {var value=input;return withUnsafeBytes(of:&value){Array($0)}}
precondition(MemoryLayout<Bool?>.size==1)
let layout:[String:Any] = ["absent":optionalBytes(nil),"false":optionalBytes(false),"true":optionalBytes(true)]
print(String(data:try JSONSerialization.data(withJSONObject:layout,options:[.sortedKeys]),encoding:.utf8)!)
