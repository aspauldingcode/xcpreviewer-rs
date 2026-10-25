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
let single:[String:Any]=["discriminant":"singleSelect","singleSelectConfiguration":["style":"list","defaultVariant":"unknown"]]
let multi:[String:Any]=["discriminant":"multiSelect","multiSelectConfiguration":["defaultVariants":["é","e\u{301}","a"]]]
let bare:[String:Any]=["title":"Root","selectionBehavior":single,"variants":[] as [Any]]
func modified(_ f:[String:Any],_ key:String,_ value:Any)->[String:Any]{var f=f;f[key]=value;return f}
func missing(_ f:[String:Any],_ key:String)->[String:Any]{var f=f;f.removeValue(forKey:key);return f}
let legacy:[String:Any]=["id":"v","displayName":"Variant","renderEffect":["id":"legacy"]]
let child=modified(bare,"title","Child")
let nested=modified(bare,"childVariantConfigurations",["id":modified(child,"childVariantConfigurations",["nested":bare])])
if CommandLine.arguments.count==4 && CommandLine.arguments[1]=="--tree" {
 let input=try PropertyListSerialization.propertyList(from:Data(contentsOf:URL(fileURLWithPath:CommandLine.arguments[2])),options:[],format:nil)
 let out=try configuration(input)
 try PropertyListSerialization.data(fromPropertyList:out,format:.binary,options:0).write(to:URL(fileURLWithPath:CommandLine.arguments[3]));exit(0)
}
let cases:[(String,Any)] = [
 ("bare-default-child",bare),
 ("empty-title",modified(bare,"title","")),
 ("explicit-empty-children",modified(bare,"childVariantConfigurations",[: ] as [String:Any])),
 ("one-child",modified(bare,"childVariantConfigurations",["id":child])),
 ("grandchild",nested),
 ("multi",modified(bare,"selectionBehavior",multi)),
 ("ordered-duplicate-variants",modified(bare,"variants",[legacy,legacy])),
 ("unicode-child-key",modified(bare,"childVariantConfigurations",["e\u{301}":child,"Ａ":bare,"A":bare])),
 ("unknown-omitted",modified(bare,"extra",true)),
 ("legacy",modified(bare,"variants",[legacy])),
 ("long",modified(modified(bare,"title",String(repeating:"é👩‍💻",count:300)),"childVariantConfigurations",[String(repeating:"🦀",count:300):child])),
 ("many",modified(modified(bare,"variants",Array(repeating:legacy,count:6)),"childVariantConfigurations",Dictionary(uniqueKeysWithValues:(0..<6).map{("id\($0)",child)}))),
 ("empty-key",modified(bare,"childVariantConfigurations",["":child])),
 ("missing-title",missing(bare,"title")),
 ("bad-title",modified(bare,"title",false)),
 ("missing-selection",missing(bare,"selectionBehavior")),
 ("bad-selection",modified(bare,"selectionBehavior",false)),
 ("unknown-selection",modified(bare,"selectionBehavior",["discriminant":"unknown"])),
 ("missing-variants",missing(bare,"variants")),
 ("bad-variants",modified(bare,"variants",false)),
 ("bad-variant-element",modified(bare,"variants",[legacy,1])),
 ("bad-children",modified(bare,"childVariantConfigurations",false)),
 ("array-children",modified(bare,"childVariantConfigurations",[child])),
 ("bad-child",modified(bare,"childVariantConfigurations",["id":false])),
 ("missing-child-title",modified(bare,"childVariantConfigurations",["id":missing(child,"title")])),
 ("deep-bad-variant",modified(bare,"childVariantConfigurations",["id":modified(child,"childVariantConfigurations",["deep":modified(bare,"variants",[false])])])),
 ("bad-selected-branch",modified(bare,"selectionBehavior",["discriminant":"singleSelect","singleSelectConfiguration":["style":"bad","defaultVariant":"id"]])),
 ("bad-modern-no-legacy-retry",modified(bare,"variants",[modified(legacy,"renderEffects",false)])),
]
var rows=[[String:Any]]()
for (name,input) in cases {var row:[String:Any]=["name":name,"kind":"overrides-configuration","input":input,"accepted":false];do{row["output"]=try configuration(input);row["accepted"]=true}catch{};rows.append(row)}
try PropertyListSerialization.data(fromPropertyList:rows,format:.binary,options:0).write(to:URL(fileURLWithPath:CommandLine.arguments[1]))
print("28 public Foundation compositions;13 accepts;15 rejects;no private decoder")
