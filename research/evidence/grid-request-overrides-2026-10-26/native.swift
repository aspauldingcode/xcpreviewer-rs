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
func effective(_ input:Any)throws->[[String:Any]] {
 let f=try dict(input);guard let raw=f["groups"] as? [Any],let rows=f["settings"] as? [Any] else {throw Invalid.value}
 let groups=try raw.map(group);var settings=[String:State]()
 for value in rows {let d=try dict(value),id=try text(d,"groupID");guard let enabled=d["isEnabled"] as? NSNumber,CFGetTypeID(enabled)==CFBooleanGetTypeID(),let ids=d["selection"] as? [String] else{throw Invalid.value};settings[id]=State(enabled:enabled.boolValue,selection:Set(ids))}
 let grid:String?;if f["gridGroupID"] != nil {grid=try text(f,"gridGroupID")}else{grid=nil}
 var result=[[String:Any]]()
 for g in groups {
  let id=g["id"] as! String
  guard let state=settings[id],state.enabled,id != grid,let config=g["overridesConfiguration"] as? [String:Any] else {continue}
  var selected=(config["variants"] as! [[String:Any]]).filter{state.selection.contains($0["id"] as! String)}
  let initial=selected
  for v in initial {if let child=(config["childVariantConfigurations"] as! [String:Any])[v["id"] as! String] as? [String:Any] {selected += (child["variants"] as! [[String:Any]]).filter{state.selection.contains($0["id"] as! String)}}}
  result.append(["group":g,"overrides":selected])
 }
 return result
}
func v(_ id:String)->[String:Any]{["id":id,"displayName":"V","renderEffects":[["id":id]]]}
let single:[String:Any]=["discriminant":"singleSelect","singleSelectConfiguration":["style":"list","defaultVariant":"a"]]
func c(_ ids:[String],_ children:[String:Any]=[:])->[String:Any]{["title":"C","selectionBehavior":single,"variants":ids.map(v),"childVariantConfigurations":children]}
func g(_ id:String="g",_ config:[String:Any]?=c(["a","b"]))->[String:Any]{var d:[String:Any]=["id":id,"associatedGroupIDsArray":["associated"]];if let config=config{d["overridesConfiguration"]=config};return d}
func st(_ id:String="g",_ enabled:Bool=true,_ ids:[String]=["a"])->[String:Any]{["groupID":id,"isEnabled":enabled,"selection":ids]}
func input(_ groups:[[String:Any]],_ states:[[String:Any]],_ grid:String?=nil)->[String:Any]{var d:[String:Any]=["groups":groups,"settings":states];if let grid=grid{d["gridGroupID"]=grid};return d}
let nested=c(["a","a","b"],["a":c(["child","child","other"],["child":c(["grandchild"])]),"child":c(["sibling"]),"b":c(["second"])])

