import Foundation
// Actual public Foundation operations, original composition; no private calls.
let cases: [(String,String,[String:Any])] = [
 ("category","variants",["contentCategory":"application"]),
 ("empty","variants",["contentCategory":"","contentOverride":""]),
 ("unknown","variants",["contentCategory":"future-category","contentOverride":"future-override"]),
 ("controls","variants",["contentCategory":"🦀\n\0","contentOverride":"\r\t"]),
 ("extra","variants",["contentCategory":"view","groups":[],"requestedOverrides":["ignored"]]),
 ("missing-category","variants",[:]),
 ("invalid-category","variants",["contentCategory":true]),
 ("invalid-override","variants",["contentCategory":"x","contentOverride":1]),
 ("array-override","variants",["contentCategory":"x","contentOverride":["x"]]),
 ("empty-array","contentOverride",["contentCategory":"application","requestedOverrides":[String]()]),
 ("ordered-duplicates","contentOverride",["contentCategory":"unknown","requestedOverrides":["z","a","z",""]]),
 ("unicode-array","contentOverride",["contentCategory":"x","requestedOverrides":["🦀","\n\0"]]),
 ("long-array","contentOverride",["contentCategory":"x","requestedOverrides":Array(repeating:"owned",count:12)]),
 ("empty-category","contentOverride",["contentCategory":"","requestedOverrides":[""]]),
 ("missing-array","contentOverride",["contentCategory":"x"]),
 ("wrong-array","contentOverride",["contentCategory":"x","requestedOverrides":"x"]),
 ("mixed-array","contentOverride",["contentCategory":"x","requestedOverrides":["x",1]]),
 ("bad-array-category","contentOverride",["contentCategory":false,"requestedOverrides":[]]),
 ("missing-array-category","contentOverride",["requestedOverrides":[]]),
 ("reply-groups-not-request","variants",["groups":[]]),
 ("single-override-not-array","contentOverride",["contentCategory":"x","contentOverride":"x"])
]
var rows = [[String:Any]]()
for (name,kind,input) in cases {
    var row: [String:Any] = ["name":name,"kind":kind,"input":input,"accepted":false]
    if let category=input["contentCategory"] as? String {
        var output: [String:Any] = ["contentCategory":category]
        if kind=="variants" {
            if input["contentOverride"] == nil { row["accepted"]=true;row["output"]=output }
            else if let value=input["contentOverride"] as? String { output["contentOverride"]=value;row["accepted"]=true;row["output"]=output }
        } else if let values=input["requestedOverrides"] as? [String] {
            output["requestedOverrides"]=values;row["accepted"]=true;row["output"]=output
        }
    }
    rows.append(row)
}
let data=try PropertyListSerialization.data(fromPropertyList:rows,format:.binary,options:0)
try data.write(to:URL(fileURLWithPath:CommandLine.arguments[1]))
print("21 public Foundation controls;10 accept/11 reject; no discovery or override action")
