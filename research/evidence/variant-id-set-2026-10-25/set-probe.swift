import Foundation
let pairs:[(String,String)] = [("é","e\u{301}"),("Å","A\u{30a}"),("Å","Å"),("각","각"),("a\u{315}\u{300}","a\u{300}\u{315}"),("ﬀ","ff"),("Ａ","A"),("A","a"),("a\u{301}\u{34f}","á"),("\u{2126}","Ω")]
var rows=[[String:Any]]()
for (a,b) in pairs {
 for values in [[a,b],[b,a]] {
  let set=Set(values)
  let enc=Array(set)
  rows.append(["input":values,"equal":a==b,"count":set.count,"representatives":enc.map{Array($0.utf8)},"first":Array(values[0].utf8),"allRetainFirst":set.count != 1 || Array(enc[0].utf8)==Array(values[0].utf8)])
 }
}
let orderInput=(0..<12).map{"id\($0)"}
let out:[String:Any] = ["rows":rows,"order":Array(Set(orderInput)),"inputOrder":orderInput]
try PropertyListSerialization.data(fromPropertyList:out,format:.binary,options:0).write(to:URL(fileURLWithPath:CommandLine.arguments[1]))
