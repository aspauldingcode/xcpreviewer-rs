import Foundation
let initial:Set<String>=["b","a"]
var result=initial
for id in initial {result.formUnion(Set([id=="a" ? "e\u{301}":"é"]))}
var parent:Set<String>=["a","e\u{301}"];parent.formUnion(Set(["é"]))
let out:[String:Any]=["initialOrder":Array(initial),"selectedCount":result.count,"canonicalMembers":result.map{$0.decomposedStringWithCanonicalMapping}.sorted(),"siblingRepresentativeBytes":Array(result.first{$0=="é"}!.utf8),"parentRepresentativeBytes":Array(parent.first{$0=="é"}!.utf8)]
try JSONSerialization.data(withJSONObject:out,options:[.prettyPrinted,.sortedKeys]).write(to:URL(fileURLWithPath:CommandLine.arguments[1]))
