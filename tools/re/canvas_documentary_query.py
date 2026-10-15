"""Read-only bounded documentary retrieval, never a truth/native acceptance service."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from canvas_entity_pilot import documentary_relations

PINS = {'typed-pilot-v3-2026-10-15.json': '796d91cd547cc1ddccef9f3ce1c1f145de4b49b41b23111f070bc649b8a245bb', 'typed-pilot-v3-independent-review-2026-10-15.json': 'db8cd660d72dbfdb5bd84a09598b43d6db9bdefaac99d4739675c350d7e5a176', 'documentary-asserts-v3-candidates-2026-10-15.json': 'dab3a21d59b8a07ac0d0b8eb5acd4df8db6fbebd3e57bdcd98263e4adac6949f', 'documentary-asserts-v3-independent-review-2026-10-15.json': '37c8d4121bdcc9caa3418da5c5bbc152b7b090a844f7ae710a5c03fae72312b4'}
NAMES = list(PINS)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def fuse_entities(entities):
    """Only exact occurrence aliases merge; all original IDs/provenance survive."""
    groups={}
    for row in entities:
        key=(row['source_sha256'],tuple(row['char_span']),row['proposed_type'],row['scope'],
             row['source_path'],row['source_grade'],json.dumps(row.get('target_identity'),sort_keys=True),
             json.dumps(row.get('target_version'),sort_keys=True))
        if key not in groups:
            groups[key]={'quote':row['surface_form'],'source_sha256':row['source_sha256'],
                         'char_span':row['char_span'],'type':row['proposed_type'],
                         'scope':row['scope'],'grade':row['source_grade'],'original_ids':[],
                         'provenance':[]}
        item=groups[key]
        for field in ('target_identity','target_version'):
            if field in row:item[field]=row[field]
        if item['quote']!=row['surface_form']:
            raise ValueError('Conflicting exact occurrence aliases')
        item['original_ids'].append(row['id'])
        item['provenance'].append({'id':row['id'],'source_path':row['source_path'],
                                   'line_span':row['line_span']})
    return list(groups.values())

def load_reviewed(root):
    blobs={}
    for name, pin in PINS.items():
        raw=(root/'research/canvas-reviews'/name).read_bytes()
        if sha(raw)!=pin:raise ValueError('Artifact/review pin mismatch: '+name)
        blobs[name]=raw
    entities,entity_review,relations,relation_review=[json.loads(blobs[n]) for n in NAMES]
    # Revalidate independently reviewed endpoints against current source bytes and ontology.
    regenerated=documentary_relations(root,blobs[NAMES[0]],blobs[NAMES[1]],PINS[NAMES[1]])
    if regenerated['candidates']!=relations['candidates']:
        raise ValueError('Changed relation endpoint/source binding')
    if (relation_review.get('candidate_sha256')!=PINS[NAMES[2]] or
            relation_review.get('endpoint_candidate_sha256')!=PINS[NAMES[0]] or
            relation_review.get('endpoint_review_sha256')!=PINS[NAMES[1]] or
            relation_review.get('independent_of_edge_generation') is not True or
            relation_review.get('truth_entailment') is not False or
            relation_review.get('ontology_sha256')!=regenerated['ontology_sha256']):
        raise ValueError('Relation review binding mismatch')
    judgments={r['id']:r for r in relation_review['rows']}
    if len(judgments)!=len(relation_review['rows']) or set(judgments)!={r['id'] for r in relations['candidates']}:
        raise ValueError('Missing/duplicate relation judgments')
    for edge in relations['candidates']:
        j=judgments[edge['id']]
        if (j.get('verdict')!='accept' or j.get('eligible') is not True or j.get('repair_applied') is not False or
                j.get('original_prediction')!=edge or not j.get('checks') or any(v is not True for v in j['checks'].values()) or
                edge['relation']!='ASSERTS' or edge['accepted_graph_edge'] is not False):
            raise ValueError('Unreviewed or promoted documentary edge')
    return {'entities':entities['candidates'],'edges':relations['candidates'],
            'bindings':dict(PINS),'relation_review_context':relation_review['reviewer_context']}

def query(data, text, limit=5):
    if type(limit) is not int or not 1<=limit<=20:raise ValueError('limit must be integer1..20')
    if not isinstance(text,str) or len(text)>128:raise ValueError('query must be <=128 characters')
    tokens=re.findall(r'\w+',text.casefold())
    if not tokens or len(tokens)>8:raise ValueError('query requires1..8 tokens')
    matches=[]
    for row in fuse_entities(data['entities']):
        words=re.findall(r'\w+',row['quote'].casefold())
        if not all(any(word.startswith(token) for word in words) for token in tokens):continue
        edges=[e for e in data['edges'] if e['to'] in row['original_ids'] or e['from'] in row['original_ids']]
        matches.append({**row,'documentary_edges':[{'id':e['id'],'relation':'ASSERTS','from':e['from'],'to':e['to']} for e in edges]})
    return {'query':text,'filter':'AND of casefolded token prefixes; no semantic matching',
            'matched':len(matches),'truncated':len(matches)>limit,'results':matches[:limit],
            'bindings':data['bindings'],'truth_entailment':False,'native_acceptance':False,
            'global_graph_acceptance':False,'relation_meaning':'ASSERTS = report states proposition; SUPPORTS not returned or inferred'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('query');p.add_argument('--limit',type=int,default=5)
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2]);a=p.parse_args()
    print(json.dumps(query(load_reviewed(a.root),a.query,a.limit),indent=2))
