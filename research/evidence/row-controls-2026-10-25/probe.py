from pathlib import Path
import json,subprocess
w=Path(__file__).parent;choices=[]
for i in range(8):
 p=subprocess.run([str(w/'native'),'--probe'],capture_output=True,text=True,timeout=8,check=True);choice=p.stdout.strip();assert choice in ['a','b'];choices.append(choice)
(w/'native-order-probes.json').write_text(json.dumps({'scope':'actual public Swift Set.first(where:) over two matching direct IDs, across eight independent processes; private binding not invoked','choices':choices,'distinct':sorted(set(choices)),'portable_choice':'a','native_choice_order_parity':False},indent=2)+'\n')
print('Eight actual public Set read probes returned only eligible IDs; order not constrained')
