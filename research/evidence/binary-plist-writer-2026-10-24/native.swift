import Foundation
import CoreFoundation
func node(_ value:Any) throws -> [String:Any] {
    if let v=value as? Data {return ["type":"data","value":v.base64EncodedString()]}
    if let v=value as? Date {return ["type":"date","value":String(v.timeIntervalSinceReferenceDate.bitPattern,radix:16)]}
    if let v=value as? String {return ["type":"string","value":v]}
    if let v=value as? NSNumber {
        if CFGetTypeID(v)==CFBooleanGetTypeID() {return ["type":"bool","value":v.boolValue]}
        let kind=String(cString:v.objCType)
        if kind=="d" || kind=="f" {return ["type":"real","value":String(v.doubleValue.bitPattern,radix:16)]}
        return ["type":"integer","value":v.stringValue]
    }
    if let v=value as? [String:Any] {var result:[String:Any]=[:];for (k,v) in v {result[k]=try node(v)};return ["type":"dictionary","value":result]}
    if let v=value as? [Any] {return ["type":"array","value":try v.map(node)]}
    throw NSError(domain:"owned.unsupported",code:1)
}
let directory=URL(fileURLWithPath:CommandLine.arguments[1]);var rows:[[String:Any]]=[]
for url in try FileManager.default.contentsOfDirectory(at:directory,includingPropertiesForKeys:nil).filter({$0.pathExtension=="bplist"}).sorted(by:{$0.lastPathComponent<$1.lastPathComponent}) {
    do {
    var format=PropertyListSerialization.PropertyListFormat.xml
    let bytes=try Data(contentsOf:url);let value=try PropertyListSerialization.propertyList(from:bytes,options:[],format:&format)
    rows.append(["name":url.deletingPathExtension().lastPathComponent,"format":format.rawValue,"node":try node(value)])
    } catch { let e=error as NSError; rows.append(["name":url.deletingPathExtension().lastPathComponent,"error":e.domain,"code":e.code,"description":e.localizedDescription]) }
}
print(String(decoding:try JSONSerialization.data(withJSONObject:rows,options:[.sortedKeys]),as:UTF8.self))
