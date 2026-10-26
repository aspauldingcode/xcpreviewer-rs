from pathlib import Path
import runpy,contextlib,io,json,re,subprocess
w=Path(__file__).parent
with contextlib.redirect_stdout(io.StringIO()):n=runpy.run_path(str(w/'state-source-verify.py'))
p,m,f,word,call,binding,sha=[n[k] for k in ['p','m','f','word','call','binding','sha']]
def fields(a):
 _,size,count=p.unpack('<HHI',p.file_offset(a+8));return [p.string(p.relative(a+16+i*size+8)) for i in range(count)]
assert fields(0x556dcc)==['configuration','metadata','contentOverride']
assert fields(0x55c0cc)==['instance','location','updateMode','overrides','variant','controlStates','localizationOverride']
assert call(p,0x15b0a4)==0x46bac4 # PreviewConfiguration metadata
assert word(p,0x15b300)==0xb9802733 and word(p,0x15b314)==0xf8736ad3 and word(p,0x15b318)==0xf9400a7b # metadata field5 then ordered count
assert word(p,0x15b324)==0xb400081b # empty -> empty array, not nil
assert call(p,0x15b30c)==0x520f84 and binding(p,0x520f84)=='_swift_getKeyPath'
assert call(p,0x15b384)==0x520f24 and binding(p,0x520f24)=='_swift_getAtKeyPath'
assert p.relative(0x52a8a8)==0x15c61c # actual computed getter in key-path pattern
assert word(p,0x15c628)==0xaa0003f4 and word(p,0x15c62c)==0xaa0803f3
assert call(p,0x15c648)==0x51e614 and binding(p,0x51e614)=='_$s22PreviewsFoundationHost11HashableBoxV5valuexvg'
assert word(p,0x15b3e0)==0xf100077b and word(p,0x15b3e4)==0x54fffc01 # loop source order, count/duplicates
assert word(p,0x15b568)==0xaa1703e6 and word(p,0x15b570)==0xd63f0120 # array always passes as controls arg
base=json.loads((w/'source-findings.json').read_text());ranges=[]
for a,b,name in [(0x15ad60,0x15b61c,'execution-point-behavior.s'),(0x15c61c,0x15c658,'control-value-keypath-getter.s')]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(p.path)],capture_output=True,text=True,check=True,timeout=20).stdout
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=p.data[p.file_offset(a):p.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));(w/name).write_text(text);ranges.append({'image':p.path.name,'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
base['ranges']+=ranges;base['selected_source_bytes_verified']=sum(x['bytes'] for x in base['ranges']);base['keypath_pattern']={'address':'0x52a878','getter_relative_field':'0x52a8a8','getter':'0x15c61c','bytes':52,'sha256':sha(p.data[p.file_offset(0x52a878):p.file_offset(0x52a878)+52])};base['scope']='Source-qualified PreviewExecutionPoint.updateBehavior mapping of configuration controlStates into always-present ordered original boxes at instance behavior boundary. Only selected native key-path getter executes, with native state containers/copies. Full behavior getter, instance/downstream updater routing and live transport/resources remain unexecuted.'
(w/'source-findings.json').write_text(json.dumps(base,indent=2)+'\n');print(base['selected_source_bytes_verified'])
