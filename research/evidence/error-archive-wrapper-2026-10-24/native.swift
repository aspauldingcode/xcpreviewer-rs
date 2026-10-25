import Foundation
func leaf(_ name:String,_ crash:Bool,_ native:Bool)->[String:Any]{["errorType":"leaf","errorTypeDescription":"[Remote] "+name,"isPotentialCrash":crash,"isNative":native]}
func wrap(_ main:[String:Any],_ underlying:[String:Any])->[String:Any]{["errorType":"wrapper","main":main,"underlying":underlying]}
let dir=URL(fileURLWithPath:CommandLine.arguments[1]);var rows:[[String:Any]]=[]
for name in ["simple","nested-main","nested-underlying"]{let main=leaf("main",true,false),cause=leaf("cause 🪨",false,true),root=leaf("root",true,true);let expected = name=="simple" ? wrap(main,cause) : (name=="nested-main" ? wrap(wrap(main,cause),root) : wrap(main,wrap(cause,root)))
 let data=try Data(contentsOf:dir.appendingPathComponent(name+".bplist"));let actual=try PropertyListSerialization.propertyList(from:data,options:[],format:nil) as! NSDictionary;precondition(actual.isEqual(to:expected));rows.append(["name":name,"bytes":data.count,"matches":true])
}
FileHandle.standardOutput.write(try JSONSerialization.data(withJSONObject:rows,options:[.prettyPrinted,.sortedKeys]));print("")
