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

struct State {let enabled:Bool;let selection:Set<String>}
func rowSettings(_ input:Any)throws->[[String:Any]] {
 let f=try dict(input);guard let raw=f["groups"] as? [Any],let rows=f["settings"] as? [Any] else{throw Invalid.value}
 let groups=try raw.map(group);var settings=[String:State]()
 for value in rows {let d=try dict(value),id=try text(d,"groupID");guard let enabled=d["isEnabled"] as? NSNumber,CFGetTypeID(enabled)==CFBooleanGetTypeID(),let ids=d["selection"] as? [String] else{throw Invalid.value};settings[id]=State(enabled:enabled.boolValue,selection:Set(ids))}
 if f["gridGroupID"] != nil {_=try text(f,"gridGroupID")}
 return groups.map{g in let id=g["id"] as! String;let stored=settings[id];let value=stored ?? State(enabled:false,selection:(g["overridesConfiguration"] as? [String:Any]).map(selected) ?? []);return ["groupID":id,"isStored":stored != nil,"isEnabled":value.enabled,"selection":value.selection.sorted(by:order)]}
}
func g(_ id:String="g",_ config:[String:Any]?=single("default"))->[String:Any]{var d:[String:Any]=["id":id];if let config=config{d["overridesConfiguration"]=config};return d}
func st(_ id:String="g",_ enabled:Bool=true,_ ids:[String]=["stored"])->[String:Any]{["groupID":id,"isEnabled":enabled,"selection":ids]}
func input(_ groups:[[String:Any]],_ states:[[String:Any]],_ grid:String?=nil)->[String:Any]{var d:[String:Any]=["groups":groups,"settings":states];if let grid=grid{d["gridGroupID"]=grid};return d}
let cases:[(String,Any)]=[
 ("empty",input([],[])),("missing-without-config",input([g("g",nil)],[])),
 ("single-fallback",input([g()],[])),("multi-fallback",input([g("g",multi(["b","a","b"]))],[])),
 ("stored-enabled",input([g()],[st()])),("stored-disabled",input([g()],[st("g",false)])),
 ("stored-empty-not-default",input([g()],[st("g",true,[])])),("stored-stale-kept",input([g()],[st("g",false,["stale",""])])),
 ("stored-without-config",input([g("g",nil)],[st()])),("canonical-lookup",input([g("é")],[st("e\u{301}")])),
 ("stored-shadows-child-defaults",input([g("g",single("a",["a":single("child")]))],[st()])),
 ("ordered-duplicate-groups",input([g("b"),g("a"),g("b")],[])),
 ("recursive-defaults",input([g("g",single("a",["a":single("b",["b":single("c")])]))],[])),
 ("no-sibling-default-cascade",input([g("g",single("a",["a":single("b"),"b":single("ignored")]))],[])),
 ("sibling-spelling-policy",input([g("g",multi(["b","a"],["a":single("e\u{301}"),"b":single("é")]))],[])),
 ("grid-not-filtered",input([g()],[],"g")),
 ("long-many",input((0..<6).map{g("g\($0)",multi([String(repeating:"é👩‍💻\n",count:300)]+(0..<12).map{"v\($0)"}))},[])),
 ("case-sensitive",input([g("G")],[st("g")])),
 ("bad-group",input([["id":"g","overridesConfiguration":false]],[st()])),
 ("missing-groups",["settings":[] as [Any]]),("bad-settings",["groups":[] as [Any],"settings":false]),
 ("bad-enabled",input([g()],[["groupID":"g","isEnabled":"true","selection":[] as [String]]])),
 ("bad-selection",input([g()],[["groupID":"g","isEnabled":true,"selection":[false]]])),
 ("bad-grid",["groups":[] as [Any],"settings":[] as [Any],"gridGroupID":false])
]
var result=[[String:Any]]()
for (name,input) in cases {var row:[String:Any]=["name":name,"kind":"row-settings","input":input,"accepted":false];do{row["output"]=try rowSettings(input);row["accepted"]=true}catch{};result.append(row)}
try PropertyListSerialization.data(fromPropertyList:result,format:.binary,options:0).write(to:URL(fileURLWithPath:CommandLine.arguments[1]))
print("24 original public Swift/Foundation compositions;18 accepts;6 rejects;portable default order;no private SwiftUI binding getter")
