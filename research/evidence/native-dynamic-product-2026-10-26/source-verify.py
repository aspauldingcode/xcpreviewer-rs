from pathlib import Path
import runpy,contextlib,io,json,re,subprocess
w=Path(__file__).parent
with contextlib.redirect_stdout(io.StringIO()):n=runpy.run_path(str(w/'base-source-verify.py'))
m,f,word,call,binding,sha,fields=[n[k] for k in ['m','f','word','call','binding','sha','fields']]
assert fields(m,0xd3060)==fields(m,0xd3148)==['path','executablePath','location','loadingStrategy','moduleName','externalFunctionBinding','isRequired']
assert fields(m,0xd30c4)==['absolute','embeddedFrameworks']
assert fields(m,0xd30ec)==['bundle','direct','xojit']
assert fields(m,0xd3120)==['default','immediate']
assert binding(m,0xb190c).endswith('unarchiveValue3forxAA0dE3Key_p_tKAA0dE13RepresentableRzlF')
assert binding(m,0xb1948).endswith('unarchiveOptionalValue3forxSgAA0dE3Key_p_tKAA0dE13RepresentableRzlF')
assert [call(m,a) for a in [0x282c,0x288c,0x293c,0x2980,0x2a20]]==[0xb190c]*5
assert [call(m,a) for a in [0x28f0,0x2a98]]==[0xb1948]*2
assert [word(m,a) for a in [0x2908,0x290c,0x2910]]==[0x3940a3e8,0x7100091f,0x1a8803fa]
assert [word(m,a) for a in range(0x2ae0,0x2af4,4)]==[0x385bd3a8,0x7100091f,0x1a9f17e9,0x2a080128,0x12000108]
base=json.loads((w/'source-findings.json').read_text())
for a,b,name in [(0x14b0,0x1648,'location.s'),(0x17ac,0x1990,'loading-strategy.s'),(0x1b24,0x1d74,'external-binding.s'),(0x2610,0x2b24,'dynamic-codec.s'),(0x2fe0,0x3020,'dynamic-destroy.s')]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(m.path)],capture_output=True,text=True,check=True,timeout=20).stdout
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=m.data[m.file_offset(a):m.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));(w/name).write_text(text);base['ranges'].append({'image':m.path.name,'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
base['selected_source_bytes_verified']=sum(x['bytes'] for x in base['ranges']);base['scope']='Dynamic product value codec, required/optional fields and native defaults. No product loading, path resolution, filesystem validation, external binding execution or transport/UI/provider/final resource settlement.'
(w/'source-findings.json').write_text(json.dumps(base,indent=2)+'\n');print(base['selected_source_bytes_verified'])
