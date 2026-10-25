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


if CommandLine.arguments.count>1 && CommandLine.arguments[1]=="--probe" {let selection:Set<String>=["a","b"];print(selection.first(where:{["a","b"].contains($0)})!);exit(0)}
func controls(_ input:Any)throws->[String:Any]{
 let f=try dict(input);guard let raw=f["group"] else{throw Invalid.value};let g=try group(raw),config=g["overridesConfiguration"] as? [String:Any]
 var enabled=false,ids=config.map(selected) ?? Set<String>(),stored=false
 if let value=f["settings"] {let d=try dict(value);guard let b=d["isEnabled"] as? NSNumber,CFGetTypeID(b)==CFBooleanGetTypeID(),let a=d["selection"] as? [String] else{throw Invalid.value};enabled=b.boolValue;ids=Set(a);stored=true}
 var write=false
 if let v=f["requestedEnabled"] {guard let b=v as? NSNumber,CFGetTypeID(b)==CFBooleanGetTypeID() else{throw Invalid.value};enabled=b.boolValue;stored=true;write=true}
 var out:[String:Any]=["isStored":stored,"isEnabled":enabled,"selection":ids.sorted(by:order),"enableWriteRequested":write,"singleSelectionAvailable":false]
 if let c=config {let defaults=selected(c);if !defaults.isEmpty {let roots=Set((c["variants"] as! [[String:Any]]).map{$0["id"] as! String});let matches=Set(ids.filter{roots.contains($0)}),fallback=matches.isEmpty;let candidates=(fallback ? defaults:matches).sorted(by:order);out["singleSelectionAvailable"]=true;out["usesDefaults"]=fallback;out["candidates"]=candidates;out["portableValue"]=candidates.first!}}
 return out
}
func v(_ id:String)->[String:Any]{["id":id,"displayName":id,"renderEffects":[] as [Any]]}
func config(_ variants:[String],_ children:[String:Any]=[:])->[String:Any] {var c=single("default",children);c["variants"]=variants.map(v);return c}
func input(_ config:[String:Any]?,_ ids:[String]?=nil,_ enabled:Bool=false,_ requested:Bool?=nil)->[String:Any]{var g:[String:Any]=["id":"g"];if let config=config{g["overridesConfiguration"]=config};var d:[String:Any]=["group":g];if let ids=ids{d["settings"]=["isEnabled":enabled,"selection":ids]};if let requested=requested{d["requestedEnabled"]=requested};return d}
let cases:[(String,Any)]=[
 ("missing-no-config",input(nil)),
 ("missing-defaults-read-only",input(config(["a"]))),
 ("equal-false-write-installs",input(config(["a"]),nil,false,false)),
 ("enable-missing",input(config(["a"]),nil,false,true)),
 ("disable-preserves-ids",input(config(["a"]),["a","unknown","child"],true,false)),
 ("same-true-write",input(config(["a"]),["a"],true,true)),
 ("selected-root",input(config(["a"]),["a"])),
 ("stored-child-only-falls-back",input(config(["a"],["a":config(["child"])]),["child"])),
 ("several-roots-ambiguous",input(config(["b","a"]),["b","a","stale"])),
 ("empty-defaults-even-stored-root",input(multi([]),["a"])),
 ("multi-defaults-available",input(multi(["b","a"]),[])),
 ("recursive-fallback-includes-child",input(single("a",["a":single("b")]),[])),
 ("stored-empty-gets-default",input(config(["a"]),[])),
 ("unknown-default-not-validated",input(config([]),["stale"])),
 ("canonical-match-stored-spelling",input(config(["é"]),["e\u{301}"])),
 ("range-style",input(single("fallback",[:],"range"),[])),
 ("toggle-without-config",input(nil,["stale"],false,true)),
 ("empty-id-available",input(single(""),[])),
 ("case-sensitive",input(config(["A"]),["a"])),
 ("long-many",input(config([String(repeating:"é👩‍💻\n",count:300)]+(0..<12).map{"v\($0)"}),[String(repeating:"é👩‍💻\n",count:300)]+(0..<12).map{"v\($0)"})),
 ("missing-group",["settings":false]),
 ("bad-group",["group":false]),
 ("bad-stored-bool",["group":["id":"g"],"settings":["isEnabled":1,"selection":[]]] as [String:Any]),
 ("bad-selection",["group":["id":"g"],"settings":["isEnabled":true,"selection":[false]]] as [String:Any]),
 ("bad-requested-enabled",["group":["id":"g"],"requestedEnabled":1] as [String:Any]),
 ("malformed-unselected-child",input(config([],["orphan":false])))
]
var result=[[String:Any]]()
for (name,input) in cases{var row:[String:Any]=["name":name,"kind":"row-controls","input":input,"accepted":false];do{row["output"]=try controls(input);row["accepted"]=true}catch{};result.append(row)}
try PropertyListSerialization.data(fromPropertyList:result,format:.binary,options:0).write(to:URL(fileURLWithPath:CommandLine.arguments[1]))
print("26 original public Swift/Foundation compositions;20 accepts;6 rejects;candidate eligibility/portable choice;no private SwiftUI binding")
