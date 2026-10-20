from pathlib import Path
import json,struct,hashlib,sys
sha=lambda b:hashlib.sha256(b).hexdigest()
def body(a,b):
 assert len(a)==len(b)==48
 assert struct.unpack_from('<I',a)[0]==struct.unpack_from('<I',b)[0]==1
 assert int.from_bytes(a[4:8],'little')>0 and int.from_bytes(b[4:8],'little')>0
 assert a[8:14]==b[8:14]==bytes(6)
 assert a[14]==19 and b[14]==17 and a[15]==b[15]==0
 expected=bytes((17+i*37)&255 for i in range(32));assert a[16:]==b[16:]==expected
 normalized=bytearray(a);normalized[4:8]=b[4:8];normalized[14]=17;assert normalized==b
 return True
def verify(d):
 rows={};faults=0
 for mode in ['clean','abrupt','no-send']:
  p=d/mode;receipt=json.loads((p/'stdout.json').read_text());assert receipt['mode']==mode
  assert all(receipt[x] is True for x in ['ok','peer_reaped','rendezvous_removed','post_reap_queue_empty'])
  assert receipt['final_kernel_reclamation_proven'] is False
  if mode=='no-send':
   assert receipt['resource_read_after_peer_exit'] is False and not (p/'send.bin').exists() and not(p/'receive.bin').exists();rows[mode]={'reaped':True,'fresh_queue_empty':True};continue
  assert receipt['resource_read_after_peer_exit'] is True and receipt['port_released_before_second_read'] is True
  a=(p/'send.bin').read_bytes();b=(p/'receive.bin').read_bytes();body(a,b)
  content=(p/'content.bin').read_bytes();assert content==b'owned-cross-process-capability\x00'
  for off in [0,4,8,13,14,15,16,31,47]:
   bad=bytearray(b)
   if off==4:bad[4:8]=bytes(4)
   else:bad[off]^=1
   try:body(a,bad)
   except AssertionError:faults+=1
   else:raise AssertionError('accepted mutated frame')
  rows[mode]={'body_bytes':len(a),'sender_sha256':sha(a),'receiver_sha256':sha(b),'content_bytes':len(content),'content_sha256':sha(content),'all_bytes_compared_with_sdk_name_rebinding_and_disposition_rewrite':True}
 return {'cases':rows,'byte_faults_rejected':faults,'body_bytes_compared':96,'scope':'Owned public Mach/fileport peers; not native Canvas or XPC cross-process encoding; no final kernel reclamation claim'}
if __name__=='__main__':print(json.dumps(verify(Path(sys.argv[1])),indent=2))
