from pathlib import Path
import runpy,contextlib,io,json,re,subprocess
w=Path(__file__).parent
with contextlib.redirect_stdout(io.StringIO()):n=runpy.run_path(str(w/'base-source-verify.py'))
m,f,word,call,binding,sha,fields=[n[k] for k in ['m','f','word','call','binding','sha','fields']]
assert fields(m,0xd4548)==fields(m,0xd4570)==['contentSeed','capabilitiesRank']
assert fields(m,0xd4598)==fields(m,0xd45b4)==['sourceIdentifier']
t=m.relative(0xd4548+20);assert m.data[m.file_offset(t)]==2 and binding(m,m.relative(t+1),8)=='_$ss6UInt64VMn'
assert m.string(m.relative(0xd4548+32))=='Si' and m.string(m.relative(0xd4598+20))=='SS'
assert binding(m,0xe47e0,8)=='_$ss6UInt64VN' and binding(m,0xe4580,8)=='_$sSiN' and binding(m,0xe4478,8)=='_$sSSN'
assert [call(m,a) for a in [0x41990,0x419f8,0x41eec]]==[0xb190c]*3
assert word(m,0x41974)==0xf0000501 and word(m,0x41978)==0xf943f021
assert word(m,0x419dc)==0xf0000501 and word(m,0x419e0)==0xf942c021
assert word(m,0x41ed0)==0xf0000501 and word(m,0x41ed4)==0xf9423c21
assert word(m,0x41a2c)==0xa90022d8 and word(m,0x41f20)==0xa9002668
assert word(m,0x325c)==0xd65f03c0 and word(m,0x20f04)==0xf9400400 and call(m,0x20f08)==0xb2548
base=json.loads((w/'source-findings.json').read_text())
for a,b,name in [(0x4187c,0x41a4c,'seed-codec.s'),(0x41b14,0x41b24,'seed-metadata.s'),(0x41df8,0x41f40,'identity-codec.s'),(0x41fe0,0x41ff0,'identity-metadata.s'),(0x325c,0x3260,'seed-destroy.s'),(0x20f04,0x20f0c,'identity-destroy.s')]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(m.path)],capture_output=True,text=True,check=True,timeout=20).stdout
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=m.data[m.file_offset(a):m.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));(w/name).write_text(text);base['ranges'].append({'image':m.path.name,'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
base['selected_source_bytes_verified']=sum(x['bytes'] for x in base['ranges']);base['scope']='Product identity/seed dictionary codecs with required String, UInt64 and Int field types. Primitive numeric bridge profiles runtime-qualified; full numeric bridge body not statically recovered. No native identity equality/hash, seed order, capabilities arbitration, artifact reuse, loader, transport/UI/provider or final resource settlement.'
(w/'source-findings.json').write_text(json.dumps(base,indent=2)+'\n');print(base['selected_source_bytes_verified'])
