import Foundation
import CoreFoundation
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
func section(_ v:Any)throws->[String:Any] {let f=try dict(v);var out=[String:Any]();if f["title"] != nil {out["title"]=try text(f,"title")};guard let values=f["variants"] as? [Any] else{throw Invalid.value};out["variants"]=try values.map(variant);return out}
func grid(_ v:Any)throws->[String:Any] {let f=try dict(v),title=try text(f,"title");guard let sections=f["sections"] as? [Any] else{throw Invalid.value};return ["title":title,"sections":try sections.map(section)]}
func group(_ v:Any)throws->[String:Any] {
 let f=try dict(v),id=try text(f,"id");var ids=[String]()
 if let v=f["associatedGroupIDsArray"] {guard let a=v as? [String] else{throw Invalid.value};ids=a}
 var out:[String:Any]=["id":id,"associatedGroupIDsArray":Array(Set(ids)).sorted{Array($0.decomposedStringWithCanonicalMapping.utf8).lexicographicallyPrecedes(Array($1.decomposedStringWithCanonicalMapping.utf8))}]
 if let v=f["overridesConfiguration"] {out["overridesConfiguration"]=try configuration(v)}
 if let v=f["variantsConfiguration"] {out["variantsConfiguration"]=try grid(v)}
 return out
}
func reply(_ v:Any)throws->[String:Any] {let f=try dict(v);guard let groups=f["groups"] as? [Any] else{throw Invalid.value};return ["groups":try groups.map(group)]}


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


func update(_ input:Any)throws->[String:Any] {
 let f=try dict(input);guard let raw=f["configuration"] else{throw Invalid.value};let config=try configuration(raw)
 guard let enabled=f["isEnabled"] as? NSNumber,CFGetTypeID(enabled)==CFBooleanGetTypeID(),let old=f["selection"] as? [String],let wanted=f["requestedSelection"] as? [String] else{throw Invalid.value}
 let current=Set(old),requested=Set(wanted);let children=config["childVariantConfigurations"] as! [String:Any]
 var childRows=[[String:Any]](),defaults=Set<String>()
 for v in config["variants"] as! [[String:Any]] {let id=v["id"] as! String;if requested.contains(id),let child=children[id] as? [String:Any] {childRows.append(child);defaults.formUnion(selected(child))}}
 var next=requested;next.formUnion(defaults);let changed=next != current
 return ["isEnabled":enabled.boolValue,"selectionChanged":changed,"selection":(changed ? next:current).sorted(by:order),"childConfigurations":childRows]
}
func v(_ id:String)->[String:Any]{["id":id,"displayName":id,"renderEffects":[] as [Any]]}
func config(_ variants:[String],_ children:[String:Any]=[:])->[String:Any] {var c=single("unused-root-default",children);c["variants"]=variants.map(v);return c}
func input(_ config:[String:Any],_ requested:[String],_ current:[String]=[],_ enabled:Bool=true)->[String:Any] {["configuration":config,"requestedSelection":requested,"selection":current,"isEnabled":enabled]}
let cases:[(String,Any)]=[
 ("empty",input(config([]),[])),
 ("own-default-ignored",input(config([]),["unknown"])),
 ("disabled-stays-disabled",input(config(["a"],["a":single("child")]),["a"],[],false)),
 ("selected-root-child",input(config(["a"],["a":single("child")]),["a"])),
 ("unselected-root",input(config(["a"],["a":single("child")]),[])),
 ("orphan-child",input(config([],["a":single("child")]),["a"])),
 ("source-order",input(config(["b","a"],["a":single("A"),"b":single("B")]),["a","b"])),
 ("duplicate-root",input(config(["a","a"],["a":single("child")]),["a"])),
 ("recursive-defaults",input(config(["a"],["a":single("b",["b":single("grand")])]),["a"])),
 ("no-root-cascade",input(config(["a","b"],["a":single("b"),"b":single("ignored")]),["a"])),
 ("replace-old-selection",input(config([]),[],["old-child"])),
 ("unknown-request-kept",input(config(["a"],["a":single("child")]),["a","unknown",""])),
 ("same-membership-rebuild",input(config(["a"],["a":single("child")]),["a"],["child","a"])),
 ("equal-keeps-old-spelling",input(config([]),["é"],["e\u{301}"])),
 ("canonical-parent-match",input(config(["é"],["e\u{301}":single("child")]),["é"])),
 ("empty-child-default",input(config(["a"],["a":multi([])]),["a"])),
 ("child-default-not-in-variants",input(config(["a"],["a":single("not-a-child-variant")]),["a"])),
 ("case-sensitive",input(config(["A"],["A":single("ignored")]),["a"])),
 ("requested-spelling-wins-on-change",input(config(["a"],["a":single("é")]),["a","e\u{301}"])),
 ("long-many",input(config((0..<6).map{"p\($0)"},Dictionary(uniqueKeysWithValues:(0..<6).map{("p\($0)",single(String(repeating:"é👩‍💻\n",count:300)))})),(0..<6).map{"p\($0)"}+(0..<12).map{"unknown\($0)"})),
 ("missing-config",["isEnabled":true,"selection":[],"requestedSelection":[]] as [String:Any]),
 ("bad-config",["configuration":false,"isEnabled":true,"selection":[],"requestedSelection":[]] as [String:Any]),
 ("bad-enabled",["configuration":config([]),"isEnabled":1,"selection":[],"requestedSelection":[]] as [String:Any]),
 ("bad-current",["configuration":config([]),"isEnabled":true,"selection":[false],"requestedSelection":[]] as [String:Any]),
 ("bad-request",["configuration":config([]),"isEnabled":true,"selection":[],"requestedSelection":[false]] as [String:Any]),
 ("malformed-unselected-child",input(config([],["orphan":false]),[]))
]
var result=[[String:Any]]()
for (name,input) in cases {var row:[String:Any]=["name":name,"kind":"update-multi-selection","input":input,"accepted":false];do{row["output"]=try update(input);row["accepted"]=true}catch{};result.append(row)}
try PropertyListSerialization.data(fromPropertyList:result,format:.binary,options:0).write(to:URL(fileURLWithPath:CommandLine.arguments[1]))
print("26 original public Swift/Foundation compositions;20 accepts;6 rejects;portable default order;no private SwiftUI binding setter")
