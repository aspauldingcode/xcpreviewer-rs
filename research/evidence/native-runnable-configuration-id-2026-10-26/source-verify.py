from pathlib import Path
import runpy,json,re,subprocess,contextlib,io
w=Path(__file__).parent
with contextlib.redirect_stdout(io.StringIO()):n=runpy.run_path(str(w/'state-source-verify.py'))
m,f,p,word,call,binding,sha=[n[k] for k in ['m','f','p','word','call','binding','sha']]
def fields(image,a):
 _,size,count=image.unpack('<HHI',image.file_offset(a+8));assert size==12;return [image.string(image.relative(a+16+i*size+8)) for i in range(count)]
assert fields(p,0x55aab8)==['displayMode','overrides','controlState']
assert fields(p,0x55aaec)==['displayMode','overrides','controlState']
assert fields(m,0xd6e3c)==['id','displayName','renderEffects','interfaceOrientationOverride']
assert fields(m,0xd6e7c)==['rawValue']
t=m.relative(0xd6e7c+20);assert m.data[m.file_offset(t):m.file_offset(t)+3]==b'SS\x00'
assert word(p,0x3a4d50)==0x39400009 and word(p,0x3a4d54)==0xf940004a and word(p,0x3a4d5c)==0xa900a901
assert call(p,0x3b9a40)==0x3c051c
assert call(p,0x3c5b68)==0x3c1068 and call(p,0x3c1068)==0x43324
assert word(p,0x43334)==0xf9400400 and word(p,0x4333c)==0xf9400a60 and call(p,0x43338)==call(p,0x43348)==0x520e1c
assert binding(p,0x51dc24)=='_$s21PreviewsMessagingHost14PreviewVariantVMa'
assert binding(p,0x51dc0c)=='_$s21PreviewsMessagingHost14PreviewVariantV2IDVMa'
assert binding(p,0x51dc18)=='_$s21PreviewsMessagingHost14PreviewVariantV2idAC2IDVvg'
assert call(p,0x3b9e30)==0x51dc18 and word(p,0x3b9ed4)==0xa9008378
assert word(p,0x3b9db0)==0x39400288 and word(p,0x3b9db8)==0xa9408297 and word(p,0x3b9dbc)==0xf9400afa
assert word(p,0x3b9c8c)==0x39400288 and call(p,0x3b9cb0)==0x3b9a44
base=json.loads((w/'source-findings.json').read_text());ranges=[]
for image,a,b,name in [(p,0x3a4d50,0x3a4d64,'configuration-init.s'),(p,0x3c1058,0x3c1068,'configuration-metadata.s'),(p,0x3c1168,0x3c1178,'configuration-id-metadata.s'),(p,0x3c5b68,0x3c5b6c,'configuration-destroy-thunk.s'),(p,0x3c1068,0x3c106c,'configuration-destroy-alias.s'),(p,0x43324,0x4334c,'configuration-destroy.s'),(p,0x3b9a40,0x3b9a44,'configuration-id-equality-entry.s'),(p,0x3b9a44,0x3b9ccc,'configuration-id-hash.s'),(p,0x3b9d1c,0x3b9ef8,'configuration-id-projection.s'),(m,0xa4930,0xa4950,'variant-metadata.s'),(m,0x3636c,0x36388,'variant-id-getter.s'),(m,0x36b0c,0x36b24,'variant-id-string-getter.s'),(m,0xa17bc,0xa1c9c,'variant-plist-codec.s'),(m,0xa1e5c,0xa1eb0,'variant-plist-witnesses.s')]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(image.path)],capture_output=True,text=True,check=True,timeout=20).stdout
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=image.data[image.file_offset(a):image.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));(w/name).write_text(text);ranges.append({'image':image.path.name,'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
base['ranges']+=ranges;base['selected_source_bytes_verified']=sum(x['bytes'] for x in base['ranges']);base['scope']='Qualified runnable Configuration.ID construction/getter/equality/hash/ownership and typed native PreviewVariant codecs. Actual calls in native.bplist; outer PreviewConfiguration.ID, real cache/provider/transport/UI/global settlement excluded.'
(w/'source-findings.json').write_text(json.dumps(base,indent=2)+'\n');print(json.dumps({'bytes':base['selected_source_bytes_verified'],'native_variant_id_field':'rawValue:String','native_configuration_id_fields':fields(p,0x55aaec)}))
