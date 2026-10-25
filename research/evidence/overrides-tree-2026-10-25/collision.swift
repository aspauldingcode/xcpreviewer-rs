import Foundation
let d=try Data(contentsOf:URL(fileURLWithPath:CommandLine.arguments[1]))
let value=try PropertyListSerialization.propertyList(from:d,options:[],format:nil)
let ns=value as! NSDictionary
let swift=value as! [String:Any]
let entries=ns.allKeys.map {key -> [String:Any] in let k=key as! String;return ["keyBytes":Array(k.utf8),"value":ns[key]!]}
let out:[String:Any] = ["type":String(reflecting:type(of:value)),"nsCount":ns.count,"swiftCount":swift.count,"entries":entries,"NSStringEqual":("é" as NSString).isEqual(to:"e\u{301}")]
let data=try JSONSerialization.data(withJSONObject:out,options:[.prettyPrinted,.sortedKeys]);FileHandle.standardOutput.write(data)
