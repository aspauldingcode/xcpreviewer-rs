import Foundation
// Original public Foundation composition guided by static source. No private decoder.
let cases: [(String,Any)] = [
 ("list",["style":"list","defaultVariant":"one"]),
 ("range",["style":"range","defaultVariant":"two"]),
 ("empty-id",["style":"list","defaultVariant":""]),
 ("opaque-id",["style":"range","defaultVariant":"unknown\n\"é👩‍💻"]),
 ("long-id",["style":"list","defaultVariant":String(repeating:"é👩‍💻",count:300)]),
 ("unknown-omitted",["style":"list","defaultVariant":"one","extra":true]),
 ("missing-style",["defaultVariant":"one"]),
 ("missing-default",["style":"list"]),
 ("unknown-style",["style":"slider","defaultVariant":"one"]),
 ("empty-style",["style":"","defaultVariant":"one"]),
 ("case-sensitive",["style":"List","defaultVariant":"one"]),
 ("numeric-style",["style":1,"defaultVariant":"one"]),
 ("bool-default",["style":"list","defaultVariant":true]),
 ("array-default",["style":"list","defaultVariant":["one"]]),
 ("dict-default",["style":"range","defaultVariant":["rawValue":"one"]]),
 ("wrong-root",["list","one"]),
 ("both-missing",[: ] as [String:Any]),
]
var rows = [[String:Any]]()
for (name,input) in cases {
 var row:[String:Any] = ["name":name,"kind":"single-selection","input":input,"accepted":false]
 if let d=input as? [String:Any], let style=d["style"] as? String, ["list","range"].contains(style), let id=d["defaultVariant"] as? String {
  row["accepted"]=true; row["output"]=["style":style,"defaultVariant":id]
 }
 rows.append(row)
}
try PropertyListSerialization.data(fromPropertyList:rows,format:.binary,options:0).write(to:URL(fileURLWithPath:CommandLine.arguments[1]))
print("17 public Foundation compositions;6 accepted;11 rejected;private decoder not invoked")
