"""Conservative report entity producer; never emits accepted graph records."""
import argparse
import datetime
import hashlib
import json
import re
from pathlib import Path

EVENT_KINDS = frozenset({'request', 'render', 'completion', 'cancellation', 'release'})
IDENTITY_TYPES = frozenset({'Event', 'Frame', 'Resource', 'Session', 'Target'})
GROUP = re.compile(r'\b(?:both|each|two|three|multiple|helpers|processes|repeats|controls|baseline and repeat)\b', re.I)
FRAMING = re.compile(r'^(?:Next:|Evidence:|REA|This controlled experiment extends|This changes|Unlike|The previous|The cross-task probe|This fresh control|The SDK declaration|The pinned header)', re.I)
ASSERTION = re.compile(r'\b(?:is|are|has|have|hosts|captures|occurs|passes|changes|starts|retains|remain|remains|report|reports|adds|gains|observes|skips|reads|must|exposes|keeps|creates|clears|send|sends|reject|rejects|return|returns|escaped|accepts|supported|qualifies|does|do|become|becomes|produces|sets|preserve|preserves)\b', re.I)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def validate_role(kind, *, context, identity=None, timestamp=None, event_kind=None):
    """Identity roles need a selected occurrence; group context cannot name one entity."""
    if kind in IDENTITY_TYPES:
        if GROUP.search(context) or not identity:
            return False
        if kind == 'Event':
            if event_kind not in EVENT_KINDS or not timestamp:
                return False
            try:
                parsed = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                return False
            if parsed.tzinfo is None:
                return False
    return kind in {'Evidence', 'Claim'} | IDENTITY_TYPES

def sentence_spans(text):
    # Keep offsets in original text; no normalization that shifts Unicode/newline spans.
    for paragraph in re.finditer(r'[^\n]+(?:\n(?!\n)[^\n]+)*', text):
        if paragraph.group().startswith('#'):
            continue
        for match in re.finditer(r'\S[\s\S]*?(?:[.!?](?=\s|$)|$)', paragraph.group()):
            start, end = paragraph.start()+match.start(), paragraph.start()+match.end()
            while end > start and text[end-1].isspace():
                end -= 1
            quote = text[start:end]
            if quote:
                yield start, end, quote

def extract_document(path, raw, expected_sha256, claim_limit=4):
    if digest(raw) != expected_sha256:
        raise ValueError('Source digest mismatch: '+str(path))
    text = raw.decode('utf-8')
    if not text.startswith('# '):
        raise ValueError('Expected report title')
    title_end = text.find('\n')
    if title_end < 0:
        title_end = len(text)
    selected = [('Evidence', 2, title_end)]
    seen = set()
    for start, end, quote in sentence_spans(text):
        normalized = ' '.join(quote.split())
        # A Claim is the report's asserted proposition, not a true runtime fact.
        # Exclude headings, instructions, questions, fragments and historical framing.
        if (quote[-1:] != '.' or not 30 <= len(quote) <= 650 or
                FRAMING.search(normalized) or '?' in quote or
                not ASSERTION.search(normalized) or normalized in seen):
            continue
        seen.add(normalized)
        selected.append(('Claim', start, end))
        if len(selected)-1 >= claim_limit:
            break
    records=[]
    for kind, start, end in selected:
        records.append({'prediction_kind':'entity','proposed_type':kind,
                        'surface_form':text[start:end], 'char_span':[start,end],
                        'line_span':[text.count('\n',0,start)+1,text.count('\n',0,end)+1],
                        'source_path':str(path),'source_sha256':expected_sha256,
                        'semantic_key_proposal':str(path)+'#'+str(start)+':'+kind,
                        'scope':'Documentary report assertion only; historical owned fixture; no native Canvas parity',
                        'assertion_level':'report-identity' if kind=='Evidence' else 'report-proposition-not-truth',
                        'domain':None,'range':None,'domain_range_reason':'Entity prediction; relation endpoints not asserted',
                        'review_status':'pending separate verifier','accepted_graph_entity':False})
    return records

def produce(root):
    ontology=json.loads((root/'research/loop/canvas-ontology.json').read_text())
    graph=json.loads((root/'research/loop/canvas-graph.json').read_text())
    documents=[n for n in graph['knowledge']['nodes'] if n['type']=='Evidence'][:10]
    if len(documents)!=10:
        raise ValueError('Expected ten pinned report nodes')
    records=[]
    for node in documents:
        provenance=node['provenance']; path=Path(provenance['path'])
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('Unsafe report path')
        extracted=extract_document(path,(root/path).read_bytes(),provenance['sha256'])
        for row in extracted:
            row.update(id='typed-pilot-v2-'+str(len(records)+1).zfill(3),
                       ontology_definition=ontology['entity_types'][row['proposed_type']],
                       source_grade=node['grade'])
            records.append(row)
    return {'schema_version':2,'producer_context':'/root/canvas_evidence_review',
            'method':'automatic conservative title and declarative Claim mention extraction',
            'round':1,'maximum_rounds':1,'candidates':records,
            'entity_predictions':len(records),'relation_predictions':0,
            'independently_reviewed':0,'precision':None,'quality_gate_passed':False,
            'development_set_reuse':True,'held_out':False,
            'type_coverage':['Evidence','Claim'],
            'limitations':['No runtime identity roles extracted from report prose',
                           'Grammar heuristic does not verify proposition truth',
                           'Same ten development reports; no held-out or global precision claim',
                           'Relation extraction deferred until entity review'],
            'native_canvas_parity':False,'handoff_approved':False,'accepted_graph_edges':[]}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2]);args=parser.parse_args()
    print(json.dumps(produce(args.root),indent=2))
