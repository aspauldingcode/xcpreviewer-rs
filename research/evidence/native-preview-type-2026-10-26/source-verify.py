from pathlib import Path
import runpy,contextlib,io,json,re,subprocess
w=Path(__file__).parent
with contextlib.redirect_stdout(io.StringIO()):n=runpy.run_path(str(w/'base-source-verify.py'))
m,f,word,call,binding,sha,fields=[n[k] for k in ['m','f','word','call','binding','sha','fields']]
assert fields(m,0xd3d38)==['hosted','static'] and fields(m,0xd3d60)==['injectedScene','mainScene','simDisplayScene','external','nsPreview']
assert fields(m,0xd3ef8)==['discriminant','sceneIdentifier'] and fields(m,0xd3f6c)==['discriminant','hostLocation']
assert fields(m,0xd3f20)==['mainScene','simDisplayScene','injectedScene','external','nsPreview']
t=m.relative(0xd3d60+20);assert m.data[m.file_offset(t):m.file_offset(t)+len(b'SS10identifier_t\x00')]==b'SS10identifier_t\x00'
# Host injectedScene is discriminant2: required String sceneIdentifier; other
# tags choose payload-free cases without accessing its inactive member.
assert word(m,0x25f60)==0x7100091f and word(m,0x25fc8)==0x52800028 and call(m,0x25fec)==0xb190c
assert binding(m,0xe4478,8)=='_$sSSN' and binding(m,0xe5308,8)=='_$sSS22PreviewsFoundationHost25PropertyListRepresentableAAWP'
assert word(m,0x25dc8)==0x52800028 and call(m,0x25dec)==0xb1900
assert word(m,0x267d4)==0x7100051f and word(m,0x267d8)==0x54000301 and call(m,0x26800)==0xb190c
assert word(m,0x25ebc)==0xd10203ff and word(m,0x26738)==0xd10203ff
# String payloads are released by the native witnesses only for payload tags.
assert call(m,0x2776c)==0xb2548 and call(m,0x27ad4)==0xb2548
base=json.loads((w/'source-findings.json').read_text());ranges=[]
for a,b,name in [(0x256ac,0x26898,'preview-location-codecs.s'),(0x2774c,0x27774,'preview-type-destroy.s'),(0x27ab0,0x27adc,'preview-type-metadata-location-destroy.s'),(0x27d28,0x27d3c,'location-metadata.s')]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(m.path)],capture_output=True,text=True,check=True,timeout=20).stdout
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=m.data[m.file_offset(a):m.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));(w/name).write_text(text);ranges.append({'image':m.path.name,'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
base['ranges']+=ranges;base['selected_source_bytes_verified']=sum(x['bytes'] for x in base['ranges']);base['scope']='Actual native PreviewType/HostLocation value decoders/encoders/destructors on owned dictionary inputs. Closed active-payload codecs only; no equality/hash/scene routing, complete shell/instance/updater/transport/UI/provider/resource parity.'
(w/'source-findings.json').write_text(json.dumps(base,indent=2)+'\n');print(base['selected_source_bytes_verified'])
