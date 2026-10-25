import Foundation
import Darwin
let token: [NSNumber] = [0,1,2,3,4,12345,6,7]
let cases: [[String:Any]] = [
 ["pid":0],["pid":-1],["discriminant":"pid","pid":Int32.max],
 ["discriminant":"pid","pid":NSNumber(value:1.0)],
 ["discriminant":"pid","pid":true],
 ["discriminant":"pid","pid":NSNumber(value:2147483648.0)],
 ["discriminant":"unknown","pid":42],["discriminant":3,"pid":43],
 ["discriminant":"auditToken","auditToken":["val":token],"pid":-9],
 ["discriminant":"auditToken","auditToken":["val":Array(repeating:NSNumber(value:UInt32.max),count:8)]],
 ["discriminant":"auditToken","auditToken":["val":[0,1]],"pid":44],
 ["discriminant":"auditToken","auditToken":["val":[0,1]]],
 ["discriminant":"auditToken","auditToken":["val":Array(repeating:NSNumber(value:-1),count:8)],"pid":45],
 ["discriminant":"pid","auditToken":["val":token]],
 ["auditToken":["val":token],"pid":46],
 ["discriminant":"auditToken","auditToken":["val":Array(repeating:NSNumber(value:1.0),count:8)]],
 ["discriminant":"auditToken","auditToken":["val":Array(repeating:true,count:8)]],
 ["discriminant":"auditToken","auditToken":["val":Array(repeating:NSNumber(value:0.5),count:8)],"pid":47],
 ["pid":NSNumber(value:-2147483648.0)],["pid":NSNumber(value:0.5)],[:]
]
var records: [[String:Any]] = []
for original in cases {
 let bytes = try PropertyListSerialization.data(fromPropertyList:original,format:.binary,options:0)
 let input = try PropertyListSerialization.propertyList(from:bytes,options:[],format:nil) as! [String:Any]
 var canonical: [String:Any]? = nil
 if let discriminant=input["discriminant"] as? String, discriminant == "auditToken", let fields=input["auditToken"] as? [String:Any], let words=fields["val"] as? [UInt32],words.count==8 {
  let token = audit_token_t(val:(words[0],words[1],words[2],words[3],words[4],words[5],words[6],words[7]))
  let pid = audit_token_to_pid(token)
  canonical=["discriminant":"auditToken","auditToken":["val":words],"pid":pid]
 } else if let pid=input["pid"] as? Int32 {canonical=["discriminant":"pid","pid":pid]}
 var row: [String:Any] = ["input":input,"accepted":canonical != nil]
 if let canonical {row["canonical"] = canonical}
 records.append(row)
}
try PropertyListSerialization.data(fromPropertyList:records,format:.binary,options:0).write(to:URL(fileURLWithPath:CommandLine.arguments[1]))
