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
func override(_ v:Any)throws->[String:Any]{let d=try dict(v);if d["contentOverride"] != nil{return ["contentOverride":try text(d,"contentOverride")]};return [:]}
func section(_ value:Any)throws->[String:Any]{
 let d=try dict(value);var out=[String:Any]()
 if d["title"] != nil{out["title"]=try text(d,"title")}
 guard let values=d["variants"] as? [Any] else{throw Invalid.value};out["variants"]=try values.map(variant);return out
}
func configuration(_ value:Any)throws->[String:Any]{
 let d=try dict(value);let title=try text(d,"title")
 guard let sections=d["sections"] as? [Any] else{throw Invalid.value};return ["title":title,"sections":try sections.map(section)]
}
let legacy:[String:Any]=["id":"v","displayName":"Variant","renderEffect":["id":"legacy"]]
let modern:[String:Any]=["id":"🦀\n\0","displayName":"V\r\t","renderEffects":[],"renderEffect":7]
let bare:[String:Any]=["variants":[legacy]]
let named:[String:Any]=["title":"section","variants":[modern,legacy,legacy]]
let long:[String:Any]=["title":String(repeating:"🦀",count:600),"variants":Array(repeating:legacy,count:6)]
let cases:[(String,String,Any)]=[
 ("empty","configuration",["title":"Grid","sections":[]]),
 ("empty-title","configuration",["title":"","sections":[]]),
 ("one-section","configuration",["title":"Grid","sections":[bare]]),
 ("ordered-duplicates","configuration",["title":"Grid","sections":[named,bare,named]]),
 ("bounded-summary","configuration",["title":"Grid","sections":Array(repeating:long,count:6)]),
 ("missing-title","configuration",["sections":[]]),
 ("invalid-title","configuration",["title":1,"sections":[]]),
 ("missing-sections","configuration",["title":"Grid"]),
 ("invalid-sections","configuration",["title":"Grid","sections":[:]]),
 ("invalid-section-element","configuration",["title":"Grid","sections":[bare,7]]),
 ("invalid-nested-variant","configuration",["title":"Grid","sections":[["variants":[legacy,7]]]]),
 ("invalid-optional-title","configuration",["title":"Grid","sections":[["title":1,"variants":[legacy]]]]),
 ("ignored-fields","configuration",["title":"Grid","sections":[bare],"unknown":true]),
 ("untitled-section","section",["variants":[]]),
 ("empty-section-title","section",["title":"","variants":[]]),
 ("unicode-section","section",["title":"🦀\n\0","variants":[modern]]),
 ("modern-empty-wins","section",["variants":[modern]]),
 ("section-duplicates","section",named),
 ("missing-variants","section",[String:Any]()),
 ("invalid-variants","section",["variants":"x"]),
 ("invalid-title-first","section",["title":true,"variants":[]]),
 ("invalid-variant","section",["variants":[7]]),
 ("missing-effects","section",["variants":[["id":"v","displayName":"V"]]]),
 ("invalid-section-root","section",7)
]
var rows=[[String:Any]]()
for(name,kind,input)in cases{var row:[String:Any]=["name":name,"kind":kind,"input":input,"accepted":false];do{row["output"]=try kind=="configuration" ? configuration(input):section(input);row["accepted"]=true}catch{};rows.append(row)}
let data=try PropertyListSerialization.data(fromPropertyList:rows,format:.binary,options:0)
try data.write(to:URL(fileURLWithPath:CommandLine.arguments[1]))
print("24 public Foundation compositions;11 accept/13 reject;no private decoder or selection")
