from pathlib import Path
import os,signal,subprocess,json
w=Path(__file__).parent
sources={'swift-state':'struct Counter { var value=0; mutating func increment(){ value += 1 } }\nvar counter=Counter()\nprint("count=\\(counter.value)")\ncounter.increment()\nprint("count=\\(counter.value)")\ncounter.increment()\nprint("count=\\(counter.value)")\n','swiftui-state':'import SwiftUI\nstruct CounterView: View { @State private var count=0; var body: some View { Button("Count: \\(count)") { count += 1 } } }\nprint("fixture")\n'}
results={}
for name,source in sources.items():
 root=w/name;(root/'Sources/Probe').mkdir(parents=True,exist_ok=True)
 (root/'Package.swift').write_text('// swift-tools-version: 6.0\nimport PackageDescription\nlet package = Package(name:"Probe",targets:[.executableTarget(name:"Probe")])\n')
 (root/'Sources/Probe/main.swift').write_text(source)
 args=['/Users/8amps/.swiftly/bin/swift','build','--package-path',str(root),'--swift-sdk','6.3-RELEASE-wasm32-unknown-wasip1','--scratch-path',str(root/'build'),'--cache-path',str(w/'cache'),'--security-path',str(w/'security'),'--manifest-cache','local','--jobs','1']
 p=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,env={**os.environ,'SWIFTPM_DISABLE_PLUGINS':'1'})
 timed=False
 try:a,b=p.communicate(timeout=60)
 except subprocess.TimeoutExpired:
  timed=True;os.killpg(p.pid,signal.SIGKILL);a,b=p.communicate()
 (w/(name+'.stdout')).write_bytes(a);(w/(name+'.stderr')).write_bytes(b);results[name]={'returncode':p.returncode,'timed_out':timed}
(w/'build-results.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results))
