import copy,json,unittest
from identity import parse,classify
class IdentityControls(unittest.TestCase):
 def row(self):return {'pid':4242,'parent':1,'group':4242,'state':'L','identity':[1792330000,123456,'/owned/PreviewLab']}
 def record(self):return {'status':'observed','root':self.row()}
 def test_matching_and_absent(self):
  r=self.row();self.assertEqual(parse(json.dumps([r]),4242),r);self.assertEqual(parse(json.dumps([r]),4242,r['identity']),r);self.assertIsNone(parse('[]',4242,r['identity']))
 def test_changed_birth_or_executable_rejected(self):
  r=self.row()
  for identity in [[1792330001,123456,'/owned/PreviewLab'],[1792330000,123457,'/owned/PreviewLab'],[1792330000,123456,'/other/program']]:
   with self.subTest(identity=identity),self.assertRaises(ValueError):parse(json.dumps([r]),4242,identity)
 def test_types_duplicates_and_ranges(self):
  r=self.row()
  for field,value in [('pid',True),('parent',False),('group',-1),('state','?'),('identity',[1,1000000,'/a']),('identity',[True,0,'/a']),('identity',[1,0,'relative']),('identity',[1,0,'/bad\x00path'])]:
   v=copy.deepcopy(r);v[field]=value
   with self.subTest(field=field,value=value),self.assertRaises(ValueError):parse(json.dumps([v]),4242)
  for raw in [json.dumps([r,r]),'[{'+'"pid":4242,"pid":4242}]','{}','[]'+' '*65537]:
   with self.subTest(raw=raw[:60]),self.assertRaises(ValueError):parse(raw,4242)
 def test_classification_never_promotes_absence_zombie_or_failure(self):
  a=[self.record() for _ in range(3)];b=[self.record() for _ in range(2)];self.assertTrue(classify(a,b)['sampled_full_identity_equal'])
  for mutate in [lambda r:r.update(root=None),lambda r:r.update(status='observation_failed'),lambda r:r['root'].update(state='Z'),lambda r:r['root']['identity'].__setitem__(1,123457),lambda r:r['root']['identity'].__setitem__(2,'/changed')]:
   v=copy.deepcopy(b);mutate(v[0]);self.assertFalse(classify(a,v)['sampled_full_identity_equal']);self.assertFalse(classify(a,v)['continuous_liveness_proven'])
if __name__=='__main__':unittest.main()
