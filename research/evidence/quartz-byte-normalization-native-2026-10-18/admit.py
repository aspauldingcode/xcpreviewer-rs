"""Strict owned receipt/shape admission and two frozen-model byte comparisons."""
import hashlib,json,math,re,struct
from pathlib import Path
from phase_prerequisites import receipt,parsed,integer,require
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def admitted(root):
    root=Path(root);c=parsed((root/'compile-record.json').read_text());source=sha(root/'probe.swift');binary=c['binary_sha256']
    require(type(binary) is str and re.fullmatch('[0-9a-f]{64}',binary) is not None,'binary hash')
    for phase in ['compile','output-valid','fixture']:receipt(root,phase,source,binary)
    f=parsed((root/'fixture-record.json').read_text())
    require(f['args']==['--fixture',str(root/'owned-documents')],'fixture args')
    markers=re.findall(r'^owned_tree_pid:([1-9][0-9]*)$',f['record']['stderr'],re.M)
    require(len(markers)==1 and 1<int(markers[0])<=2147483647,'owned PID');pid=int(markers[0])
    rows=[parsed(x) for x in f['record']['stdout'].splitlines()];require(len(rows)==2,'row count')
    folder=root/'owned-documents';require({p.name for p in folder.iterdir()}=={'source.raw','phase0.raw','phase1.raw'},'files')
    for p in folder.iterdir():require(p.is_file() and not p.is_symlink(),'linked file')
    source_input=(root/'source-input.raw').read_bytes();require(len(source_input)==3120 and (folder/'source.raw').read_bytes()==source_input,'source bytes')
    expected={model:(root/('prospective-'+model+'.raw')).read_bytes() for model in ['division','reciprocal']}
    require(all(len(v)==16384 for v in expected.values()),'prediction geometry')
    buffers=[];results=[]
    for phase,row in enumerate(rows):
        require(set(row)=={'pid','phase','file','width','height','stride','allocation_bytes','sha256','color_space','bitmap_info','source_sha256'},'fields')
        require(all(integer(row[k]) for k in ['pid','phase','width','height','stride','allocation_bytes','bitmap_info']),'typed metadata')
        require([row[k] for k in ['pid','phase','width','height','stride','allocation_bytes','bitmap_info']]==[pid,phase,256,3,4112,16384,8449],'geometry')
        require(row['color_space']=='kCGColorSpaceLinearSRGB' and row['file']=='phase%d.raw'%phase,'identity')
        require(row['source_sha256']==hashlib.sha256(source_input).hexdigest(),'source hash')
        data=(folder/row['file']).read_bytes();require(len(data)==16384 and hashlib.sha256(data).hexdigest()==row['sha256'],'output hash')
        for y in range(3):
            for x in range(256):
                pixel=struct.unpack('<4f',data[y*4112+x*16:y*4112+x*16+16])
                require(all(math.isfinite(v) and 0<=v<=1 for v in pixel) and pixel[3]==1,'visible domain')
            require(data[y*4112+4096:y*4112+4112]==b'\xa5'*16,'padding')
        require(data[12336:]==b'\xa5'*4048,'tail')
        results.append({'phase':phase,'allocation_bytes_compared':16384,'model_mismatch_bytes':{model:sum(a!=b for a,b in zip(data,v)) for model,v in expected.items()}});buffers.append(data)
    require(buffers[0]==buffers[1],'A/A repeat')
    return {'measurement_receipts_admitted':True,'source_bytes_compared':3120,'output_bytes_compared':32768,'padding_bytes':96,'tail_bytes':8096,'results':results,'native_cause_proven':False,'canvas_qualified':False,'scope':'Owned public same-space Quartz conversion; frozen byte models may both fail'}
if __name__=='__main__':print(json.dumps(admitted(Path(__file__).parent)))
