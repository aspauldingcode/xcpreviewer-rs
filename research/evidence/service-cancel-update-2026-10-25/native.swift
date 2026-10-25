import Foundation
let inputs: [(String,Any)] = [("zero",0),("small",123),("signedMax",NSNumber(value:Int64.max)),("unsignedHigh",NSNumber(value:UInt64(Int64.max)+1)),("unsignedMax",NSNumber(value:UInt64.max)),("bool",true),("real",NSNumber(value:123.0)),("fraction",NSNumber(value:0.5)),("negative",-1),("realEndpoint",NSNumber(value:Double(UInt64.max)))]
var rows: [[String:Any]] = []
for (label,input) in inputs {
 let dictionary: [String:Any] = ["pid":NSNumber(value:Int32(-1)),"contentIdentifier":"owned/content/🙂","updateSeed":input]
 let data=try PropertyListSerialization.data(fromPropertyList:dictionary,format:.binary,options:0)
 let decoded=try PropertyListSerialization.propertyList(from:data,options:[],format:nil) as! [String:Any]
 let seed=decoded["updateSeed"] as? UInt64
 var row: [String:Any] = ["label":label,"input":decoded,"accepted":seed != nil]
 if let seed {row["canonical"]=["pid":Int32(-1),"contentIdentifier":"owned/content/🙂","updateSeed":NSNumber(value:seed)]}
 rows.append(row)
}
try PropertyListSerialization.data(fromPropertyList:rows,format:.binary,options:0).write(to:URL(fileURLWithPath:CommandLine.arguments[1]))
if CommandLine.arguments.count > 3 {
 let container=try Data(contentsOf:URL(fileURLWithPath:CommandLine.arguments[2]))
 let blobs=try PropertyListSerialization.propertyList(from:container,options:[],format:nil) as! [Data]
 let decoded=try blobs.map {try PropertyListSerialization.propertyList(from:$0,options:[],format:nil)}
 try PropertyListSerialization.data(fromPropertyList:decoded,format:.binary,options:0).write(to:URL(fileURLWithPath:CommandLine.arguments[3]))
}
