import Foundation
let dir=URL(fileURLWithPath:CommandLine.arguments[1]);var rows:[[String:Any]]=[]
for name in ["default","full","prefixed","empty"] {
 var expected:[String:Any] = ["errorType":"leaf","errorTypeDescription":"[Remote] Unknown Error","isPotentialCrash":true,"isNative":false]
 if name=="full" {expected=["errorType":"leaf","errorTypeDescription":"[Remote] owned 🪨","highValueTitle":"","lowValueTitle":"low","additionalInfo":"details\0雪","additionalDiagnostics":"line\n","severity":"info","options":Int.min,"isPotentialCrash":false,"isNative":true]}
 if name=="prefixed" {expected["errorTypeDescription"]="[Remote] stable";expected["severity"]="error";expected["options"]=Int.max}
 if name=="empty" {expected["errorTypeDescription"]="[Remote] "}
 let data=try Data(contentsOf:dir.appendingPathComponent(name+".bplist"));let actual=try PropertyListSerialization.propertyList(from:data,options:[],format:nil) as! NSDictionary
 precondition(actual.isEqual(to:expected));rows.append(["name":name,"fields":actual.count,"bytes":data.count,"matches":true])
}
FileHandle.standardOutput.write(try JSONSerialization.data(withJSONObject:rows,options:[.sortedKeys,.prettyPrinted]));print("")
