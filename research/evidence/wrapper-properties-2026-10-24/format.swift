import Foundation
let cases:[(String?,String?)]=[(nil,nil),("",nil),(nil,""),("",""),("main","cause"),("雪 🪨","é\u{301}"),("a\0b%","c\0d%@")]
var rows:[[String:Any]]=[]
for (index,pair) in cases.enumerated(){let result:String?;switch pair{case(nil,nil):result=nil;case(let a?,nil):result=a;case(nil,let b?):result=b;case(let a?,let b?):result=String(format:"%@: %@",a,b)};rows.append(["index":index,"result":result as Any? ?? NSNull(),"utf8":result.map{Array($0.utf8)} as Any? ?? NSNull()])}
FileHandle.standardOutput.write(try JSONSerialization.data(withJSONObject:rows,options:[.prettyPrinted,.sortedKeys]));print("")
