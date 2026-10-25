import Foundation
struct Key:Hashable {let category:String;let overrides:[String]}
enum Invalid:Error {case value}
func keys(_ input:Any)throws->[String:Any]{guard let array=input as? [Any] else{throw Invalid.value};let requests=try array.map{value->Key in guard let d=value as? [String:Any],let c=d["contentCategory"] as? String,let ids=d["requestedOverrides"] as? [String] else{throw Invalid.value};return Key(category:c,overrides:ids)};var map=[Key:Int](),indices=[Int]();for (index,key) in requests.enumerated(){if let old=map[key]{indices.append(old)}else{map[key]=index;indices.append(index)}};return ["representatives":indices,"uniqueKeys":map.count]}
func r(_ c:String="cat",_ ids:[String]=[])->[String:Any]{["contentCategory":c,"requestedOverrides":ids]}
let cases:[(String,Any)]=[
 ("empty-batch",[] as [Any]),("one-empty-request",[r()]),("identical",[r("cat",["a"]),r("cat",["a"])]),
 ("category-differs",[r("a"),r("b")]),("override-differs",[r("cat",["a"]),r("cat",["b"])]),
 ("order-significant",[r("cat",["a","b"]),r("cat",["b","a"])]),
 ("duplicates-significant",[r("cat",["a"]),r("cat",["a","a"])]),
 ("duplicate-placement",[r("cat",["a","b","a"]),r("cat",["a","a","b"])]),
 ("canonical-category",[r("é",["a"]),r("e\u{301}",["a"])]),
 ("canonical-override",[r("cat",["é"]),r("cat",["e\u{301}"])]),
 ("canonical-positionwise",[r("é",["é","가"]),r("e\u{301}",["e\u{301}","가"])]),
 ("canonical-combining-order",[r("cat",["a\u{315}\u{300}"]),r("cat",["a\u{300}\u{315}"])]),
 ("case-sensitive",[r("Cat",["a"]),r("cat",["a"]),r("cat",["A"])]),
 ("compatibility-distinct",[r("cat",["ﬁ"]),r("cat",["fi"])]),
 ("empty-id-distinct",[r(),r("cat",[""])]),
 ("empty-category",[r(""),r(""),r("cat")]),
 ("nonadjacent-first-representative",[r("cat",["a"]),r("cat",["b"]),r("cat",["a"]),r("cat",["b"])]),
 ("unknown-open-values",[r("unknown",["opaque"]),r("unknown",["opaque"])]),
 ("ignored-extra-field",[r(),["contentCategory":"cat","requestedOverrides":[] as [String],"ignored":true]]),
 ("long-many",(0..<24).map{r("cat",[String(repeating:"é👩‍💻\n",count:300),"v\($0 % 3)"])}),
 ("not-array",r()),("not-dictionary",[false]),("missing-category",[["requestedOverrides":[] as [String]]]),
 ("missing-overrides",[["contentCategory":"cat"]]),("bad-category",[["contentCategory":true,"requestedOverrides":[] as [Any]]] as [Any]),
 ("malformed-late-element",[r(),["contentCategory":"cat","requestedOverrides":["a",false]]] as [Any])
]
var rows=[[String:Any]]()
for (name,input) in cases{var row:[String:Any]=["name":name,"kind":"override-cache-keys","input":input,"accepted":false];do{row["output"]=try keys(input);row["accepted"]=true}catch{};rows.append(row)}
try PropertyListSerialization.data(fromPropertyList:rows,format:.binary,options:0).write(to:URL(fileURLWithPath:CommandLine.arguments[1]))
print("26 original public Swift Hashable/Dictionary/Foundation compositions;20 accept/six reject;no private cache invocation or native hash-bit parity")
