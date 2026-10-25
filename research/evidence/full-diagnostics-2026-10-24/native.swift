import Foundation
func report(_ node: [String:Any]) -> String {
 if let main=node["main"] as? [String:Any],let cause=node["underlying"] as? [String:Any] {
  return report(main)+"\n\n==================================\n\n"+report(cause).components(separatedBy:"\n").map{"|  "+$0}.joined(separator:"\n")
 }
 var text=node["errorTypeDescription"] as! String
 if let title=(node["highValueTitle"] as? String) ?? (node["lowValueTitle"] as? String) { text += ": "+title }
 for key in ["additionalInfo","additionalDiagnostics"] { if let s=node[key] as? String { text += "\n\n"+s } }
 return text.replacingOccurrences(of:"\\n",with:"\n",options:[],range:nil)
}
let leaves:[[String:Any]]=[
 ["errorType":"leaf","errorTypeDescription":""],
 ["errorType":"leaf","errorTypeDescription":"Type","highValueTitle":"","lowValueTitle":"ignored","additionalInfo":"","additionalDiagnostics":""],
 ["errorType":"leaf","errorTypeDescription":"T\\nX","lowValueTitle":"low 🪨","additionalInfo":"a\\nb\n","additionalDiagnostics":"\0%\\n\u{301}"],
 ["errorType":"leaf","errorTypeDescription":"\r\n\nend\n","additionalDiagnostics":"z\n\u{301}\r\n"],
 ["errorType":"leaf","errorTypeDescription":"\\\\n\\n n\\n\u{301}"],
]
func wrap(_ main:[String:Any],_ cause:[String:Any])->[String:Any]{["errorType":"wrapper","main":main,"underlying":cause]}
let inputs=leaves+[wrap(leaves[0],leaves[0]),wrap(leaves[1],leaves[2]),wrap(leaves[2],wrap(leaves[3],leaves[0])),wrap(wrap(leaves[0],leaves[1]),leaves[4])]
let records=inputs.map{n -> [String:Any] in let s=report(n);return ["archive":n,"result":s,"utf8":Data(s.utf8)]}
let data=try PropertyListSerialization.data(fromPropertyList:records,format:.binary,options:0)
try data.write(to:URL(fileURLWithPath:CommandLine.arguments[1]))
let json=records.map{r -> [String:Any] in ["result":r["result"]!,"utf8":Array((r["utf8"] as! Data))]}
let output=try JSONSerialization.data(withJSONObject:json,options:[.prettyPrinted,.sortedKeys]);FileHandle.standardOutput.write(output)
