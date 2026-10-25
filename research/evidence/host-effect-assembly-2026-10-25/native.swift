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

func assemble(_ input:Any)throws->[[String:Any]] {
 let f=try dict(input);guard let input=f["overrides"] as? [Any] else {throw Invalid.value}
 let overrides=try input.map(variant);let selected=try f["variant"].map(variant)
 return overrides.flatMap{$0["renderEffects"] as! [[String:Any]]} + (selected?["renderEffects"] as? [[String:Any]] ?? [])
}
func v(_ effects:[String],_ id:String="same")->[String:Any] { ["id":id,"displayName":"Name","renderEffects":effects.map{["id":$0]}] }
let cases:[(String,Any)]=[
 ("empty",["overrides":[] as [Any]]),
 ("overrides-order",["overrides":[v(["a","b"]),v(["c","a"])] ]),
 ("selected-only",["overrides":[] as [Any],"variant":v(["v","v"])]),
 ("selected-last",["overrides":[v(["o","same"])],"variant":v(["same","v"])]),
 ("duplicate-variants",["overrides":[v(["a"]),v(["a"])] ]),
 ("canonical-spellings-retained",["overrides":[v(["e\u{301}","é"])],"variant":v(["é"])]),
 ("empty-effect-list",["overrides":[v([]),v(["b"]),v([])],"variant":v([])]),
 ("legacy",["overrides":[["id":"v","displayName":"V","renderEffect":["id":"legacy"]]],"variant":v(["last"])]),
 ("modern-wins",["overrides":[["id":"v","displayName":"V","renderEffects":[] as [Any],"renderEffect":["id":"ignored"]]]]),
 ("open-ids",["overrides":[v(["","Missing","unknown"])] ]),
 ("orientation-not-effect",["overrides":[["id":"v","displayName":"V","renderEffects":[] as [Any],"interfaceOrientationOverride":"landscapeRight"]]]),
 ("long",["overrides":[v([String(repeating:"é👩‍💻\n",count:300)])]]),
 ("many",["overrides":[v((0..<20).map{"e\($0)"})]]),
 ("unknown-fields",["overrides":[] as [Any],"ignored":false]),
 ("missing-overrides",[: ] as [String:Any]),
 ("bad-overrides",["overrides":false]),
 ("bad-variant",["overrides":[] as [Any],"variant":false]),
 ("bad-override-effect",["overrides":[["id":"v","displayName":"V","renderEffects":[false]]]])
]
var rows=[[String:Any]]()
for (name,input) in cases {var row:[String:Any]=["name":name,"kind":"render-effects","input":input,"accepted":false];do{row["output"]=try assemble(input);row["accepted"]=true}catch{};rows.append(row)}
try PropertyListSerialization.data(fromPropertyList:rows,format:.binary,options:0).write(to:URL(fileURLWithPath:CommandLine.arguments[1]))
print("18 original public Foundation compositions;14 accepts;4 rejects;no private update method")
