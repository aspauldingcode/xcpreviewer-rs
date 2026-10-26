import Foundation
let root=URL(fileURLWithPath:CommandLine.arguments[1]);var count=0
for f in try FileManager.default.contentsOfDirectory(at:root,includingPropertiesForKeys:nil) where f.lastPathComponent.hasSuffix(".canonical.bplist") {
 let d=try Data(contentsOf:f);let v=try PropertyListSerialization.propertyList(from:d,format:nil)
 let d2=try PropertyListSerialization.data(fromPropertyList:v,format:.binary,options:0)
 try d2.write(to:f.appendingPathExtension("reparsed"));count+=1
}
precondition(count==131);print(count)
