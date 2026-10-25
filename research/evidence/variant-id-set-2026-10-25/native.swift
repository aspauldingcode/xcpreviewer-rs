import Foundation
// Source-guided composition with actual public Swift Set/String and Foundation.
var cases:[(String,Any)] = [
 ("empty",["defaultVariants":[] as [String]]),
 ("one",["defaultVariants":["id"]]),
 ("ordered",["defaultVariants":["z","a","m"]]),
 ("duplicates",["defaultVariants":["b","a","b","a"]]),
 ("empty-opaque-ids",["defaultVariants":["","unknown","\n\"é👩‍💻"]]),
 ("unknown-omitted",["defaultVariants":["id"],"extra":true]),
 ("canonical-equivalence",["defaultVariants":["é","e\u{301}","Å","A\u{30a}","Å","각","각"]]),
 ("first-spelling-reverse",["defaultVariants":["e\u{301}","é","A\u{30a}","Å","각","각"]]),
 ("combining-order",["defaultVariants":["a\u{315}\u{300}","a\u{300}\u{315}"]]),
 ("compatibility-distinct",["defaultVariants":["ﬀ","ff","Ａ","A","a","á","a\u{301}\u{34f}"]]),
 ("unicode18-boundary",["defaultVariants":["a\u{5c8}\u{300}","a\u{300}\u{5c8}","a\u{10ef0}\u{300}","a\u{300}\u{10ef0}"]]),
 ("long",["defaultVariants":[String(repeating:"é👩‍💻",count:300)]]),
 ("many",["defaultVariants":(0..<20).map{"id\($0)"}]),
 ("missing",[: ] as [String:Any]),
 ("string",["defaultVariants":"id"]),
 ("dictionary",["defaultVariants":["id":true]]),
 ("number",["defaultVariants":[1]]),
 ("bool",["defaultVariants":[true]]),
 ("nested",["defaultVariants":[["id"]]]),
 ("mixed",["defaultVariants":["id",1,"id"]]),
 ("root",["id"]),
]
for count in [2,5,16,128] {cases.append(("representative-\(count)",["defaultVariants":["e\u{301}"]+Array(repeating:"é",count:count)]))}
var rows = [[String:Any]]()
for (name,input) in cases {
 var row:[String:Any] = ["name":name,"kind":"multi-selection","input":input,"accepted":false]
 if let d=input as? [String:Any],let ids=d["defaultVariants"] as? [String] {
  row["accepted"]=true
  // Sorting is the portable policy; native Set iteration itself is unordered.
  row["output"]=["defaultVariants":Array(Set(ids)).sorted { Array($0.decomposedStringWithCanonicalMapping.utf8).lexicographicallyPrecedes(Array($1.decomposedStringWithCanonicalMapping.utf8)) }]
 }
 rows.append(row)
}
try PropertyListSerialization.data(fromPropertyList:rows,format:.binary,options:0).write(to:URL(fileURLWithPath:CommandLine.arguments[1]))
print("25 compositions;17 accepted;8 rejected;public Swift Set/String;private decoder not invoked")
