import Foundation
// Original public Foundation casts and keyed access; no private framework import.
enum Invalid:Error {case value}
func box(_ input:Any)throws->[String:Any] {guard let d=input as? [String:Any] else {throw Invalid.value};return d}
func output(_ input:Any,_ kind:String)throws->Any {
 if kind=="control-state-boxes" {guard let values=input as? [Any] else {throw Invalid.value};return try values.map(box)}
 let fields=try box(input)
 if kind=="plist-box" {return fields}
 guard let value=fields["value"] else {if kind=="unbox-optional-string" {return ["isPresent":false]};throw Invalid.value}
 guard let string=value as? String else {throw Invalid.value}
 return ["isPresent":true,"value":string]
}
var cases=[(String,String,Any)]()
let payloads:[[String:Any]]=[[:],["unknown":false],["value":true],["value":17],["value":Data([0,255])],["value":["nested":[false,"v"]]],["value":Date(timeIntervalSinceReferenceDate:0.125)],["value":""],["value":"é"],["value":"s","other":["kept",false]]]
for (i,payload) in payloads.enumerated() {cases.append(("box-\(i)","plist-box",payload))}
for (i,payload) in ([false,[] as [Any],"wrong"] as [Any]).enumerated() {cases.append(("bad-root-\(i)","plist-box",payload))}
cases += [("empty-array","control-state-boxes",[] as [Any]),("duplicate-boxes","control-state-boxes",[payloads[0],payloads[4],payloads[4]]),("bad-late-box","control-state-boxes",[payloads[0],false] as [Any]),("many-boxes","control-state-boxes",Array(repeating:payloads[9],count:12))]
let values:[[String:Any]]=[[:],["value":""],["value":String(repeating:"é👩‍💻\n",count:300),"unknown":false],["value":false],["value":17],["value":[:] as [String:Any]]]
for kind in ["unbox-string","unbox-optional-string"] {for (i,value) in values.enumerated() {cases.append(("\(kind)-\(i)",kind,value))}}
var rows=[[String:Any]]()
for (name,kind,input) in cases {var row:[String:Any]=["name":name,"kind":kind,"input":input,"accepted":false];do{row["output"]=try output(input,kind);row["accepted"]=true}catch{};rows.append(row)}
try PropertyListSerialization.data(fromPropertyList:rows,format:.binary,options:0).write(to:URL(fileURLWithPath:CommandLine.arguments[1]))
print("29 original public Foundation compositions;18 accepts;11 rejects;no private box codec/getter")
