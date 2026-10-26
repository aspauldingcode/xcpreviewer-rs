from pathlib import Path
import runpy,contextlib,io,json,re,subprocess
w=Path(__file__).parent
with contextlib.redirect_stdout(io.StringIO()):n=runpy.run_path(str(w/'base-source-verify.py'))
m,f,word,call,binding,sha,fields=[n[k] for k in ['m','f','word','call','binding','sha','fields']]
for fd,key,expected,types in [(0xd3410,0xd35a4,['identifier','path','sourceFilePaths','forReplacement'],['SSSg','SS','ShySSG','Sb']),(0xd3450,0xd35e4,['identifier','path'],['SSSg','SS']),(0xd3478,0xd360c,['name','minVersion','sdkVersion'],['SS']*3)]:
 assert fields(m,fd)==fields(m,key)==expected
 assert [m.string(m.relative(fd+20+12*i)) for i in range(len(expected))]==types
assert [call(m,a) for a in [0x1300c,0x13108,0x13180,0x132bc]]==[0xb1948]*4
assert [call(m,a) for a in [0x1306c,0x1331c,0xcba4,0xcc04,0xcc68]]==[0xb190c]*5
assert [word(m,a) for a in [0x13144,0x13150,0x13154]]==[0xf85b83a8,0xf100011f,0x9a88013a]
assert [word(m,a) for a in [0x131f4,0x131f8,0x131fc,0x13200,0x13214]]==[0x385b83a8,0x7100091f,0x1a9f17e9,0x2a080128,0x12000108]
assert word(m,0xba18)==0xb4000369 and word(m,0xba88)==0x370001c8
# Archive's public decoder returns four registers, while its protocol witness
# stores those registers through the caller's indirect result buffer.
assert call(m,0xc198)==call(m,0xc28c)==0x13264
assert [word(m,a) for a in [0xc1a0,0xc1a4,0xc1a8,0xc1ac]]==[0x9a880000,0x9a880021,0x9a880042,0x9a880063]
assert word(m,0xc294)==0xa9000660 and word(m,0xc298)==0xa9010e62
assert word(m,0xc1d4)==0xf9400297 and word(m,0xc1d8)==0xf9400e88
assert binding(m,0xe4478,8)=='_$sSSN' and binding(m,0xe4560,8)=='_$sSbN'
base=json.loads((w/'source-findings.json').read_text())
for a,b,name in [(0xb970,0xbb1c,'object-codec-entry.s'),(0x12fa8,0x13220,'object-decode.s'),(0xc0dc,0xc2a8,'archive-abi-and-encode.s'),(0x13264,0x13388,'archive-decode.s'),(0xca70,0xcce8,'platform-codec.s'),(0x14178,0x14188,'object-metadata.s'),(0x14324,0x14334,'archive-metadata.s'),(0x14540,0x14550,'platform-metadata.s'),(0x13f50,0x13f80,'object-destroy.s'),(0x14188,0x141b0,'archive-destroy.s'),(0x14334,0x14364,'platform-destroy.s')]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(m.path)],capture_output=True,text=True,check=True,timeout=20).stdout
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=m.data[m.file_offset(a):m.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));(w/name).write_text(text);base['ranges'].append({'image':m.path.name,'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
base['selected_source_bytes_verified']=sum(x['bytes'] for x in base['ranges']);base['scope']='Object/archive/platform value codecs, native defaults/omissions, String-set membership and selected archive ABI witnesses. Native randomized source-path Set iteration not reproduced. No file opening, version parsing, replacement/reuse/link/load policy, full target/static/setup/shell, transport/UI/provider or final resource settlement.'
(w/'source-findings.json').write_text(json.dumps(base,indent=2)+'\n');print(base['selected_source_bytes_verified'])
