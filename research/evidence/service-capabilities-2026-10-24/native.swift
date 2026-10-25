import Foundation
let inputs: [(String,Any?)] = [("missing",nil),("false",false),("true",true),("int0",NSNumber(value:0)),("int1",NSNumber(value:1)),("int2",NSNumber(value:2)),("negative",NSNumber(value:-1)),("real0",NSNumber(value:0.0)),("real1",NSNumber(value:1.0)),("real2",NSNumber(value:2.0)),("fraction",NSNumber(value:0.5)),("string","true"),("data",Data([0,1])),("array",[true]),("dictionary",["a":true])]
var rows: [[String:Any]] = []
for (label,input) in inputs {
 var payload: [String:Any] = [:];if let input {payload["isRunningInXTP"] = input}
 let bytes = try PropertyListSerialization.data(fromPropertyList:payload,format:.binary,options:0)
 let decoded = try PropertyListSerialization.propertyList(from:bytes,options:[],format:nil) as! [String:Any]
 let result = decoded["isRunningInXTP"] as? Bool
 var row: [String:Any] = ["label":label,"payload":decoded,"accepted":result != nil]
 if let result {row["value"] = result}
 rows.append(row)
}
try PropertyListSerialization.data(fromPropertyList:rows,format:.binary,options:0).write(to:URL(fileURLWithPath:CommandLine.arguments[1]))
