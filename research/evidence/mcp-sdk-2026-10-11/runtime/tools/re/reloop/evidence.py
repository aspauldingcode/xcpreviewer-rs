"""Verified SQLite/FTS evidence index, bounded retrieval and scoped claims."""
import json
import pathlib
import re
import sqlite3
from reloop.core import atomic, canonical_hash, digest, evaluate, load, now


def artifact(controller, run_id, relative):
    if not controller.verify(run_id)['valid']:
        raise RuntimeError('Evidence integrity failure')
    root = (controller.runs / run_id).resolve()
    target = (root / relative).resolve()
    if root not in target.parents or not target.is_file():
        raise ValueError('Artifact path must remain inside verified run')
    manifest = load(root / 'manifest.json')
    if relative not in {a['path'] for a in manifest['artifacts']}:
        raise ValueError('Artifact not in sealed manifest')
    return target


def page(controller, run_id, relative, offset=0, chars=6000):
    if type(offset) is not int or offset < 0 or type(chars) is not int or not 1 <= chars <= 12000:
        raise ValueError('Invalid evidence page')
    target = artifact(controller, run_id, relative)
    if target.stat().st_size > 4 * 1024 * 1024:
        raise ValueError('Select a summary artifact rather than a bulk dump')
    text = target.read_text(errors='replace')
    return {'run_id': run_id, 'path': relative, 'sha256': digest(target),
            'offset': offset, 'text': text[offset:offset + chars],
            'next_offset': offset + chars if offset + chars < len(text) else None}


