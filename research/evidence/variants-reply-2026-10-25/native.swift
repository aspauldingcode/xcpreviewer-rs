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
let minimal:[String:Any]=["id":"g"]
let single:[String:Any]=["discriminant":"singleSelect","singleSelectConfiguration":["style":"list","defaultVariant":"unknown"]]
let tree:[String:Any]=["title":"Overrides","selectionBehavior":single,"variants":[] as [Any],"childVariantConfigurations":["id":["title":"Child","selectionBehavior":single,"variants":[] as [Any]]]]
let legacy:[String:Any]=["id":"v","displayName":"Variant","renderEffect":["id":"legacy"]]
let layout:[String:Any]=["title":"Grid","sections":[["variants":[legacy,legacy]],["title":"","variants":[] as [Any]]]]
func change(_ f:[String:Any],_ k:String,_ v:Any)->[String:Any]{var f=f;f[k]=v;return f}
let full=change(change(minimal,"overridesConfiguration",tree),"variantsConfiguration",layout)
let cases:[(String,String,Any)] = [
 ("minimal","group",minimal),
 ("empty-id","group",["id":""]),
 ("unknown-id","group",["id":"unknown"]),
 ("empty-associations","group",change(minimal,"associatedGroupIDsArray",[] as [String])),
 ("unicode-duplicates","group",change(minimal,"associatedGroupIDsArray",["e\u{301}","é","g","missing","g"])),
 ("wrong-key-ignored","group",change(minimal,"associatedGroupIDs",true)),
 ("override-only","group",change(minimal,"overridesConfiguration",tree)),
 ("grid-only","group",change(minimal,"variantsConfiguration",layout)),
 ("both","group",full),
 ("unknown-fields","group",change(full,"extra",false)),
 ("long-id","group",change(minimal,"id",String(repeating:"é👩‍💻",count:300))),
 ("many-associations","group",change(minimal,"associatedGroupIDsArray",(0..<12).map{"id\($0)"})),
 ("empty-reply","variants-reply",["groups":[] as [Any]]),
 ("one","variants-reply",["groups":[minimal]]),
 ("ordered-duplicates","variants-reply",["groups":[full,minimal,full]]),
 ("many-groups","variants-reply",["groups":Array(repeating:full,count:6)]),
 ("missing-id","group",[: ] as [String:Any]),
 ("bad-id","group",["id":1]),
 ("bad-associations","group",change(minimal,"associatedGroupIDsArray",false)),
 ("bad-association-element","group",change(minimal,"associatedGroupIDsArray",["id",1])),
 ("bad-overrides","group",change(minimal,"overridesConfiguration",false)),
 ("bad-grid","group",change(minimal,"variantsConfiguration",false)),
 ("missing-override-title","group",change(minimal,"overridesConfiguration",[: ] as [String:Any])),
 ("bad-nested-child","group",change(minimal,"overridesConfiguration",change(tree,"childVariantConfigurations",["id":false]))),
 ("bad-grid-title","group",change(minimal,"variantsConfiguration",["title":false,"sections":[] as [Any]])),
 ("bad-section","group",change(minimal,"variantsConfiguration",["title":"Grid","sections":[false]])),
 ("missing-groups","variants-reply",[: ] as [String:Any]),
 ("bad-groups","variants-reply",["groups":false]),
 ("bad-group-element","variants-reply",["groups":[minimal,false]]),
 ("nested-failure","variants-reply",["groups":[minimal,change(minimal,"variantsConfiguration",false)]]),
 ("root","group",["id"]),
 ("reply-root","variants-reply",["groups"]),
]
var rows=[[String:Any]]()
for (name,kind,input) in cases {var row:[String:Any]=["name":name,"kind":kind,"input":input,"accepted":false];do{row["output"]=try kind=="group" ? group(input):reply(input);row["accepted"]=true}catch{};rows.append(row)}
try PropertyListSerialization.data(fromPropertyList:rows,format:.binary,options:0).write(to:URL(fileURLWithPath:CommandLine.arguments[1]))
print("32 public Foundation compositions;16 accepts;16 rejects;no private decoder")
