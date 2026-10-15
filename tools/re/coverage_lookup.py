"""Bounded discovery of prior research anchors; never grants delivery acceptance."""
import argparse
import hashlib
import json
import re
from pathlib import Path


def lookup(root, terms):
    root=Path(root).resolve();docs=root/'docs/reverse-engineering'
    def normalize(value):return re.sub(r'[^a-z0-9]+',' ',value.lower()).strip()
    terms=[normalize(term) for term in terms]
    if not terms or any(not term for term in terms):raise ValueError('Nonempty research terms required')
    files=sorted(docs.glob('*.md'))
    if len(files)>2048:raise ValueError('Coverage document count limit')
    total=0;matches=[]
    for p in files:
        if p.is_symlink():continue
        size=p.stat().st_size;total+=size
        if size>1048576 or total>16777216:raise ValueError('Coverage byte limit')
        text=p.read_text();plain=normalize(text)
        if not all(term in plain for term in terms):continue
        # Link anchors are discovery hints, not a claim that their contents pass.
        anchors=[]
        for link in re.findall(r'\]\(([^)]+manifest\.json)\)',text):
            target=(p.parent/link).resolve()
            try:relative=target.relative_to(root/'research/evidence')
            except ValueError:continue
            if target.is_file() and not (p.parent/link).is_symlink():
                anchors.append({'manifest':'research/evidence/'+str(relative),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
        matches.append({'document':str(p.relative_to(root)),'title':text.splitlines()[0].lstrip('# '),'anchors':anchors})
    return {'decision':'review-existing-evidence' if matches else 'no-text-match','matches':matches,'delivery_accepted':False,'limitation':'Text discovery only. Read scope and verify the cited seal before choosing or skipping research.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('terms',nargs='+');parser.add_argument('--root',default=Path(__file__).resolve().parents[2]);args=parser.parse_args()
    print(json.dumps(lookup(args.root,args.terms),indent=2))
