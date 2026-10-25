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
let modern:[String:Any]=["id":"v","displayName":"Variant","renderEffects":[["id":"z"],["id":"a"],["id":"z"]]]
let legacy:[String:Any]=["id":"v","displayName":"Variant","renderEffect":["id":"legacy"]]
var cases:[(String,String,Any)]=[
 ("empty-modern","variant",["id":"v","displayName":"V","renderEffects":[]]),
 ("legacy","variant",legacy),
 ("modern-order","variant",modern.merging(["renderEffect":7]){_,new in new}),
 ("empty-wins","variant",["id":"v","displayName":"V","renderEffects":[],"renderEffect":7]),
 ("empty-strings","variant",["id":"","displayName":"","renderEffect":["id":""]]),
 ("unicode-controls","variant",["id":"🦀\n\0","displayName":"\r\t","renderEffect":["id":"future-effect"]]),
 ("unknown-orientation","variant",legacy.merging(["interfaceOrientationOverride":"future"]){_,new in new}),
 ("numeric-orientation","variant",legacy.merging(["interfaceOrientationOverride":1]){_,new in new}),
 ("invalid-modern-no-retry","variant",legacy.merging(["renderEffects":"bad"]){_,new in new}),
 ("invalid-element-no-retry","variant",legacy.merging(["renderEffects":[["id":"x"],7]]){_,new in new}),
 ("invalid-effect-id","variant",["id":"v","displayName":"V","renderEffects":[["id":1]]]),
 ("missing-effects","variant",["id":"v","displayName":"V"]),
 ("missing-id","variant",["displayName":"V","renderEffect":["id":"x"]]),
 ("missing-display","variant",["id":"v","renderEffect":["id":"x"]]),
 ("bad-display","variant",legacy.merging(["displayName":true]){_,new in new}),
 ("bad-legacy-id","variant",["id":"v","displayName":"V","renderEffect":["id":true]]),
 ("long-effects","variant",["id":"v","displayName":"V","renderEffects":Array(repeating:["id":"owned\n\0"],count:12)]),
 ("absent","override",[String:Any]()),
 ("empty","override",["contentOverride":""]),
 ("unknown","override",["contentOverride":"future-choice"]),
 ("controls","override",["contentOverride":"🦀\n\0"]),
 ("ignored-request-fields","override",["requestedOverrides":["not-an-applied-choice"]]),
 ("invalid-selected","override",["contentOverride":1]),
 ("invalid-selected-array","override",["contentOverride":["x"]]),
 ("invalid-root","override",7)
]
for raw in ["portrait","portraitUpsideDown","landscapeLeft","landscapeRight"]{cases.append((raw,"variant",legacy.merging(["interfaceOrientationOverride":raw]){_,new in new}))}
var rows=[[String:Any]]()
for(name,kind,input)in cases{var row:[String:Any]=["name":name,"kind":kind,"input":input,"accepted":false];do{row["output"]=try kind=="variant" ? variant(input):override(input);row["accepted"]=true}catch{};rows.append(row)}
let data=try PropertyListSerialization.data(fromPropertyList:rows,format:.binary,options:0)
try data.write(to:URL(fileURLWithPath:CommandLine.arguments[1]))
print("29 public Foundation compositions;16 accept/13 reject; no private decoder or effect application")
