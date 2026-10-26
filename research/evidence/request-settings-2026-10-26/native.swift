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

func boolean(_ f:[String:Any],_ key:String)throws->Bool {guard let n=f[key] as? NSNumber,CFGetTypeID(n)==CFBooleanGetTypeID() else {throw Invalid.value};return n.boolValue}
func projections(_ value:Any)throws->[[String:Any]] {
 var f=try dict(value);let mode=try dict(f["mode"] as Any),tag=try text(mode,"discriminant")
 var canvas:[String:Any]?=nil;var location="inCanvas"
 switch tag {
 case "live":location=try text(mode,"hostLocation");guard ["inCanvas","external"].contains(location) else {throw Invalid.value}
 case "grid":canvas=try group(mode["group"] as Any)
 case "static":break
 default:throw Invalid.value
 }
 let caps=try dict(f["capabilities"] as Any),continuous=try boolean(caps,"supportsContinuousLivePreview"),statics=try boolean(caps,"supportsStaticPreviews")
 f.removeValue(forKey:"gridGroupID");if let canvas=canvas {f["gridGroupID"]=canvas["id"]}
 let all=try effective(f).flatMap{$0["overrides"] as! [[String:Any]]}
 func item(_ display:[String:Any],_ overrides:[[String:Any]],_ variant:[String:Any]?=nil)->[String:Any] {var d:[String:Any]=["displayMode":display,"overrides":overrides];if let variant=variant {d["variant"]=variant};return d}
 let staticMode:[String:Any]=["discriminant":"static"]
 var result=[[String:Any]]()
 if tag=="live" || continuous {result.append(item(["discriminant":"interactive","value":tag != "live" || location != "external"],all))}
 if !statics {return result}
 if tag=="static" || result.isEmpty {result.append(item(staticMode,all))}
 if let canvas=canvas {
  f["gridGroup"]=canvas;let overrides=try gridOverrides(f)
  if let config=canvas["variantsConfiguration"] as? [String:Any] {for section in config["sections"] as! [[String:Any]] {for variant in section["variants"] as! [[String:Any]] {result.append(item(staticMode,overrides,variant))}}}
 }
 return result
}
func canvas(_ variants:[String]=["x","y","x"])->[String:Any] {
 var d=linked("canvas",["b"])
 d["variantsConfiguration"]=["title":"Grid","sections":[["variants":Array(variants.prefix(1)).map(v)],["title":"Other","variants":Array(variants.dropFirst()).map(v)]]]
 return d
}
func request(_ mode:[String:Any],_ continuous:Bool=true,_ statics:Bool=true,_ groups:[[String:Any]]=[linked("a",["canvas"]),g("b"),g("c"),g("c"),g("canvas")],_ states:[[String:Any]]=[st("a"),st("b"),st("c"),st("canvas")])->[String:Any] {
 var d=input(groups,states);d["mode"]=mode;d["capabilities"]=["supportsContinuousLivePreview":continuous,"supportsStaticPreviews":statics];return d
}
let modes:[[String:Any]]=[["discriminant":"live","hostLocation":"inCanvas"],["discriminant":"live","hostLocation":"external"],["discriminant":"static"],["discriminant":"grid","group":canvas()]]
var cases=[(String,Any)]()
for (i,mode) in modes.enumerated() {for continuous in [false,true] {for statics in [false,true] {cases.append(("matrix-\(i)-\(continuous)-\(statics)",request(mode,continuous,statics)))}}}
cases += [
 ("empty-grid-no-interactive",request(["discriminant":"grid","group":canvas([])],false,true)),
 ("empty-grid-interactive",request(["discriminant":"grid","group":canvas([])],true,true)),
 ("missing-grid-config",request(["discriminant":"grid","group":linked("canvas",[])],false,true)),
 ("empty-groups-grid",request(modes[3],false,true,[],[])),
 ("live-missing-state",request(modes[0],false,false,[g()],[])),
 ("static-no-config",request(modes[2],true,true,[g("g",nil)],[st()])),
 ("child-order",request(modes[3],true,true,[g("g",nested)],[st("g",true,["a","child","grandchild","sibling"])])),
 ("payload-not-looked-up",request(["discriminant":"grid","group":canvas(["x"])],true,true,[linked("canvas",["g"]),g()],[st("canvas"),st()])),
 ("canonical-associations",request(["discriminant":"grid","group":linked("é",["A\u{30a}"])],false,true,[linked("g",["e\u{301}"]),g("Å"),g("other")],[st(),st("A\u{30a}"),st("other")])),
 ("disabled",request(modes[3],false,true,[g()],[st("g",false)])),
 ("inactive-mode-payloads",request(["discriminant":"static","hostLocation":false,"group":false],true,true)),
 ("long-many",request(["discriminant":"grid","group":canvas([String(repeating:"é👩‍💻\n",count:300)]+(0..<12).map{"v\($0)"})],true,true))
]
var missingMode=request(modes[0]);missingMode.removeValue(forKey:"mode")
var missingCaps=request(modes[0]);missingCaps.removeValue(forKey:"capabilities")
var badBool=request(modes[0]);badBool["capabilities"]=["supportsContinuousLivePreview":1,"supportsStaticPreviews":true]
cases += [
 ("missing-mode",missingMode),("missing-capabilities",missingCaps),("numeric-bool",badBool),
 ("unknown-mode",request(["discriminant":"unknown"])),
 ("unknown-location",request(["discriminant":"live","hostLocation":"elsewhere"])),
 ("missing-grid-group",request(["discriminant":"grid"])),
 ("malformed-grid-even-no-static",request(["discriminant":"grid","group":["id":"canvas","variantsConfiguration":false]],false,false)),
 ("malformed-disabled",request(modes[2],false,false,[["id":"g","overridesConfiguration":false]],[st("g",false)]))
]

