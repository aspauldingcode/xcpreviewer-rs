import Foundation
var d=[String:String]();d["e\u{301}"]="first";d["é"]="last"
let key=d.keys.first!
let result:[String:Any]=["count":d.count,"lookup":d["é"]!,"keyBytes":Array(key.utf8),"expectedFirstKeyBytes":Array("e\u{301}".utf8)]
try JSONSerialization.data(withJSONObject:result,options:[.sortedKeys,.prettyPrinted]).write(to:URL(fileURLWithPath:CommandLine.arguments[1]))
