import Foundation
var ranges:[[UInt32]]=[];var first:UInt32?=nil;var last:UInt32=0
let prefix="[Remote] "
for raw in UInt32(0)...UInt32(0x10ffff) {
 guard let scalar=UnicodeScalar(raw) else {continue}
 let rejected = !(prefix+String(scalar)+"x").hasPrefix(prefix)
 if rejected {
  if let begin=first,raw != last+1 {ranges.append([begin,last]);first=raw}
  if first==nil {first=raw};last=raw
 } else if let begin=first {ranges.append([begin,last]);first=nil}
}
if let begin=first {ranges.append([begin,last])}
let controls=["[Remote] owned","[Remote] 🪨","[Remote] \u{301}x","[Remote] \u{fe0f}x","[Remote] \u{200d}x","[Remote] \u{903}x","[Remote] \nx"]
let output:[String:Any] = ["valid_scalars":1112064,"ranges":ranges,"controls":controls.map { ["title":$0,"has_prefix":$0.hasPrefix(prefix),"normalized":$0.hasPrefix(prefix) ? $0 : prefix+$0] as [String:Any] }]
FileHandle.standardOutput.write(try JSONSerialization.data(withJSONObject:output,options:[.sortedKeys]));print("")
