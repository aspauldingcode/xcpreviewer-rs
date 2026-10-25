import Foundation
func string(_ hex:Substring)->String {String(String.UnicodeScalarView(hex.split(separator:",").map {Unicode.Scalar(UInt32($0,radix:16)!)!}))}
let lines=try String(contentsOfFile:CommandLine.arguments[1],encoding:.utf8).split(separator:"\n")
var failures=[[String:Any]]();var counts=[String:Int]()
for line in lines {
 let parts=line.split(separator:"\t");let kind=String(parts[0]);counts[kind,default:0]+=1
 if string(parts[1]) != string(parts[2]) { failures.append(["kind":kind,"left":String(parts[1]),"right":String(parts[2])]) }
}
let out:[String:Any] = ["counts":counts,"failures":failures,"privateDecoderInvoked":false]
try JSONSerialization.data(withJSONObject:out,options:[.prettyPrinted,.sortedKeys]).write(to:URL(fileURLWithPath:CommandLine.arguments[2]))
print("Checked",lines.count,"pairs; mismatches",failures.count)
