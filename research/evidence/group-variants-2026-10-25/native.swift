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

struct VariantKey: Hashable {
 let id:String;let name:String;let effects:[String];let orientation:String?
 init(_ d:[String:Any]) {id=d["id"] as! String;name=d["displayName"] as! String;effects=(d["renderEffects"] as! [[String:Any]]).map{$0["id"] as! String};orientation=d["interfaceOrientationOverride"] as? String}
}
func enumerate(_ input:Any)throws->[String:Any] {
 let g=try group(input),o=(g["overridesConfiguration"] as? [String:Any])?["variants"] as? [[String:Any]] ?? []
 let sections=(g["variantsConfiguration"] as? [String:Any])?["sections"] as? [[String:Any]] ?? []
 let grid=sections.flatMap{$0["variants"] as! [[String:Any]]}
 // Original reconstruction of the recovered first-insertion OrderedSet rule.
 // Public Swift Hashable/Set, not the private OrderedSet/getters.
 var seen=Set<VariantKey>();let all=(o+grid).filter{seen.insert(VariantKey($0)).inserted}
 return ["overrides":o,"grid":grid,"all":all]
}
func v(_ id:String="v",_ name:String="Name",_ effects:[String]=["a","b"],_ orientation:String?=nil)->[String:Any] {
 var d:[String:Any]=["id":id,"displayName":name,"renderEffects":effects.map{["id":$0]}];if let orientation=orientation{d["interfaceOrientationOverride"]=orientation};return d
}
let single:[String:Any]=["discriminant":"singleSelect","singleSelectConfiguration":["style":"list","defaultVariant":"missing"]]
func g(_ overrides:[[String:Any]],_ sections:[[[String:Any]]],_ child:Bool=false)->[String:Any] {
 var tree:[String:Any]=["title":"Overrides","selectionBehavior":single,"variants":overrides]
 if child {tree["childVariantConfigurations"]=["missing":["title":"Child","selectionBehavior":single,"variants":[v("child-only")]]]}
 return ["id":"group","overridesConfiguration":tree,"variantsConfiguration":["title":"Grid","sections":sections.map{["variants":$0]}]]
}
let cases:[(String,Any)]=[
 ("absent",["id":"g"]),("empty",g([],[])),
 ("ordered-duplicates",g([v("b"),v("a"),v("b")],[[v("c"),v("a")],[],[v("d"),v("c")]])),
 ("same-id-fields-differ",g([v()],[[v("v","Other"),v("v","Name",["b","a"]),v("v","Name",["a","a","b"]),v("v","Name",["a","b"],"portrait"),v()]])),
 ("canonical-all-strings",g([v("e\u{301}","A\u{30a}",["e\u{301}"])],[[v("é","Å",["é"])]])),
 ("compatibility-case-distinct",g([v("A"),v("Ａ")],[[v("a"),v("A")]])),
 ("child-excluded",g([],[],true)),
 ("legacy-modern-equal",g([["id":"v","displayName":"Name","renderEffect":["id":"a"]]],[[v("v","Name",["a"])]])),
 ("empty-effects",g([v("v","Name",[])],[[v("v","Name",[]),v("v","Name",["Missing"])]])),
 ("orientations",g([],[[v("v","Name",[],"portrait"),v("v","Name",[],"portraitUpsideDown"),v("v","Name",[],"landscapeLeft"),v("v","Name",[],"landscapeRight"),v("v","Name",[])]])),
 ("many-long",g((0..<12).map{v("id\($0)",String(repeating:"é👩‍💻\n",count:300))},[])),
 ("malformed-unselected-child",["id":"g","overridesConfiguration":["title":"O","selectionBehavior":single,"variants":[] as [Any],"childVariantConfigurations":["unused":false]]]),
 ("bad-grid",["id":"g","variantsConfiguration":false]),("missing-id",[: ] as [String:Any]),
 ("bad-effect",g([["id":"v","displayName":"N","renderEffects":[false]]],[])),
 ("bad-orientation",g([v("v","N",[],"unknown")],[]))
]
var rows=[[String:Any]]()
for (name,input) in cases {var row:[String:Any]=["name":name,"kind":"group-variants","input":input,"accepted":false];do{row["output"]=try enumerate(input);row["accepted"]=true}catch{};rows.append(row)}
try PropertyListSerialization.data(fromPropertyList:rows,format:.binary,options:0).write(to:URL(fileURLWithPath:CommandLine.arguments[1]))
print("16 original public Swift/Foundation compositions;11 accept;5 reject;no private getter")
