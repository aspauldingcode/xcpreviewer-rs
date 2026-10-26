from pathlib import Path
import runpy,contextlib,io,json,re,subprocess
w=Path(__file__).parent
with contextlib.redirect_stdout(io.StringIO()):n=runpy.run_path(str(w/'base-source-verify.py'))
m,f,word,call,binding,sha,fields=[n[k] for k in ['m','f','word','call','binding','sha','fields']]
assert fields(m,0xd3c24)==['pid','hostUpdateSeed','hostUpdateGroupSeed','previewType','contentIdentifier','contentCategory','contentOverride','contentPayload','staticProducts','setupPayload','controlStates']
assert fields(m,0xd3cec)==['dynamicProducts','shellDidLoadStaticProducts','updates','loggingOutputPath','staticProducts']
# Exact raw key spelling controlStates in the selected rawValue getter branch.
assert [word(m,a) for a in range(0x22c58,0x22c78,4)]==[0xd28c2e81,0xf2acae81,0xf2c00e61,0xf2fda001,0xd28dec60,0xf2ae8dc0,0xf2cdee40,0xf2ea6d80]
assert call(m,0x23d24)==call(m,0x232ec)==0x24184
assert call(m,0x23d3c)==0xb1948 and binding(m,0xb1948)=='_$s22PreviewsFoundationHost12PropertyListV22unarchiveOptionalValue3forxSgAA0dE3Key_p_tKAA0dE13RepresentableRzlF'
assert word(m,0x23d04)==0x52800148 # key tag 10
assert word(m,0x23f14)==0xb9803ae8 and word(m,0x23f18)==0xf8286b14 # final field ownership transfer
assert word(m,0x26b68)==0xb9803a88 and word(m,0x26b6c)==0xf8686a60 and call(m,0x26b7c)==0xb2548
assert binding(m,0xb2548)=='_swift_bridgeObjectRelease'
# Setup Key case1 uses legacy spelling products (not dynamicProducts).
assert [word(m,a) for a in range(0x246f0,0x24700,4)]==[0xd28e4e0a,0xf2ac8dea,0xf2cc6eaa,0xf2ee6e8a]
base=json.loads((w/'source-findings.json').read_text());ranges=[]
for image,a,b,name in [(m,0x22b20,0x22ca0,'shell-keys.s'),(m,0x22df8,0x242c8,'shell-codec.s'),(m,0x26ad4,0x26b80,'shell-destroy.s'),(m,0x246dc,0x247b0,'setup-key-spelling.s')]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(image.path)],capture_output=True,text=True,check=True,timeout=20).stdout
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=image.data[image.file_offset(a):image.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));(w/name).write_text(text);ranges.append({'image':image.path.name,'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
assert [call(m,a) for a in [0x23648,0x236e0,0x238a8,0x23968,0x239ec,0x23b3c]]==[0xb190c]*6
assert [call(m,a) for a in [0x23790,0x23820,0x23a44,0x23c40,0x23d3c]]==[0xb1948]*5
assert binding(m,0xe4750,8)=='_$ss5Int32VMn'
assert binding(m,0xe4fb8,8)=='_$s22PreviewsFoundationHost12PropertyListVMn'
for fd in [0xd41a4,0xd41c0,0xd41dc]:
 assert fields(m,fd)==['rawValue']
 t=m.relative(fd+20);assert m.data[m.file_offset(t):m.file_offset(t)+3]==b'SS\x00'
base['ranges']+=ranges;base['selected_source_bytes_verified']=sum(x['bytes'] for x in base['ranges']);base['scope']='All eleven ShellUpdatePayload fields, six required and five optional generic decodes, raw String content roles, Int32 PID, raw PropertyList dictionary content and complete selected shell codec/destruction. Incremental ambiguity/control-box canonical-key profile inherited; no native delivery/application/transport/resources.'
(w/'source-findings.json').write_text(json.dumps(base,indent=2)+'\n');print(base['selected_source_bytes_verified'])
