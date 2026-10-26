import Foundation
import CoreFoundation
struct Key:Hashable {let category:String;let ids:[String]}
struct Ticket {let key:Key;let task:Int;let created:Bool}
enum Invalid:Error {case value}
func dict(_ v:Any)throws->[String:Any]{guard let d=v as? [String:Any] else{throw Invalid.value};return d}
func boolean(_ f:[String:Any],_ k:String,_ fallback:Bool)throws->Bool{guard let v=f[k] else{return fallback};guard let n=v as? NSNumber,CFGetTypeID(n)==CFBooleanGetTypeID() else{throw Invalid.value};return n.boolValue}
func key(_ f:[String:Any])throws->Key{let d=try dict(f["request"] as Any);guard let c=d["contentCategory"] as? String,let ids=d["requestedOverrides"] as? [String] else{throw Invalid.value};return Key(category:c,ids:ids)}
enum Op {case acquire(Key),failure(Int),invalidate(Key,Bool)}
func trace(_ input:Any)throws->[String:Any]{let f=try dict(input),clear=try boolean(f,"clearOnFailure",false);guard let values=f["operations"] as? [Any] else{throw Invalid.value};var available=[Bool]();let ops=try values.map{v->Op in let f=try dict(v);guard let op=f["op"] as? String else{throw Invalid.value};switch op{case "acquire":let k=try key(f);available.append(true);return .acquire(k)
case "failure":guard let n=f["ticket"] as? NSNumber,CFGetTypeID(n) != CFBooleanGetTypeID(),!["f","d"].contains(String(cString:n.objCType)),let i=f["ticket"] as? Int,i>=0,i<available.count,available[i] else{throw Invalid.value};available[i]=false;return .failure(i)
case "invalidate":return .invalidate(try key(f),try boolean(f,"cancelingTask",true))
default:throw Invalid.value}}
 // Original serialized handle-storage composition; no Task executor or private actor invoked.
 var storage=[Key:Int](),tickets=[Ticket?](),starts=0,cancels=[Int](),events=[[String:Any]]()
 for op in ops{var e=[String:Any]();switch op{case .acquire(let k):let task:Int,created:Bool;if let old=storage[k]{task=old;created=false}else{starts+=1;task=starts;created=true;storage[k]=task};tickets.append(Ticket(key:k,task:task,created:created));e=["op":"acquire","task":task,"created":created]
 case .failure(let i):let ticket=tickets[i]!;tickets[i]=nil;e=["op":"failure"];if clear && ticket.created{if let task=storage.removeValue(forKey:ticket.key){e["removed"]=task}}
 case .invalidate(let k,let cancel):e=["op":"invalidate"];if cancel,let task=storage[k]{cancels.append(task);e["cancelRequested"]=task};if let task=storage.removeValue(forKey:k){e["removed"]=task}}
 events.append(e)}
 return ["events":events,"tasksStarted":starts,"retainedTasks":storage.values.sorted(),"cancelRequests":cancels]
}
func request(_ ids:[String]=[],_ category:String="cat")->[String:Any]{["contentCategory":category,"requestedOverrides":ids]}
func a(_ ids:[String]=[],_ category:String="cat")->[String:Any]{["op":"acquire","request":request(ids,category)]}
func fail(_ ticket:Int)->[String:Any]{["op":"failure","ticket":ticket]}
func inv(_ ids:[String]=[],_ cancel:Bool?=nil)->[String:Any]{var d:[String:Any]=["op":"invalidate","request":request(ids)];if let cancel=cancel{d["cancelingTask"]=cancel};return d}
func input(_ ops:[[String:Any]],_ clear:Bool?=nil)->[String:Any]{var d:[String:Any]=["operations":ops];if let clear=clear{d["clearOnFailure"]=clear};return d}
let cases:[(String,Any)]=[
 ("empty",input([])),("one",input([a()])),("coalesced-handles",input([a(),a(),a()])),
 ("failure-retained-by-default",input([a(),fail(0),a()])),
 ("creator-failure-cleared",input([a(),fail(0),a()],true)),
 ("reused-failure-does-not-clear",input([a(),a(),fail(1),a()],true)),
 ("creator-clears-after-reused-failure",input([a(),a(),fail(1),fail(0),a()],true)),
 ("default-invalidation-cancels",input([a(),inv(),a()])),
 ("invalidation-without-cancel",input([a(),inv([],false),a()])),
 ("missing-invalidation",input([inv()])),
 ("late-creator-failure-clears-replacement",input([a(),inv([],false),a(),fail(0),a()],true)),
 ("late-failure-retained-default",input([a(),inv([],false),a(),fail(0),a()])),
 ("old-reused-failure-keeps-replacement",input([a(),a(),inv([],false),a(),fail(1),a()],true)),
 ("ordered-keys",input([a(["a","b"]),a(["b","a"]),a(["a","b"])])),
 ("duplicate-count-keys",input([a(["a"]),a(["a","a"]),a(["a"])])),
 ("canonical-keys",input([a(["é"],"é"),a(["e\u{301}"],"e\u{301}")])),
 ("categories-differ",input([a([],"a"),a([],"b")])),
 ("repeated-invalidation",input([a(),inv(),inv()])),
 ("waiter-failure-after-clear",input([a(),a(),fail(0),fail(1),a()],true)),
 ("long-many",input((0..<24).map{a([String(repeating:"é👩‍💻\n",count:300),"v\($0 % 3)"])})),
 ("missing-ops",["clearOnFailure":false]),
 ("bad-clear",["clearOnFailure":1,"operations":[]] as [String:Any]),
 ("unknown-op",input([["op":"settle"]])),
 ("bad-late-request",input([a(),["op":"acquire","request":["contentCategory":"cat","requestedOverrides":[false]]]])),
 ("future-ticket",input([fail(0)])),("consumed-ticket",input([a(),fail(0),fail(0)]))
]
var rows=[[String:Any]]()
for (name,input) in cases{var row:[String:Any]=["name":name,"kind":"task-cache","input":input,"accepted":false];do{row["output"]=try trace(input);row["accepted"]=true}catch{};rows.append(row)}
try PropertyListSerialization.data(fromPropertyList:rows,format:.binary,options:0).write(to:URL(fileURLWithPath:CommandLine.arguments[1]))
print("26 original public Swift Dictionary/Foundation state compositions;20 accept/six reject;no private actor/executor invocation")
