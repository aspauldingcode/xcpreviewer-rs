import Foundation
let archiveKey="UVHumanReadableError"
let cases: [(String,Any?)] = [
 ("missing",nil), ("string","archive"), ("data",Data()), ("array",[String]()),
 ("empty",[String:Any]()), ("nested",["unknown":Data([0,128,255]),"nested":["code":Int.min]] as [String:Any]),
 ("non_string_key",NSDictionary(object:"value",forKey:NSNumber(value:17))),
 ("nsstring_key",NSDictionary(object:"value",forKey:"owned" as NSString))
]
var rows:[[String:Any]]=[]
for (name,value) in cases {
 var info:[String:Any]=[:]; if let value {info[archiveKey]=value}
 let error=NSError(domain:"owned",code:17,userInfo:info)
 let dictionary=error.userInfo[archiveKey] as? [String:Any]
 let expected=["empty","nested","nsstring_key"].contains(name)
 precondition((dictionary != nil)==expected)
 rows.append(["name":name,"dictionary":dictionary != nil,"count":dictionary?.count ?? -1])
}
let output=try JSONSerialization.data(withJSONObject:rows,options:[.prettyPrinted,.sortedKeys]);FileHandle.standardOutput.write(output);print("")
