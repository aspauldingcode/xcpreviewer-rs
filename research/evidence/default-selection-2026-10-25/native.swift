import Foundation
// Public primitive casts/serialization with original source-guided composition.
enum Invalid:Error { case value }
func dict(_ v:Any)throws->[String:Any]{guard let d=v as? [String:Any] else{throw Invalid.value};return d}
func text(_ d:[String:Any],_ key:String)throws->String{guard let s=d[key] as? String else{throw Invalid.value};return s}
func effect(_ v:Any)throws->[String:Any]{["id":try text(dict(v),"id")]}
func variant(_ v:Any)throws->[String:Any]{
 let d=try dict(v);let effects:[[String:Any]]
 if let value=d["renderEffects"]{guard let array=value as? [Any] else{throw Invalid.value};effects=try array.map(effect)}
 else{guard let value=d["renderEffect"] else{throw Invalid.value};effects=[try effect(value)]}
 let id=try text(d,"id"),name=try text(d,"displayName")
 var out:[String:Any]=["id":id,"displayName":name,"renderEffects":effects,"renderEffect":effects.first ?? ["id":"Missing"]]
 if d["interfaceOrientationOverride"] != nil{let value=try text(d,"interfaceOrientationOverride");guard ["portrait","portraitUpsideDown","landscapeLeft","landscapeRight"].contains(value) else{throw Invalid.value};out["interfaceOrientationOverride"]=value}
 return out
}
func behavior(_ v:Any)throws->[String:Any] {
 let f=try dict(v),tag=try text(f,"discriminant")
 if tag=="singleSelect" {let p=try dict(f["singleSelectConfiguration"] as Any),style=try text(p,"style"),id=try text(p,"defaultVariant");guard ["list","range"].contains(style) else{throw Invalid.value};return ["discriminant":tag,"singleSelectConfiguration":["style":style,"defaultVariant":id]]}
 if tag=="multiSelect" {let p=try dict(f["multiSelectConfiguration"] as Any);guard let ids=p["defaultVariants"] as? [String] else{throw Invalid.value};return ["discriminant":tag,"multiSelectConfiguration":["defaultVariants":Array(Set(ids)).sorted{Array($0.decomposedStringWithCanonicalMapping.utf8).lexicographicallyPrecedes(Array($1.decomposedStringWithCanonicalMapping.utf8))}]]}
 throw Invalid.value
}
func configuration(_ v:Any)throws->[String:Any] {
 let f=try dict(v),title=try text(f,"title");guard let selection=f["selectionBehavior"] else{throw Invalid.value};let normalized=try behavior(selection)
 guard let values=f["variants"] as? [Any] else{throw Invalid.value};let variants=try values.map(variant)
 var children=[String:Any]()
 if let value=f["childVariantConfigurations"] {let fields=try dict(value);for (key,value) in fields {children[key]=try configuration(value)}}
 return ["title":title,"selectionBehavior":normalized,"variants":variants,"childVariantConfigurations":children]
}
func order(_ a:String,_ b:String)->Bool {Array(a.decomposedStringWithCanonicalMapping.utf8).lexicographicallyPrecedes(Array(b.decomposedStringWithCanonicalMapping.utf8))}
func selected(_ f:[String:Any])->Set<String> {
 let behavior=f["selectionBehavior"] as! [String:Any];let initial:Set<String>
 if behavior["discriminant"] as! String=="singleSelect" {initial=[(behavior["singleSelectConfiguration"] as! [String:Any])["defaultVariant"] as! String]}
 else {initial=Set((behavior["multiSelectConfiguration"] as! [String:Any])["defaultVariants"] as! [String])}
 var result=initial;let children=f["childVariantConfigurations"] as! [String:Any]
 // Portable ordering policy. Actual native getter iterates the initial Set.
 for id in initial.sorted(by:order) {if let child=children[id] as? [String:Any] {result.formUnion(selected(child))}}
 return result
}
func single(_ id:String,_ children:[String:Any]=[:],_ style:String="list")->[String:Any] {["title":"Node","selectionBehavior":["discriminant":"singleSelect","singleSelectConfiguration":["style":style,"defaultVariant":id]],"variants":[] as [Any],"childVariantConfigurations":children]}
func multi(_ ids:[String],_ children:[String:Any]=[:])->[String:Any] {["title":"Node","selectionBehavior":["discriminant":"multiSelect","multiSelectConfiguration":["defaultVariants":ids]],"variants":[] as [Any],"childVariantConfigurations":children]}
let cases:[(String,Any)] = [
 ("single",single("a")),("range",single("a",[:],"range")),("empty-id",single("")),("unknown-id",single("missing")),
 ("multi-empty",multi([])),("multi",multi(["b","a","b"])),("canonical-defaults",multi(["e\u{301}","é"])),
 ("selected-child",single("a",["a":single("b")])),("unselected-child",single("a",["z":single("ignored")])),
 ("empty-multi-no-child",multi([],["a":single("ignored")])),
 ("no-sibling-cascade",single("a",["a":single("b"),"b":single("must-not-appear")])),
 ("nested-child-cascade",single("a",["a":single("b",["b":single("c")]),"b":single("must-not-appear")])),
 ("selected-two",multi(["b","a"],["a":single("x"),"b":single("y"),"z":single("ignored")])),
 ("canonical-child-lookup",single("e\u{301}",["é":single("leaf")])),
 ("parent-spelling-wins",multi(["a","e\u{301}"],["a":single("é")])),
 ("sibling-spelling-policy",multi(["b","a"],["a":single("e\u{301}"),"b":single("é")])),
 ("empty-key-child",single("",["":single("leaf")])),
 ("child-default-empty",single("a",["a":multi([])])),
 ("long",single(String(repeating:"é👩‍💻",count:300))),
 ("many",multi((0..<20).map{"id\($0)"})),
 ("bad-root",false),("missing-title",[: ] as [String:Any]),
 ("bad-selected-behavior",["title":"Node","selectionBehavior":["discriminant":"bad"],"variants":[] as [Any]]),
 ("invalid-unselected-child-still-decode-error",single("a",["z":false])),
]
var rows=[[String:Any]]()
for (name,input) in cases {var row:[String:Any]=["name":name,"kind":"default-selection","input":input,"accepted":false];do{let normalized=try configuration(input);row["output"]=selected(normalized).sorted(by:order);row["accepted"]=true}catch{};rows.append(row)}
try PropertyListSerialization.data(fromPropertyList:rows,format:.binary,options:0).write(to:URL(fileURLWithPath:CommandLine.arguments[1]))
print("24 original Foundation/default-set compositions;20 accepts;4 rejects;portable sibling ordering;no private getter")
