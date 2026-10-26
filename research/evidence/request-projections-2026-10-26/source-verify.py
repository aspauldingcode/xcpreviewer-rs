from pathlib import Path
import sys,hashlib,json,subprocess,re
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).parent;sys.path.insert(0,str(r/'tools/re'))
from reloop.swiftmeta import MachO
from reloop.stubbind import tables,index
sha=lambda b:hashlib.sha256(b).hexdigest()
m=MachO(Path('/Applications/Xcode.app/Contents/SharedFrameworks/PreviewsPipeline.framework/Versions/A/PreviewsPipeline'))
assert sha(m.data)=='c0897c050716f12f88da4dd08c24e3d3ae1de36dc748b65ad0b7346979e40053'
def word(a):return m.u32(m.file_offset(a))
def call(a):
 v=word(a);assert v>>26 in [5,37];n=v&0x3ffffff;return a+4*(n-(1<<26) if n&(1<<25) else n)
def binding(a):
 s,ind,libs=tables(m);sec=next(t for t in m.sections if t['address']<=a<t['address']+t['size']);i=index(m,sec,a,12,ind);n,k,ss,d,v=m.unpack('<IBBHQ',s[0]+16*i);assert k&0xe==0 and ss==0 and v==0;o=s[2]+n;return m.data[o:m.data.index(0,o)].decode()

def fields(a):
 _,size,n=m.unpack('<HHI',m.file_offset(a+8));assert size==12;return [m.string(m.relative(a+16+i*size+8)) for i in range(n)]
assert fields(0x558c04)==['previewMetadata','contentOverride','supportedVariantGroups','supportsTogglingExternalHosting','supportsContinuousLivePreview','supportsStaticPreviews','supportsScreenshotRequests','staticUpdateMode','destinationDisplayName']
assert fields(0x55aa68)==['interactive','static']
assert fields(0x55aab8)==['displayMode','overrides','controlState']
assert fields(0x5554e8)==['previewInstance','destinationPreferences','origin','configuration','variant','capabilities','context','localizationOverride']
assert fields(0x557058)==['live','grid','static']
assert fields(0x55b758)==['inCanvas','external']
# Request field3's indirect symbolic reference is a local chained pointer,
# not an import; its descriptor belongs to PreviewRunnable.Configuration.
assert m.data[m.file_offset(0x546c82)]==2
assert 0x546c83+m.unpack('<i',m.file_offset(0x546c83))[0]==0x5ac3b8
assert m.unpack('<Q',m.file_offset(0x5ac3b8))[0]==0x10000000567218
assert m.string(m.relative(0x567218+8))=='Configuration' and m.relative(0x567218+16)==0x55aab8
assert m.string(m.relative(m.relative(0x567218+4)+8))=='PreviewRunnable'
# Capability metadata accessor and exact native field vector indices (0x10+4*i).
assert call(0x6f524)==0x26f1fc and word(0x6f52c)==0xf8100100 and word(0x6f8d8)==0xf8500118
assert word(0x6f924)==0xb9802308 and word(0x6f92c)==0x38686928
assert word(0x6f934)==0x54000a01 and word(0x6f904)==0x340001a0
assert word(0x6f908)==0x7100041f # live0 or continuous Bool -> interactive builder
assert word(0x6fa6c)==0x52800028 and word(0x6fa84)==0x39400268 and word(0x6fa8c)==0x1a9f17e8
assert word(0x6faa0)==0x39000128 and word(0x6faa4)==0xa900d534
assert word(0x6fab8)==0x52800021 # no variant (Optional.none)
assert call(0x6fb2c)==0x49c8 and call(0x6fb7c)==0x1f2cc
assert word(0x6fb80)==0xb9802708 and word(0x6fba0)==0x54000461 # static support controls remainder
assert word(0x6fc4c)==0x14000389 # no static support -> return
assert word(0x6fc64)==0x52800057 and word(0x6fc78)==0x52800042 and call(0x6fc88)==0x16d2a8
assert word(0x6fcb0)==0x370001b5 and word(0x6fcbc)==0xb4000148 # static mode OR no existing request
assert word(0x6fd38)==0x39000117 and word(0x6fd3c)==0xf9000514 and word(0x6fd48)==0xf9000914
assert word(0x6fd5c)==0x52800021 and call(0x6fe28)==0x1f2cc
assert call(0x6fee8)==0x520f3c and word(0x6feec)==0x7100041f # only grid continues
assert call(0x70614)==0x51e008 and binding(0x51e008)=='_$s21PreviewsMessagingHost19PreviewVariantGroupV21variantsConfigurationAA0d8VariantsH0VSgvg'
assert call(0x70664)==0x51e2c0 and binding(0x51e2c0)=='_$s21PreviewsMessagingHost28PreviewVariantsConfigurationV8sectionsSayAC7SectionVGvg'
assert call(0x706f8)==0x51e2a8 and binding(0x51e2a8)=='_$s21PreviewsMessagingHost28PreviewVariantsConfigurationV7SectionV8variantsSayAA0D7VariantVGvg'
assert word(0x70804)==0xb40011eb and word(0x708c0)==0x52800049 and word(0x708c4)==0x39000109
assert word(0x708d0)==0xa900e51b and word(0x708f4)==0x52800001 # static with a present variant
assert call(0x709b0)==0x1f2cc and word(0x709dc)==0xf100056b and word(0x709e0)==0x54fff2a1
assert word(0x70a70)==0xf85403a0
# DisplayMode payload bytes0/1 select interactive,2 selects static; injector tag1 writes2.
assert word(0x3c0994)==0x39400008 and word(0x3c0998)==0x7100091f and word(0x3c09a8)==0x1a8837e0
assert word(0x3c09bc)==0x11000428 and word(0x3c09c0)==0x39000008
assert word(0x5385a4)==0 and word(0x5385a8)==1 and word(0x53a830)==0 and word(0x53a834)==1
ranges=[]
for a,b,name in [(0x6f518,0x70b58,'admitted-request-builder.s'),(0x3c0994,0x3c09c8,'display-mode-witnesses.s')]:
 text=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(a),'--stop-address='+hex(b),str(m.path)],capture_output=True,text=True,check=True,timeout=20).stdout
 words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',text,re.M)};raw=m.data[m.file_offset(a):m.file_offset(a)+b-a];assert raw==b''.join(words[x] for x in range(a,b,4));(w/name).write_text(text);ranges.append({'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
out={'image_sha256':sha(m.data),'uuid':m.uuid,'ranges':ranges,'selected_source_bytes_verified':sum(x['bytes'] for x in ranges),'private_previewRequests_invoked':False,'scope':'post-admission ordered display mode/overrides/optional variant projection only; no full request or runtime parity','capability_field_indices':{'supportsContinuousLivePreview':4,'supportsStaticPreviews':5}}
(w/'source-findings.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