func gridOverrides(_ input:Any)throws->[[String:Any]] {
 var f=try dict(input)
 let canvas=try group(f["gridGroup"] as Any), gridID=canvas["id"] as! String
 f["gridGroupID"]=gridID
 let associated=Set(canvas["associatedGroupIDsArray"] as! [String])
 return try effective(f).filter { entry in
  let g=entry["group"] as! [String:Any]
  return !Set(g["associatedGroupIDsArray"] as! [String]).contains(gridID) && !associated.contains(g["id"] as! String)
 }.flatMap { $0["overrides"] as! [[String:Any]] }
}
func linked(_ id:String,_ ids:[String])->[String:Any]{var d=g(id);d["associatedGroupIDsArray"]=ids;return d}
func plan(_ groups:[[String:Any]],_ states:[[String:Any]],_ canvas:[String:Any])->[String:Any]{var d=input(groups,states);d["gridGroup"]=canvas;return d}
let baseCases:[(String,Any)]=[
 ("empty",input([],[])),("missing-settings",input([g()],[])),("disabled",input([g()],[st("g",false)])),
 ("no-config",input([g("g",nil)],[st()])),("empty-selected",input([g()],[st("g",true,[])])),
 ("direct-order",input([g("g",c(["b","a","a","unknown"]))],[st("g",true,["a","b"])])),
 ("default-not-used",input([g()],[st("g",true,["unresolved"])])),
 ("one-level-snapshot",input([g("g",nested)],[st("g",true,["a","child","grandchild","sibling","second"])])),
 ("both-parents",input([g("g",nested)],[st("g",true,["a","b","child","second"])])),
 ("child-without-parent",input([g("g",nested)],[st("g",true,["child"])])),
 ("grid-excludes-id",input([g("g"),g("other")],[st(),st("other")],"g")),
 ("grid-other-keeps",input([g()],[st()],"other")),
 ("canonical-group-id",input([g("é")],[st("e\u{301}")],"e\u{301}")),
 ("canonical-selection-child-key",input([g("g",c(["é"],["e\u{301}":c(["Å"])]))],[st("g",true,["e\u{301}","A\u{30a}"])])),
 ("settings-last-value",input([g("é")],[st("e\u{301}",false),st("é",true)])),
 ("groups-order-duplicates",input([g("b"),g("a"),g("b")],[st("a"),st("b")])),
 ("associations-ignored",input([g(),g("associated")],[st(),st("associated",false)])),
 ("long-many",input((0..<6).map{g("g\($0)",c([String(repeating:"é👩‍💻\n",count:300)]+(0..<12).map{"v\($0)"}))},(0..<6).map{st("g\($0)",true,[String(repeating:"é👩‍💻\n",count:300)]+(0..<12).map{"v\($0)"})})),
 ("malformed-excluded-group",input([["id":"g","overridesConfiguration":false]],[st("g",false)])),
 ("missing-groups",["settings":[] as [Any]]),("bad-settings",["groups":[] as [Any],"settings":false]),
 ("bad-enabled",input([g()],[["groupID":"g","isEnabled":"true","selection":[] as [String]]])),
 ("bad-selection",input([g()],[["groupID":"g","isEnabled":true,"selection":[false]]])),
 ("bad-grid",["groups":[] as [Any],"settings":[] as [Any],"gridGroupID":false])
]

var cases=baseCases.map { name,value -> (String,Any) in
 var d=value as! [String:Any]
 let id=(d["gridGroupID"] as? String) ?? "canvas"
 d["gridGroup"]=["id":id,"associatedGroupIDsArray":[] as [String]]
 if name=="bad-grid" {d["gridGroup"]=false}
 return (name,d)
}
cases += [
 ("outgoing",plan([linked("a",["canvas"]),g("b")],[st("a"),st("b")],linked("canvas",[]))),
 ("incoming",plan([g("a"),g("b")],[st("a"),st("b")],linked("canvas",["b"]))),
 ("both-directions",plan([linked("a",["canvas"]),g("b"),g("c"),g("c")],[st("a"),st("b"),st("c")],linked("canvas",["b"]))),
 ("canonical-outgoing",plan([linked("a",["e\u{301}"])],[st("a")],linked("é",[]))),
 ("canonical-incoming",plan([g("é")],[st("e\u{301}")],linked("canvas",["e\u{301}"]))),
 ("transitive-not-followed",plan([linked("a",["b"]),linked("b",["canvas"])],[st("a"),st("b")],linked("canvas",[]))),
 ("payload-not-looked-up",plan([linked("canvas",["a"]),g("a")],[st("canvas"),st("a")],linked("canvas",[]))),
 ("unknown-empty-case-distinct",plan([g(""),g("Canvas"),g("x")],[st(""),st("Canvas"),st("x")],linked("canvas",["unknown"])))
]
var result=[[String:Any]]()
for (name,input) in cases {var row:[String:Any]=["name":name,"kind":"grid-request-overrides","input":input,"accepted":false];do{row["output"]=try gridOverrides(input);row["accepted"]=true}catch{};result.append(row)}
try PropertyListSerialization.data(fromPropertyList:result,format:.binary,options:0).write(to:URL(fileURLWithPath:CommandLine.arguments[1]))
print("32 original public Set/String/Foundation compositions;26 accepts;6 rejects;no private previewRequests method")
