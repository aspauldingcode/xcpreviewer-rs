import hashlib,json
from pathlib import Path

def verify(folder):
 e=Path(folder);m=json.loads((e/'manifest.json').read_text())
 assert set(m['files'])=={str(p.relative_to(e)) for p in e.rglob('*') if p.is_file() and p!=e/'manifest.json'}
 for name,row in m['files'].items():
  p=e/name;assert not Path(name).is_absolute() and '..' not in Path(name).parts and not p.is_symlink();raw=p.read_bytes();assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
 d=json.loads((e/'anchors.json').read_text());assert len(d['rows'])==2 and d['task_accepted'] is d['handoff_approved'] is False
 expected=[('research/evidence/native-state-binding-2026-10-11/manifest.json','959d7d600eb86d1d4df5a8ad601199c80a19965e','7f9ecd5288bd62f5d0f8a2136cebce157b523fcb430a9267c715189b1add172e'),('research/evidence/surface-partial-right-2026-10-14/manifest.json','f60d1ef99f4e07893113a58440d8b337c51f3ce8','25583eef6084ed9e9ef387fab81b794774c1505a04c4966659a2b00b8b59e28e')]
 for row,(path,commit,seal) in zip(d['rows'],expected):
  assert row['manifest']==path and row['commit']==commit and row['manifest_sha256']==seal and row['git_mode']=='100644'
  assert row['published_ref']=='origin/master' and row['published_ref_commit']=='e5f9a769046c6e9f65be40dadf50fd39168f7960' and row['commit_is_ancestor'] is True and row['repository_blob_matches_seal'] is True
  assert row['document_mentions_seal'] is row['independent_external_trust'] is row['semantic_review_complete'] is row['qualified_for_acceptance'] is False
  frozen=Path(row['frozen_manifest']);assert not frozen.is_absolute() and '..' not in frozen.parts
  raw=(e/frozen).read_bytes();assert len(raw)==row['manifest_bytes'] and hashlib.sha256(raw).hexdigest()==seal and hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['git_blob']
 return {'repository_anchors':2,'git_object_bytes_verified':sum(r['manifest_bytes'] for r in d['rows']),'document_digests_added':False,'independent_external_trust':False,'semantic_review_complete':False}
