import Foundation
// Original source-guided composition; public casts/Set/String, no private decoder.
let single:[String:Any]=["style":"list","defaultVariant":"unknown"]
let multi:[String:Any]=["defaultVariants":["b","a","b","é","e\u{301}"]]
let cases:[(String,Any)] = [
 ("single",["discriminant":"singleSelect","singleSelectConfiguration":single]),
 ("range",["discriminant":"singleSelect","singleSelectConfiguration":["style":"range","defaultVariant":""]]),
 ("multi",["discriminant":"multiSelect","multiSelectConfiguration":multi]),
 ("empty-set",["discriminant":"multiSelect","multiSelectConfiguration":["defaultVariants":[] as [String]]]),
 ("both-single-active",["discriminant":"singleSelect","singleSelectConfiguration":single,"multiSelectConfiguration":multi]),
 ("both-multi-active",["discriminant":"multiSelect","singleSelectConfiguration":single,"multiSelectConfiguration":multi]),
 ("ignore-malformed-multi",["discriminant":"singleSelect","singleSelectConfiguration":single,"multiSelectConfiguration":false]),
 ("ignore-malformed-single",["discriminant":"multiSelect","singleSelectConfiguration":false,"multiSelectConfiguration":multi]),
 ("unknown-fields",["discriminant":"singleSelect","singleSelectConfiguration":single,"extra":true]),
 ("long-single",["discriminant":"singleSelect","singleSelectConfiguration":["style":"range","defaultVariant":String(repeating:"é👩‍💻",count:300)]]),
 ("many-multi",["discriminant":"multiSelect","multiSelectConfiguration":["defaultVariants":(0..<20).map{"id\($0)"}]]),
 ("missing-tag",["singleSelectConfiguration":single]),
 ("bad-tag-type",["discriminant":true,"singleSelectConfiguration":single]),
 ("unknown-tag",["discriminant":"other","singleSelectConfiguration":single,"multiSelectConfiguration":multi]),
 ("wrong-case",["discriminant":"SingleSelect","singleSelectConfiguration":single]),
 ("empty-tag",["discriminant":"","singleSelectConfiguration":single]),
 ("missing-single",["discriminant":"singleSelect","multiSelectConfiguration":multi]),
 ("missing-multi",["discriminant":"multiSelect","singleSelectConfiguration":single]),
 ("bad-single-root",["discriminant":"singleSelect","singleSelectConfiguration":false,"multiSelectConfiguration":multi]),
 ("bad-multi-root",["discriminant":"multiSelect","multiSelectConfiguration":false,"singleSelectConfiguration":single]),
 ("invalid-style-no-retry",["discriminant":"singleSelect","singleSelectConfiguration":["style":"bad","defaultVariant":"id"],"multiSelectConfiguration":multi]),
 ("invalid-default-no-retry",["discriminant":"singleSelect","singleSelectConfiguration":["style":"list","defaultVariant":true],"multiSelectConfiguration":multi]),
 ("invalid-set-no-retry",["discriminant":"multiSelect","multiSelectConfiguration":["defaultVariants":["id",1]],"singleSelectConfiguration":single]),
 ("missing-style",["discriminant":"singleSelect","singleSelectConfiguration":["defaultVariant":"id"]]),
 ("missing-defaults",["discriminant":"multiSelect","multiSelectConfiguration":[: ] as [String:Any]]),
 ("root",["singleSelect"]),
]
var rows=[[String:Any]]()
for (name,input) in cases {
 var row:[String:Any]=["name":name,"kind":"selection-behavior","input":input,"accepted":false]
 if let fields=input as? [String:Any],let tag=fields["discriminant"] as? String {
  if tag=="singleSelect",let payload=fields["singleSelectConfiguration"] as? [String:Any],let style=payload["style"] as? String,["list","range"].contains(style),let id=payload["defaultVariant"] as? String {
   row["accepted"]=true;row["output"]=["discriminant":tag,"singleSelectConfiguration":["style":style,"defaultVariant":id]]
  } else if tag=="multiSelect",let payload=fields["multiSelectConfiguration"] as? [String:Any],let ids=payload["defaultVariants"] as? [String] {
   row["accepted"]=true;row["output"]=["discriminant":tag,"multiSelectConfiguration":["defaultVariants":Array(Set(ids)).sorted{Array($0.decomposedStringWithCanonicalMapping.utf8).lexicographicallyPrecedes(Array($1.decomposedStringWithCanonicalMapping.utf8))}]]
  }
 }
 rows.append(row)
}
try PropertyListSerialization.data(fromPropertyList:rows,format:.binary,options:0).write(to:URL(fileURLWithPath:CommandLine.arguments[1]))
print("26 public Foundation compositions;11 accepts;15 rejects;no private decoder")
