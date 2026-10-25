import Foundation
var ranges:[[Int]]=[];var begin:Int?=nil;var end=0;var tested=0;var mismatches=0
for code in 0...0x10ffff {guard let scalar=UnicodeScalar(code)else{continue};tested+=1
 let suffix=String(scalar)+"x"
 let blocked=("\\n"+suffix).replacingOccurrences(of:"\\n",with:"\n")==("\\n"+suffix)
 let remoteBlocked = !("[Remote] "+suffix).hasPrefix("[Remote] ")
 if blocked != remoteBlocked {mismatches+=1}
 if blocked {if let start=begin,code != end+1{ranges.append([start,end]);begin=code}else if begin == nil {begin=code};end=code}
}
if let start=begin{ranges.append([start,end])}
let data=try JSONSerialization.data(withJSONObject:["tested":tested,"mismatches_with_remote_boundary":mismatches,"rejected":ranges],options:[.sortedKeys]);FileHandle.standardOutput.write(data)
