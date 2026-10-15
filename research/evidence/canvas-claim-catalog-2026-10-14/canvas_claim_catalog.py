"""Exact-span candidate extraction for independent review, never acceptance or fusion."""
import argparse,hashlib,json,re
from pathlib import Path
from canvas_graph import ROOT,safe,sha,read


def catalog(root,graph,per_document=5):
 root=Path(root).resolve()
 if type(per_document) is not int or not 1<=per_document<=10:raise ValueError('Bounded document sample required')
 evidence=[n for n in graph['knowledge']['nodes'] if n['type']=='Evidence']
 if not evidence or len(evidence)>32:raise ValueError('Evidence pilot scope limit')
 rows=[];seen=set()
 for node in evidence:
  ref=node['provenance'];path=safe(root,ref['path'])
  if path.stat().st_size>1048576 or sha(path)!=ref['sha256']:raise ValueError('Source changed or oversized')
  text=path.read_text();candidates=[];in_code=False
  # Paragraphs/sentences are candidates for human interpretation, not semantic facts.
  for block in re.finditer(r'[^\n]+(?:\n(?!\n)[^\n]+)*',text):
   value=block.group()
   if value.lstrip().startswith(('```','~~~')):
    fences=sum(line.lstrip().startswith(('```','~~~')) for line in value.splitlines())
    if fences%2:in_code=not in_code
    continue
   if in_code or value.lstrip().startswith(('#','|','```')):continue
   for sentence in re.finditer(r'.+?(?:[.!?](?=\s+[A-Z]|$)|$)',value,re.DOTALL):
    quote=sentence.group().strip()
    if not 40<=len(quote)<=2048:continue
    start=block.start()+sentence.start()+len(sentence.group())-len(sentence.group().lstrip());end=start+len(quote)
    assert text[start:end]==quote
    key=(node['scope'],node['target_version'],re.sub(r'\s+',' ',quote).lower())
    if key in seen:continue
    seen.add(key);candidates.append({'id':hashlib.sha256(json.dumps(key).encode()).hexdigest(),'source_node':node['id'],'source_path':ref['path'],'source_sha256':ref['sha256'],'char_span':[start,end],'line_span':[text.count('\n',0,start)+1,text.count('\n',0,end)+1],'quote':quote,'scope':node['scope'],'target_version':node['target_version'],'source_grade':node['grade'],'assertion_level':'document-statement-only','semantic_review':'pending','qualified_for_acceptance':False})
    if len(candidates)==per_document:break
   if len(candidates)==per_document:break
  if len(candidates)!=per_document:raise ValueError('Not enough eligible statements: '+ref['path'])
  rows.extend(candidates)
 return {'schema_version':1,'pilot_documents':len(evidence),'per_document':per_document,'statement_candidates':len(rows),'records':rows,'extraction':'Deterministic exact-span document statements; no automatic semantic support edges or fusion','quality_gate':{'required_reviewed_items':50,'required_precision':0.9,'independently_reviewed':0,'precision':None,'passed':False},'task_accepted':False,'handoff_approved':False}


def verify_catalog(root,result):
 sources={n['id']:n for n in read(Path(root)/'research/loop/canvas-graph.json')['knowledge']['nodes'] if n['type']=='Evidence'}
 rows=result['records'];assert len(rows)==result['statement_candidates'] and len({r['id'] for r in rows})==len(rows)
 assert result['pilot_documents']==len(sources) and type(result['per_document']) is int and 1<=result['per_document']<=10
 assert len(rows)==len(sources)*result['per_document'] and all(sum(r['source_node']==key for r in rows)==result['per_document'] for key in sources)
 for row in rows:
  source=sources[row['source_node']];assert row['source_path']==source['provenance']['path'] and row['source_sha256']==source['provenance']['sha256'] and row['scope']==source['scope'] and row['target_version']==source['target_version'] and row['source_grade']==source['grade']
  p=safe(root,row['source_path']);assert sha(p)==row['source_sha256'];text=p.read_text();start,end=row['char_span'];assert type(start) is type(end) is int and 0<=start<end<=len(text) and text[start:end]==row['quote']
  assert row['line_span']==[text.count('\n',0,start)+1,text.count('\n',0,end)+1]
  key=(row['scope'],row['target_version'],re.sub(r'\s+',' ',row['quote']).lower());assert row['id']==hashlib.sha256(json.dumps(key).encode()).hexdigest()
  assert row['assertion_level']=='document-statement-only' and row['semantic_review']=='pending' and row['qualified_for_acceptance'] is False
 assert result['quality_gate']=={'required_reviewed_items':50,'required_precision':0.9,'independently_reviewed':0,'precision':None,'passed':False}
 assert result['task_accepted'] is result['handoff_approved'] is False
 return {'literal_spans_verified':len(rows),'semantic_precision':None,'quality_gate_passed':False}


if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=ROOT);args=parser.parse_args();print(json.dumps(catalog(args.root,read(args.root/'research/loop/canvas-graph.json')),indent=2))
