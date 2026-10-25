import Foundation
let root=URL(fileURLWithPath:CommandLine.arguments[1],isDirectory:true)
let entries:[(String,String?,String)]=[("a.txt",nil,"first"),("bad.txt","blocked","failed"),("a.txt",nil,"replacement 🪨\0"),("deep.txt","deep/sub","\\n\n%"),("bad2.txt","blocked","failed again")]
let cases:[[(String,String?,String)]]=[[],entries,[("bad.txt","blocked","failed first"),("empty.txt","","")]]
var records:[[String:Any]]=[]
for (caseIndex,items) in cases.enumerated(){let base=root.appendingPathComponent("case-\(caseIndex)",isDirectory:true);try FileManager.default.createDirectory(at:base,withIntermediateDirectories:true);try "file".write(to:base.appendingPathComponent("blocked"),atomically:true,encoding:.utf8)
 var inputs:[[String:Any]]=[];var outputs:[[String:Any]]=[];var failures:[[String:Any]]=[]
 for (index,entry) in items.enumerated(){let(name,folder,text)=entry;var input:[String:Any]=["name":name,"folder_present":folder != nil,"contents":text];if let folder=folder{input["folder"]=folder};inputs.append(input)
 var directory=base;var operations:[String]=[];var data=Data();var domain="";var code=0
 do {if let folder=folder{operations.append("directory");directory=directory.appendingPathComponent(folder,isDirectory:true);operations.append("create");try? FileManager.default.createDirectory(at:directory,withIntermediateDirectories:true)}
 operations.append("file");let destination=directory.appendingPathComponent(name);operations.append("write");try text.write(to:destination,atomically:true,encoding:.utf8);data=try Data(contentsOf:destination)
 }catch{let e=error as NSError;domain=e.domain;code=e.code;failures.append(["index":index,"domain":domain,"code":code])}
 outputs.append(["index":index,"operations":operations,"bytes":data,"error_domain":domain,"error_code":code])
 }
 records.append(["inputs":inputs,"outputs":outputs,"failures":failures,"attempted":items.count])
}
let data=try PropertyListSerialization.data(fromPropertyList:records,format:.binary,options:0);try data.write(to:URL(fileURLWithPath:CommandLine.arguments[2]))
let output=records.map{r -> [String:Any] in ["attempted":r["attempted"]!,"failures":r["failures"]!]};FileHandle.standardOutput.write(try JSONSerialization.data(withJSONObject:output,options:[.prettyPrinted,.sortedKeys]))
