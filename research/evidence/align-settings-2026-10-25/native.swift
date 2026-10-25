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


struct State {let enabled:Bool;let selection:Set<String>}
func keyLess(_ a:String,_ b:String)->Bool {Array(a.decomposedStringWithCanonicalMapping.utf8).lexicographicallyPrecedes(Array(b.decomposedStringWithCanonicalMapping.utf8))}
func aligned(_ input:Any)throws->[String:Any] {
 let f=try dict(input);guard let raw=f["groups"] as? [Any],let rows=f["settings"] as? [Any] else{throw Invalid.value}
 let groups=try raw.map(group);var settings=[String:State]()
 for value in rows {let d=try dict(value),id=try text(d,"groupID");guard let enabled=d["isEnabled"] as? NSNumber,CFGetTypeID(enabled)==CFBooleanGetTypeID(),let ids=d["selection"] as? [String] else{throw Invalid.value};settings[id]=State(enabled:enabled.boolValue,selection:Set(ids))}
 let grid:String?;if f["gridGroupID"] != nil {grid=try text(f,"gridGroupID")}else{grid=nil}
 let discovered=Set(groups.map{$0["id"] as! String});let clear=grid.map{!discovered.contains($0)} ?? false
 let before=settings.count
 // Original source-guided public Dictionary mutation, not private EditorSettings.
 for id in Array(settings.keys) {if !discovered.contains(id){settings.removeValue(forKey:id)}}
 let states=settings.keys.sorted(by:keyLess).map{id -> [String:Any] in let v=settings[id]!;return ["groupID":id,"isEnabled":v.enabled,"selection":Array(v.selection).sorted(by:keyLess)]}
 return ["clearStoredCanvasMode":clear,"removedSettings":before-settings.count,"settings":states]
}
func v(_ id:String)->[String:Any]{["id":id,"displayName":"V","renderEffects":[] as [Any]]}
let single:[String:Any]=["discriminant":"singleSelect","singleSelectConfiguration":["style":"list","defaultVariant":"default"]]
func g(_ id:String="g",_ config:Bool=true)->[String:Any]{var d:[String:Any]=["id":id,"associatedGroupIDsArray":["associated"]];if config{d["overridesConfiguration"]=["title":"C","selectionBehavior":single,"variants":[v("valid")]]};return d}
func st(_ id:String="g",_ enabled:Bool=true,_ ids:[String]=["stale"])->[String:Any]{["groupID":id,"isEnabled":enabled,"selection":ids]}
func input(_ groups:[[String:Any]],_ states:[[String:Any]],_ grid:String?=nil)->[String:Any]{var d:[String:Any]=["groups":groups,"settings":states];if let grid=grid{d["gridGroupID"]=grid};return d}
let cases:[(String,Any)]=[
 ("empty",input([],[])),("all-removed",input([],[st(),st("other")])),
 ("new-groups-no-defaults",input([g(),g("new")],[])),
 ("retain-disabled-and-stale-selection",input([g()],[st("g",false,["stale",""])])),
 ("retain-empty-selection",input([g()],[st("g",true,[])])),
 ("prune-only-group-ids",input([g()],[st(),st("unknown")])),
 ("no-override-config-still-retained",input([g("g",false)],[st()])),
 ("grid-present",input([g()],[st()],"g")),
 ("grid-missing",input([g()],[st()],"missing")),
 ("grid-missing-empty-groups",input([],[],"g")),
 ("canonical-grid",input([g("é")],[st("e\u{301}")],"e\u{301}")),
 ("canonical-selection-representative",input([g()],[st("g",true,["e\u{301}","é","A","Ａ"])])),
 ("settings-first-key-last-value",input([g("é")],[st("e\u{301}",false),st("é",true,["new"])])),
 ("duplicate-groups",input([g("g"),g("g")],[st()])),
 ("associations-do-not-retain-settings",input([g()],[st(),st("associated")])),
 ("case-sensitive",input([g("G")],[st("g")],"g")),
 ("long-many",input((0..<6).map{g("g\($0)")},(0..<6).map{st("g\($0)",false,[String(repeating:"é👩‍💻\n",count:300)]+(0..<12).map{"v\($0)"})})),
 ("empty-id",input([g("")],[st("")],"")),
 ("bad-group",input([["id":"g","overridesConfiguration":false]],[st()])),
 ("missing-groups",["settings":[] as [Any]]),("bad-settings",["groups":[] as [Any],"settings":false]),
 ("bad-enabled",input([g()],[["groupID":"g","isEnabled":"true","selection":[] as [String]]])),
 ("bad-selection",input([g()],[["groupID":"g","isEnabled":true,"selection":[false]]])),
 ("bad-grid",["groups":[] as [Any],"settings":[] as [Any],"gridGroupID":false])
]
var result=[[String:Any]]()
for (name,input) in cases {var row:[String:Any]=["name":name,"kind":"align-settings","input":input,"accepted":false];do{row["output"]=try aligned(input);row["accepted"]=true}catch{};result.append(row)}
try PropertyListSerialization.data(fromPropertyList:result,format:.binary,options:0).write(to:URL(fileURLWithPath:CommandLine.arguments[1]))
print("24 original public Swift/Foundation compositions;18 accepts;6 rejects;no private alignment method")