class Store:
    def __init__(self, controller):
        self.controller = controller
        self.path = controller.state / 'evidence.sqlite3'
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, manifest_hash TEXT, data TEXT);
            CREATE TABLE IF NOT EXISTS nodes(id TEXT PRIMARY KEY, run_id TEXT, kind TEXT, data TEXT);
            CREATE TABLE IF NOT EXISTS edges(source TEXT, target TEXT, kind TEXT, data TEXT,
                PRIMARY KEY(source,target,kind));
            CREATE VIRTUAL TABLE IF NOT EXISTS documents USING fts5(run_id UNINDEXED,path UNINDEXED,body);
        ''')

    def close(self): self.db.close()

    def node(self, key, run_id, kind, data):
        self.db.execute('INSERT OR REPLACE INTO nodes VALUES(?,?,?,?)',
                        (key, run_id, kind, json.dumps(data, sort_keys=True)))

    def edge(self, source, target, kind, data=None):
        self.db.execute('INSERT OR REPLACE INTO edges VALUES(?,?,?,?)',
                        (source, target, kind, json.dumps(data or {}, sort_keys=True)))

    def index(self):
        added = []; invalid = []
        for run in sorted(self.controller.runs.iterdir()):
            manifest = load(run / 'manifest.json', {})
            if not manifest.get('sealed'): continue
            if not self.controller.verify(run.name)['valid']:
                invalid.append(run.name)
                self.db.execute('DELETE FROM documents WHERE run_id=?', (run.name,))
                self.db.execute('DELETE FROM runs WHERE id=?', (run.name,))
                self.db.execute('DELETE FROM edges WHERE source IN (SELECT id FROM nodes WHERE run_id=?) OR target IN (SELECT id FROM nodes WHERE run_id=?)', (run.name,run.name))
                self.db.execute('DELETE FROM nodes WHERE run_id=?',(run.name,))
                continue
            fingerprint = digest(run / 'manifest.json')
            prior = self.db.execute('SELECT manifest_hash FROM runs WHERE id=?', (run.name,)).fetchone()
            if prior and prior[0] == fingerprint: continue
            self.db.execute('DELETE FROM documents WHERE run_id=?', (run.name,))
            summary = {k: manifest.get(k) for k in ['run_id','experiment_id','hypothesis','verdict','execution','checks','environment_hash']}
            self.db.execute('INSERT OR REPLACE INTO runs VALUES(?,?,?)', (run.name, fingerprint, json.dumps(summary)))
            self.node('run:' + run.name, run.name, 'run', summary)
            for entry in manifest['artifacts']:
                relative = entry['path']
                if not relative.startswith('output/') or entry['bytes'] > 256 * 1024:
                    continue
                path = run / relative
                if path.suffix not in {'.json','.txt','.stdout','.stderr','.jsonl'}: continue
                text = path.read_text(errors='replace')
                if path.suffix == '.json':
                    try: text = json.dumps(compact(json.loads(text)), ensure_ascii=False)
                    except ValueError: pass
                self.db.execute('INSERT INTO documents VALUES(?,?,?)', (run.name, relative, text))
                key = 'artifact:' + run.name + ':' + relative
                self.node(key, run.name, 'artifact', entry)
                self.edge('run:' + run.name, key, 'produced')
                if path.name == 'joined-trace.json':
                    joined = load(path)
                    for item in joined.get('links', []):
                        function = 'function:' + run.name + ':' + item['image_sha256'] + ':' + item['offset']
                        self.node(function, run.name, 'function', item)
                        self.edge(key, function, 'observed-and-resolved', {'scope': joined.get('scope')})
            added.append(run.name)
        self.db.commit()
        return {'indexed': added, 'invalid': invalid,
                'runs': self.db.execute('SELECT count(*) FROM runs').fetchone()[0],
                'nodes': self.db.execute('SELECT count(*) FROM nodes').fetchone()[0]}

    def search(self, query, limit=8):
        if not isinstance(query, str) or not 1 <= len(query) <= 500 or type(limit) is not int or not 1 <= limit <= 20:
            raise ValueError('Invalid search bounds')
        # Literal tokens prevent callers from accidentally executing FTS syntax.
        words = re.findall(r'[\w$]+', query)[:12]
        if not words: return []
        expression = ' AND '.join('"' + w.replace('"','""') + '"' for w in words)
        rows = self.db.execute('SELECT run_id,path,snippet(documents,2,"[", "]"," … ",32) AS snippet FROM documents WHERE documents MATCH ? ORDER BY bm25(documents) LIMIT ?', (expression, limit)).fetchall()
        result = []
        for row in rows:
            if self.controller.verify(row['run_id'])['valid']:
                result.append(dict(row))
        return result

    def graph(self, run_id):
        if not self.controller.verify(run_id)['valid']: raise RuntimeError('Evidence integrity failure')
        nodes = [dict(r) for r in self.db.execute('SELECT id,kind,data FROM nodes WHERE run_id=? LIMIT 100', (run_id,))]
        ids = {n['id'] for n in nodes}
        edges = [dict(r) for r in self.db.execute('SELECT source,target,kind,data FROM edges WHERE source IN (SELECT id FROM nodes WHERE run_id=?) LIMIT 200',(run_id,)) if r['target'] in ids]
        return {'nodes':nodes,'edges':edges,'bounded':True}


def compact(value):
    """Keep diagnostic semantics; remove byte blobs and huge unrequested arrays."""
    if isinstance(value, dict):
        return {k: ({'omitted_chars':len(v)} if (k.endswith('base64') or k=='raw_bytes') and isinstance(v,str) else compact(v)) for k,v in value.items()}
    if isinstance(value, list):
        items = [compact(v) for v in value[:200]]
        return items + ([{'omitted_items':len(value)-200}] if len(value)>200 else [])
    if isinstance(value, str) and len(value)>6000:
        return value[:6000] + '\n[bounded; retrieve artifact for more]'
    return value


def claim(controller, spec):
    required = {'id','assertion','scope','evidence'}
    if not isinstance(spec,dict) or set(spec)!=required or not re.fullmatch('[a-z][a-z0-9-]{1,63}',spec['id']):
        raise ValueError('Invalid claim fields or ID')
    if not all(isinstance(spec[k],str) and spec[k].strip() for k in ['assertion','scope']):
        raise ValueError('Claim assertion and explicit scope required')
    if not isinstance(spec['evidence'],list) or not 1<=len(spec['evidence'])<=20:
        raise ValueError('Claim requires 1..20 evidence references')
    assessments=[]; scopes=set()
    for reference in spec['evidence']:
        if set(reference)!={'run_id','check'} or not isinstance(reference['check'],dict): raise ValueError('Invalid claim evidence')
        check=reference['check']
        if set(check)!={'path','equals'} or not isinstance(check['path'],str):raise ValueError('Invalid evidence check')
        result=load(artifact(controller,reference['run_id'],'output/result.json'))
        manifest=load(controller.runs/reference['run_id']/'manifest.json')
        verdict,checks=evaluate([check],result)
        if manifest['execution']!='success':verdict='inconclusive'
        elif checks[0]['present'] and not checks[0]['passed']:verdict='contradicts'
        assessments.append({'run_id':reference['run_id'],'verdict':verdict,'checks':checks})
        scopes.add(manifest['environment_hash'])
    verdicts={a['verdict'] for a in assessments}
    status='contradicted' if 'contradicts' in verdicts else 'supported' if verdicts=={'supports'} else 'candidate'
    record={**spec,'status':status,'assessments':assessments,'environment_hashes':sorted(scopes),'updated_at':now(),
            'limitation':'Checks support explicit scoped assertions only. Repetition/static views do not automatically establish independent corroboration.'}
    path=controller.state/'claims'/spec['id']/(canonical_hash(record)+'.json')
    atomic(path,record)
    return record
