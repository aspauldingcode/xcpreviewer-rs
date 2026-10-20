from pathlib import Path
import json,struct,re,subprocess,hashlib
w=Path(__file__).parent;path=Path('/Users/8amps/xcpreviewer-rs/research/raw/reply-route-20261020/mapped/libxpc-mapped-v2.elf');b=path.read_bytes();assert hashlib.sha256(b).hexdigest()=='be92683dd727339d21ad82f4d3624e97757c327a4387172fc1a7d4acef5417fc';off=struct.unpack_from('<Q',b,32)[0];n=struct.unpack_from('<H',b,56)[0];sz=struct.unpack_from('<H',b,54)[0];segs=[struct.unpack_from('<IIQQQQQQ',b,off+j*sz)for j in range(n)]
def at(a,n):
 for typ,flags,fo,va,pa,fs,ms,align in segs:
  if typ==1 and va<=a and a+n<=va+fs:return b[fo+a-va:fo+a-va+n]
 raise AssertionError('unmapped')
bundle=json.load(open(w/'rea-libxpc.json'));records=[x['normalized_result']for x in bundle['records']if x['operation']=='analyze_function'];assert len(records)==5
ranges=[]
for d in records:
 p=d['procedure'];expected=set()
 for region in p['body']['ranges']:expected.update(range(int(region['start'],16),int(region['end'],16)+1,4))
 assert{int(x.split(':')[0],16)for x in d['assembly']}==expected
 out=subprocess.check_output(['xcrun','llvm-objdump','-d','--start-address='+hex(min(expected)),'--stop-address='+hex(max(expected)+4),str(path)],timeout=10);(w/(p['address']+'.s')).write_bytes(out);llvm={int(a,16):int(h,16)for a,h in re.findall(rb'^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s',out,re.M)}
 for a in expected:assert struct.unpack('<I',at(a,4))[0]==llvm[a]
 ranges.append((p,expected))
s=(w/'sdk-entry.c').read_text().replace('int main(void)','int main(int argc,char**argv)').replace('Dl_info d={0};','if(argc!=2)return 6;Dl_info d={0};')
start=s.index('printf("{');s=s[:start]+'''const unsigned offsets[]={OFFSETS};const unsigned sizes[]={SIZES};for(unsigned i=0;i<5;i++){if(offsets[i]+sizes[i]>345440)return 7;char name[1024];if(snprintf(name,sizeof(name),"%s/%u.bin",argv[1],offsets[i])>=(int)sizeof(name))return 8;FILE*f=fopen(name,"wb");if(!f)return 9;if(fwrite((char*)d.dli_fbase+offsets[i],1,sizes[i],f)!=sizes[i])return 10;fclose(f);}return 0;}\n'''
# Offsets are exact REA entries minus the pinned mapped Mach-O header base.
s=s.replace('OFFSETS',','.join(str(int(p['address'],16)-0x18d99b000)for p,_ in ranges)).replace('SIZES',','.join(str(len(expected)*4)for _,expected in ranges))
(w/'native-code.c').write_text(s)
p=subprocess.run(['/usr/bin/clang','-Wall','-Wextra','-Werror',str(w/'native-code.c'),'-o',str(w/'native-code')],capture_output=True,timeout=30);(w/'native-code.build').write_bytes(p.stdout+p.stderr);p.check_returncode()
outdir=w/'native-code-bytes';outdir.mkdir(exist_ok=True);p=subprocess.run([str(w/'native-code'),str(outdir)],capture_output=True,timeout=5);(w/'native-code.log').write_bytes(p.stdout+p.stderr);p.check_returncode()
proof=[]
for p,expected in ranges:
 entry=int(p['address'],16);native=(outdir/(str(entry-0x18d99b000)+'.bin')).read_bytes();actual=b''.join(at(a,4)for a in sorted(expected));assert native==actual
 proof.append({'entry':p['address'],'ranges':p['body']['ranges'],'body_bytes':len(native),'sha256':hashlib.sha256(native).hexdigest(),'native_ELF_LLVM_equal':True})
assert sum(x['body_bytes']for x in proof)==1412
prefix=json.load(open(w/'sdk-entry.json'));assert prefix['uuid']=='c40fcae87a173d8287cb3da4802adef1' and prefix['offset']==54636 and bytes.fromhex(prefix['prefix32_hex'])==at(0x18d9a856c,32)
print(json.dumps({'bodies':proof,'native_ELF_LLVM_bytes_verified':1412,'libxpc_uuid':prefix['uuid'],'mapped_sha256':hashlib.sha256(b).hexdigest(),'SDK_entry_prefix_equal':True,'private_entrypoints_called':False,'runtime_dispatch_result_or_disposal_branch_not_observed':True},indent=2))
