from pathlib import Path
import sys,struct,hashlib,json,subprocess,re
r=Path('/Users/8amps/xcpreviewer-rs');w=Path(__file__).parent;sys.path.insert(0,str(r/'tools/re'))
from reloop.cachebind import Cache,export_names
c=Cache('/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld');base=0x263300000;trie,uuid=c.exports(base);assert uuid=='fffb683f59433c2591b272d6e5174fa3';data=c.read(base,0x10440);sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(data)=='d52bb808c85bf5067dc936655a9dfe5ee75d54f544c1beb923195c520af9b3a3'
def branch(a):
 v=struct.unpack_from('<I',data,a-base)[0];assert v>>26 in [5,37];n=v&0x3ffffff;return a+4*(n-(1<<26) if n&(1<<25) else n)
assert branch(base+0x9aec)==base+0x8800
info=c.stub(branch(base+0x88a4));path,b,_=c.image(info['target']);t,u=c.exports(b);names=export_names(t,info['target']-b);assert '_xpc_connection_enable_sim2host_4sim' in [x['name'] for x in names]
for off,name in [(0x9abc,'_$s16PreviewsServices0A17ServiceConnectionC09hostToSimD0ACSo13OS_xpc_object_p_tcfC'),(0xb080,'_$s16PreviewsServices0A17ServiceConnectionCMa'),(0xa150,'_$s16PreviewsServices0A17ServiceConnectionC8activate8receiveryAA0aC15MessageReceiver_pSg_tF'),(0xa230,'_$s16PreviewsServices0A17ServiceConnectionC4send7message12replyHandlerySo14UVPropertyListC_yAHSg_s5Error_pSgtctF')]:assert name in [x['name'] for x in export_names(trie,off)]
assert struct.unpack_from('<I',data,0x9af8)[0]==0x52800401 and struct.unpack_from('<I',data,0x88ac)[0]==0x52800e01
# Independently verify selected source instructions via the previously retained
# non-executed analysis wrapper; it is never linked, loaded or published.
image=r/'research/raw/service-connection-lifecycle-20261024/analysis.macho';ranges=[]
for a,b,name in [(0x9abc,0x9b94,'factory.s'),(0x8800,0x88c8,'inner-factory.s'),(0xa150,0xa20c,'activate.s'),(0xa230,0xa254,'send-wrapper.s')]:
 p=subprocess.run(['xcrun','llvm-objdump','--disassemble','--start-address='+hex(base+a),'--stop-address='+hex(base+b),str(image)],capture_output=True,text=True,check=True,timeout=20).stdout;words={int(x,16):int(y,16).to_bytes(4,'little') for x,y in re.findall(r'^\s*([0-9a-f]+):\s*([0-9a-f]{8})\s',p,re.M)};raw=data[a:b];assert raw==b''.join(words[x] for x in range(base+a,base+b,4));(w/name).write_text(p);ranges.append({'start':hex(a),'bytes':b-a,'sha256':sha(raw)})
result={'services_uuid':uuid,'services_text_sha256':sha(data),'ranges':ranges,'source_bytes':sum(x['bytes'] for x in ranges),'factory_operation':'xpc_connection_enable_sim2host_4sim','operation_image':path,'operation_image_uuid':u,'operation_export':'_xpc_connection_enable_sim2host_4sim','scope':'Actual factory invokes simulator transport operation. Ordinary owned local endpoint fails in native wrapper while SDK baseline works. Simulator operation is a context distinction, not proven sole cause. No code/system protection or peer-signing policy changed.'};(w/'source-findings.json').write_text(json.dumps(result,indent=2)+'\n');print(result['source_bytes'])
