"""Link pinned report documents to sealed artifacts; never grants semantic acceptance."""
import argparse,hashlib,json,re
from pathlib import Path
from canvas_graph import ROOT,read,safe,sha

class BudgetExceeded(ValueError):pass

def crosswalk(root,graph,max_bytes=134217728):
 root=Path(root).resolve();base=root/'research/evidence';used=0
 def charge(size):
  nonlocal used
  if size<0 or used+size>max_bytes:raise BudgetExceeded('Crosswalk read byte limit')
  used+=size
 manifests=sorted(base.glob('*/manifest.json'))
 if len(manifests)>1024:raise ValueError('Manifest index count limit')
 index={};skipped=[]
 for p in manifests:
  name=str(p.relative_to(root))
  try:
   safe(root,name)
   if p.stat().st_size>1048576:raise ValueError('Manifest index file limit')
   charge(p.stat().st_size)
   index.setdefault(sha(p),[]).append(name)
  except BudgetExceeded:raise
  except (OSError,ValueError) as error:skipped.append({'path':name,'reason':str(error)})
 if used>max_bytes:raise ValueError('Crosswalk byte limit')
 documents=[];verified_cache={}
 for node in graph['knowledge']['nodes']:
  if node['type']!='Evidence':continue
  ref=node['provenance'];p=safe(root,ref['path'])
  charge(2*p.stat().st_size)
  if p.stat().st_size>1048576 or sha(p)!=ref['sha256']:raise ValueError('Changed report')
  text=p.read_text();direct={m.group(1) for m in re.finditer(r'(research/evidence/[A-Za-z0-9._-]+)(?:/manifest\.json)?',text)}
  paths={name+'/manifest.json' for name in direct}
  for mentioned in set(re.findall(r'\b[0-9a-f]{64}\b',text)):paths.update(index.get(mentioned,[]))
  if len(paths)>32:raise ValueError('Document reference count limit')
  links=[]
  for name in sorted(paths):
   if name not in verified_cache:
    try:
     manifest_path=safe(root,name)
     if manifest_path.stat().st_size>1048576:raise ValueError('Manifest file limit')
     charge(2*manifest_path.stat().st_size);seal=sha(manifest_path);m=read(manifest_path);files=m['files']
     if not isinstance(files,dict) or not files or len(files)>16384:raise ValueError('Invalid manifest file inventory')
     total=0
     for item,row in files.items():
      artifact=safe(manifest_path.parent,item);size=artifact.stat().st_size;charge(size);total+=size
      if size!=row['bytes'] or sha(artifact)!=row['sha256']:raise ValueError('Artifact mismatch: '+item)
     actual={str(q.relative_to(manifest_path.parent)) for q in manifest_path.parent.rglob('*') if q.is_file() and q!=manifest_path}
     if actual!=set(files):raise ValueError('Manifest completeness mismatch')
     verified_cache[name]={'path':name,'sha256':seal,'bytes_verified':True,'files':len(files),'artifact_bytes':total}
    except BudgetExceeded:raise
    except (OSError,ValueError,KeyError,TypeError) as error:
     verified_cache[name]={'path':name,'bytes_verified':False,'error':type(error).__name__+': '+str(error)}
   result={**verified_cache[name]};result['document_mentions_seal']=result.get('sha256') in text if result.get('sha256') else False;result['semantic_review_complete']=False;result['qualified_for_acceptance']=False;links.append(result)
  documents.append({'source_node':node['id'],'source_path':ref['path'],'source_sha256':ref['sha256'],'grade':node['grade'],'scope':node['scope'],'target_version':node['target_version'],'links':links,'resolution':'resolved' if links else 'unresolved; no path/hash link found','semantic_review_complete':False})
 return {'schema_version':1,'documents':documents,'manifest_index':{'indexed':sum(map(len,index.values())),'skipped':skipped},'unique_manifests':len(verified_cache),'charged_read_bytes':used,'limits':{'manifests':1024,'links_per_document':32,'file_inventory':16384,'read_bytes':max_bytes},'native_execution':False,'independent_semantic_review_complete':False,'task_accepted':False,'handoff_approved':False}


if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);args=p.parse_args();print(json.dumps(crosswalk(args.root,read(args.root/'research/loop/canvas-graph.json')),indent=2))
