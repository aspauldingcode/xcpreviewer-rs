"""Frozen control consistency check; no processes, UI actions or integration."""
import copy,json
from pathlib import Path

def verify(record,peer):
    def need(ok):
        if not ok:raise ValueError('Control receipt mismatch')
    need(type(record.get('returncode')) is int and record['returncode']==0)
    rows=[json.loads(s) for s in record['stdout'].splitlines()]
    need(len(rows)==4 and len(record['requests'])==4 and len(peer)==3)
    need([x.get('id') for x in rows]==[1,2,3,4])
    for i,(op,forwarded) in enumerate([('click','PRESS'),('press','PRESS'),('CLICK','CLICK')]):
        q=record['requests'][i+1];args=q['params']['arguments'];p=peer[i]['request'];r=rows[i+1]['result'];v=r['structuredContent']
        need(q['id']==i+2 and q['method']=='tools/call' and q['params']['name']=='computer_act')
        need(args=={'target':'ax-owned-mock','op':op,'ref':'ax:0.0','label':'Owned sentinel '+op})
        need(p=={'app':'ax-owned-mock','expect':args['label'],'expect_role':'','id':i+1,'key':'','menu':'','method':'act','op':forwarded,'path':'0.0','text':''})
        need(type(r['isError']) is bool and r['isError']==(i<2))
        need(len(r['content'])==1 and r['content'][0]['type']=='text' and json.loads(r['content'][0]['text'])==v)
        if i<2:need(v['ok'] is False and v['error']=='MOCK: element offers CLICK but no AXPress')
        else:need(v['ok'] is True and v['result']=={'mock_only':True,'forwarded':'CLICK'})
    return {'frozen_receipts_consistent':True,'scope':'UCU disk binary with mocked bridge; no native input'}

if __name__=='__main__':
    root=Path(__file__).parent;record=json.loads((root/'stdio.json').read_text());peer=[json.loads(s) for s in (root/'mock-requests.jsonl').read_text().splitlines()]
    result=verify(record,peer);rejected=[]
    for name in ['wrong_op','wrong_label','wrong_peer_id','missing_ack','changed_request','nonzero_exit']:
        a=copy.deepcopy(record);b=copy.deepcopy(peer)
        if name=='wrong_op':b[0]['request']['op']='CLICK'
        elif name=='wrong_label':b[1]['request']['expect']='Other window'
        elif name=='wrong_peer_id':b[2]['request']['id']=9
        elif name=='missing_ack':
            rows=[json.loads(s) for s in a['stdout'].splitlines()];rows[-1]['result']['structuredContent']['result']={};rows[-1]['result']['content'][0]['text']=json.dumps(rows[-1]['result']['structuredContent']);a['stdout']='\n'.join(json.dumps(s) for s in rows)
        elif name=='changed_request':a['requests'][1]['params']['arguments']['target']='Xcode'
        else:a['returncode']=1
        try:verify(a,b)
        except (ValueError,KeyError):rejected.append(name)
        else:raise RuntimeError('Mutation accepted: '+name)
    print(json.dumps({'result':result,'rejected':rejected},indent=2))
