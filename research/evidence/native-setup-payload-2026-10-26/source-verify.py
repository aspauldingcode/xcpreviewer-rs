from pathlib import Path
import runpy,contextlib,io,json,re,subprocess
w=Path(__file__).parent
with contextlib.redirect_stdout(io.StringIO()):n=runpy.run_path(str(w/'base-source-verify.py'))
m,f,word,call,binding,sha,fields=[n[k] for k in ['m','f','word','call','binding','sha','fields']]
assert fields(m,0xd3cec)==['dynamicProducts','shellDidLoadStaticProducts','updates','loggingOutputPath','staticProducts']
assert fields(m,0xd3e78)==['dynamicProducts','staticProducts','shellDidLoadStaticProducts','updates','loggingOutputPath']
assert [call(m,a) for a in [0x24d98,0x24eac]]==[0xb190c]*2
assert [call(m,a) for a in [0x24cf8,0x24df8,0x24f44]]==[0xb1948]*3
assert word(m,0x24c84)==0xaa0803f7 and word(m,0x24a50)==0xad400680
assert word(m,0x24d30)==0xf9441908 and binding(m,0xe4830,8)=='__swiftEmptyArrayStorage'
assert word(m,0x24d3c)==0x9a890116
assert word(m,0x24e34)==0x7100091f and word(m,0x24e40)==0xf9400ac8 and word(m,0x24e48)==0x1a9f07e8
assert [call(m,a) for a in [0x27500,0x27508,0x27510,0x27520]]==[0xb2548]*4
base=json.loads((w/'source-findings.json').read_text())
for a,b,name in [(0x24a44,0x24fb4,'setup-codec.s'),(0x246dc,0x247b0,'setup-key-hash.s'),(0x274ec,0x27524,'setup-destroy.s'),(0x27738,0x27748,'setup-metadata.s')]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(m.path)],capture_output=True,text=True,check=True,timeout=20).stdout
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=m.data[m.file_offset(a):m.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));(w/name).write_text(text);base['ranges'].append({'image':m.path.name,'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
base['selected_source_bytes_verified']=sum(x['bytes'] for x in base['ranges']);base['scope']='Setup record fields, required/optional calls, empty static array and dependent Bool default, encoding and destruction. Incremental multi-key ambiguity remains an explicit portable restriction; no setup application or transport.'
(w/'source-findings.json').write_text(json.dumps(base,indent=2)+'\n');print(base['selected_source_bytes_verified'])
