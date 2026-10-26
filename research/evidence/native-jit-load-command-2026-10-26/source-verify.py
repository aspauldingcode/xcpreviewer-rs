from pathlib import Path
import runpy,contextlib,io,json,re,subprocess
w=Path(__file__).parent
with contextlib.redirect_stdout(io.StringIO()):n=runpy.run_path(str(w/'base-source-verify.py'))
m,f,word,call,binding,sha,fields=[n[k] for k in ['m','f','word','call','binding','sha','fields']]
assert fields(m,0xd58c8)==fields(m,0xd5968)==['loadDylib']
assert fields(m,0xd5940)==['discriminant','command']
assert fields(m,0xd58e4)==fields(m,0xd5984)==['path','linkage','symbolsPath']
assert fields(m,0xd5918)==['strong','weak']
assert m.string(m.relative(0xd58e4+20))=='SS' and m.string(m.relative(0xd58e4+44))=='SSSg'
assert [call(m,a) for a in [0x71914,0x71978,0x71aa8]]==[0xb190c]*3
assert [call(m,a) for a in [0x71b08,0x71b48]]==[0xb1948]*2
assert word(m,0x71ba0)==0x71000b7f and word(m,0x71ba4)==0x1a9b03f8
# Public enum/struct decoder entrypoints use indirect results, unlike the
# prior archive register ABI. Verify this before native invocation.
assert word(m,0x6ff0c)==word(m,0x70668)==0xaa0803f3
assert call(m,0x6ff14)==0x718bc and call(m,0x70670)==0x71a48
assert word(m,0x70680)==0xad000660 and word(m,0x70688)==0xf9001268
assert word(m,0x6fe44)==0xaa1403f3 and word(m,0x70590)==0xf9000bf4
assert call(m,0x720b8)==0x71d50 and call(m,0x71d50)==0x71d54
assert word(m,0x71d64)==0xf9400400 and word(m,0x71d6c)==0xf9401260
assert call(m,0x71d68)==call(m,0x71d78)==0xb2548
base=json.loads((w/'source-findings.json').read_text())
for a,b,name in [(0x6fe28,0x6ff40,'command-codec-entry.s'),(0x70584,0x7069c,'dylib-codec-entry.s'),(0x718bc,0x719dc,'command-decode.s'),(0x71a48,0x71be0,'dylib-decode.s'),(0x71d40,0x71d7c,'command-metadata-destroy.s'),(0x71e94,0x71ea4,'dylib-metadata.s'),(0x720b8,0x720bc,'shared-destroy-trampoline.s')]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(m.path)],capture_output=True,text=True,check=True,timeout=20)
 text=text.stdout
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=m.data[m.file_offset(a):m.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));(w/name).write_text(text);base['ranges'].append({'image':m.path.name,'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
base['selected_source_bytes_verified']=sum(x['bytes'] for x in base['ranges']);base['scope']='JIT load-command single-case enum and nested dylib description value codecs, closed strong/weak linkage with missing-strong default, indirect public method ABI and shared destructor trampoline. No dylib loading, symbol path use, linkage resolution, native identity/hash/order, full target/static/setup/shell, transport/UI/provider or final resource settlement.'
(w/'source-findings.json').write_text(json.dumps(base,indent=2)+'\n');print(base['selected_source_bytes_verified'])
