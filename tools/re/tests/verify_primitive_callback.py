import hashlib
import json
from pathlib import Path


def verify(folder):
    e=Path(folder);manifest=json.loads((e/'manifest.json').read_text())
    assert set(manifest['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p.name!='manifest.json'}
    for name,item in manifest['files'].items():
        assert not Path(name).is_absolute() and '..' not in Path(name).parts
        p=e/name;raw=p.read_bytes();assert not p.is_symlink() and len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
    pins={'before':'417d121a6181d060f96a944ba6fe1b03b8b22c3ddc161f866f1bf6a420e7ad93','after':'0b786699d5d3759ad6ef30e584ff8a6a3a42ae73a023e6e91504c254beadd631'}
    messages={'string':'owned primitive','zero':'0','false':'false','null':'null','undefined':'undefined','empty':'','bigint':'17','symbol':'Symbol(owned)','opaque':'Observed non-Error failure','error':'owned error','frozen':'owned frozen','readonly':'owned readonly'}
    broken={'string','bigint','symbol','frozen','readonly'}
    for phase in ['before','after']:
        assert hashlib.sha256((e/(phase+'.js')).read_bytes()).hexdigest()==pins[phase]
        assert json.loads((e/(phase+'-wait.json')).read_text())=={'code':0,'timeout':False,'stdout':'','stderr':''}
        rows=json.loads((e/(phase+'-results.json')).read_text());assert [r['name'] for r in rows]==list(messages)
        for row in rows:
            name=row['name'];assert row['writes']==['abort\n'] and row['kills']==[{'pid':-900001,'signal':'SIGKILL'}]
            if phase=='before' and name in broken:
                assert row['settled'] is False and row['closeThrow']['name']=='TypeError' and row['error'] is row['record'] is None
                continue
            assert row['settled'] is True and row['closeThrow'] is None
            if phase=='before' and name=='opaque':assert row['error']=={'originalIdentity':True}
            else:
                message=messages[name] if phase=='after' or name=='error' else 'Observed compiler failed: abort'
                assert row['error']=={'name':'Error','message':message,'originalIdentity':name=='error'}
            record=row['record'];assert record['privateAbortRequested'] is True and record['emergencyClosed'] is False and record['signal']=='SIGKILL'
            assert record['pid']==900001 and record['anchorCode'] is None
            for stream in ['stdout','stderr']:
                assert record[stream]=='' and record[stream+'Bytes']==0 and record[stream+'Sha256']==hashlib.sha256(b'').hexdigest()
            assert record['report']=={'kind':'complete','drained':True,'target_code':43,'failure':'abort','observations':1,'tracked':0,'remaining_observed':0,'scope':'Injected source control, no native process'}
    assert json.loads((e/'source-slots.json').read_text())==json.loads((e/'native-slots.json').read_text())=={'used':2,'limit':2}
    rea=json.loads((e/'current-rea.json').read_text());cfg=json.loads((e/'config.json').read_text())
    assert rea['target']['sha256']==cfg['observer']['sha256']=='718c0dd47aaa6598281d0f0afb7dd12fa4c497a8494897b24829905de82ecda5'
    assert rea['target']['architecture']=='arm64' and rea['server']['version']=='6.2.0'
    for mode,message in [('string','Owned primitive native callback failure'),('false','false')]:
        root=e/('native-'+mode);d=json.loads((root/'result.json').read_text());r=d['record'];p=r['report'];child=d['trigger']['child'];ready=d['trigger']['ready']
        assert d['index']==mode and d['normalizedOriginal'] is True and d['error']=='Error: '+message
        assert r['privateAbortRequested'] is True and r['emergencyClosed'] is False and r['signal']=='SIGKILL'
        assert p['drained'] is True and p['failure']=='abort' and p['target_code']==43 and p['remaining_observed']==0 and p['tracked']==2
        assert any(child==row for batch in d['observed'] for row in batch)
        assert child['pid']==ready['child_pid'] and child['group']==child['pid'] and child['parent']==ready['parent_pid'] and child['state']=='L'
        assert ready['child_ack']=='ready' and ready['parent_group']==r['pid'] and child['identity'][0]>0 and 0<=child['identity'][1]<1000000
        wait=json.loads((root/'child-wait.json').read_text());assert wait=={'pid':child['pid'],'raw_status':42<<8,'exited':True,'exit_code':42}
        assert (root/'child.raw').read_bytes()==bytes([0,1,2,255,10,42,99,128])
        assert json.loads((e/('native-'+mode+'-wait.json')).read_text())=={'code':0,'stdout':'owned primitive callback native pass\n','stderr':'','timeout':False}
        for stream in ['stdout','stderr']:
            assert r[stream]=='' and r[stream+'Bytes']==0 and r[stream+'Sha256']==hashlib.sha256(b'').hexdigest()
    return {'source_cases':24,'owned_native_jobs':2,'controlled_child_bytes':16,'primitive_failure_preserved':True,'immutable_error_wrapped':True,'ordinary_error_identity_preserved':True,'async_callback_qualified':False,'native_canvas_protocol_qualified':False}
