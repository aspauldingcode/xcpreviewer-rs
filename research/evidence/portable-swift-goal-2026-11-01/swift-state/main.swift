struct Counter { var value=0; mutating func increment(){ value += 1 } }
var counter=Counter()
print("count=\(counter.value)")
counter.increment()
print("count=\(counter.value)")
counter.increment()
print("count=\(counter.value)")
