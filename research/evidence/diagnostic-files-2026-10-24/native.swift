import Foundation
let root=URL(fileURLWithPath:CommandLine.arguments[1],isDirectory:true)
try FileManager.default.createDirectory(at:root,withIntermediateDirectories:true)
let inputs:[(String,String?,String)]=[("a.txt",nil,""),("a.txt","","owned 🪨\0%\\n\n"),("a.txt","deep/sub","other"),("a.txt",nil,"replacement"),("a.txt","blocked","unwritten")]
try "file".write(to:root.appendingPathComponent("blocked"),atomically:true,encoding:.utf8)
var rows:[[String:Any]]=[]
for (name,folder,text) in inputs {
 var ops:[String]=[];var directory=root;var bytes=Data();var domain="";var code=0;var createDomain="";var createCode=0
 do {if let folder=folder {ops.append("directory");directory=directory.appendingPathComponent(folder,isDirectory:true);ops.append("create");do{try FileManager.default.createDirectory(at:directory,withIntermediateDirectories:true)}catch{let e=error as NSError;createDomain=e.domain;createCode=e.code}}
 ops.append("file");let destination=directory.appendingPathComponent(name)
 ops.append("write");try text.write(to:destination,atomically:true,encoding:.utf8);bytes=try Data(contentsOf:destination)
 }catch{let e=error as NSError;domain=e.domain;code=e.code}
 var row:[String:Any]=["name":name,"folder_present":folder != nil,"contents":text,"operations":ops,"bytes":bytes,"error_domain":domain,"error_code":code,"atomic":true,"create_error_domain":createDomain,"create_error_code":createCode];if let folder=folder{row["folder"]=folder};rows.append(row)
}
let data=try PropertyListSerialization.data(fromPropertyList:rows,format:.binary,options:0);try data.write(to:URL(fileURLWithPath:CommandLine.arguments[2]))
let json=rows.map{r -> [String:Any] in ["operations":r["operations"]!,"bytes":Array(r["bytes"] as! Data),"error_domain":r["error_domain"]!,"error_code":r["error_code"]!]}
let output=try JSONSerialization.data(withJSONObject:json,options:[.prettyPrinted,.sortedKeys]);FileHandle.standardOutput.write(output)