func configured(_ value:Any)throws->[[String:Any]] {
 let f=try dict(value)
 // Validate every active projection input even when admission is disabled.
 let raw=try projections(value)
 func settings(_ value:Any)throws->(Bool,[Any]) {let d=try dict(value),enabled=try boolean(d,"isEnabled");guard let states=d["boxedCanvasControlStates"] as? [Any] else {throw Invalid.value};return (enabled,states)}
 let defaults=try settings(f["defaultPreviewSettings"] as Any)
 let selected=try f["previewSettings"].map(settings) ?? defaults
 if !selected.0 {return []}
 return raw.map { entry in var row=entry;row["controlState"]=selected.1;return row }
}
let opaque:[Any]=["opaque",true,17,Data([0,255]),["nested":[false,"state"]],"opaque"]
func settings(_ enabled:Bool,_ states:[Any]=[])->[String:Any]{["isEnabled":enabled,"boxedCanvasControlStates":states]}
var configuredCases=cases.map { name,value -> (String,Any) in var d=value as! [String:Any];d["defaultPreviewSettings"]=settings(true,opaque);return (name,d) }
for enabled in [false,true] {for stored in [false,true] {var d=request(modes[3]);d["defaultPreviewSettings"]=settings(enabled,opaque);d["previewSettings"]=settings(stored,["stored","stored",false]);configuredCases.append(("precedence-\(enabled)-\(stored)",d))}}
var disabled=request(modes[3]);disabled["defaultPreviewSettings"]=settings(false,opaque)
var emptyStored=request(modes[3]);emptyStored["defaultPreviewSettings"]=settings(true,opaque);emptyStored["previewSettings"]=settings(true)
var badDefault=request(modes[0]);badDefault["defaultPreviewSettings"]=settings(true);badDefault["previewSettings"]=settings(true);badDefault["defaultPreviewSettings"]=["isEnabled":1,"boxedCanvasControlStates":[] as [Any]]
var badStored=request(modes[0]);badStored["defaultPreviewSettings"]=settings(false);badStored["previewSettings"]=["isEnabled":false,"boxedCanvasControlStates":false]
configuredCases += [("default-disabled",disabled),("empty-stored-wins",emptyStored),("invalid-unused-default",badDefault),("invalid-disabled-stored",badStored),("missing-default",request(modes[0]))]
var result=[[String:Any]]()
for (name,input) in configuredCases {var row:[String:Any]=["name":name,"kind":"configured-request-projections","input":input,"accepted":false];do{row["output"]=try configured(input);row["accepted"]=true}catch{};result.append(row)}
try PropertyListSerialization.data(fromPropertyList:result,format:.binary,options:0).write(to:URL(fileURLWithPath:CommandLine.arguments[1]))
print("45 original public Swift/Foundation compositions;34 accepts;11 rejects;no private request method/box codec")
