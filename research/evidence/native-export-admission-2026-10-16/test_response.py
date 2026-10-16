import copy
import io
import hashlib
import json
from pathlib import Path
import unittest
from PIL import Image
from export_response import normalize,admit_frozen_sentinel,Rejected
HERE=Path(__file__).parent
class ResponseTests(unittest.TestCase):
    def setUp(self):
        self.results=json.loads((HERE/'native-results.json').read_text())
        self.expected=json.loads((HERE/'expected.json').read_text())
    def test_actual_failure_rejected_without_inventing_image(self):
        with self.assertRaises(Rejected):normalize(self.results['sentinel_light'])
    def test_actual_positive_variants_and_text_only(self):
        for name in self.expected:
            row=self.results[name];self.assertFalse(normalize(row)['content_accepted'])
            text_only=copy.deepcopy(row);text_only.pop('structuredContent');self.assertEqual(normalize(row),normalize(text_only))
    def test_error_flag_overrides_positive_looking_payload(self):
        row=copy.deepcopy(self.results['sentinel_dark']);row['isError']=True
        with self.assertRaises(Rejected):normalize(row)
    def test_flag_and_payload_type_errors_reject(self):
        for flag in [0,'false',None]:
            row=copy.deepcopy(self.results['sentinel_dark']);row['isError']=flag
            with self.assertRaises(Rejected):normalize(row)
        row=copy.deepcopy(self.results['sentinel_light']);row.pop('isError')
        with self.assertRaises(Rejected):normalize(row)
    def test_conflicting_representations_reject(self):
        row=copy.deepcopy(self.results['sentinel_dark']);row['structuredContent']['errors']=['failed']
        with self.assertRaises(Rejected):normalize(row)
    def test_malformed_oversized_missing_payload_rejects(self):
        for text in ['{','[]','x'*65537,'{"errors":[]}']:
            with self.assertRaises(Rejected):normalize({'content':[{'type':'text','text':text}]})
    def test_frozen_success_binds_identity_and_pixels(self):
        for name,expected in self.expected.items():
            png=(HERE/expected['local_image']).read_bytes();im=Image.open(HERE/expected['local_image']).convert('RGBA')
            result=admit_frozen_sentinel(self.results[name],png,expected)
            self.assertTrue(result['content_accepted']);self.assertFalse(result['live_provenance'])
    def test_wrong_path_png_mode_and_old_decoder_interface_reject(self):
        name='sentinel_dark';expected=self.expected[name];row=self.results[name]
        png=(HERE/expected['local_image']).read_bytes();im=Image.open(HERE/expected['local_image']).convert('RGBA');raw=im.tobytes()
        bad=copy.deepcopy(expected);bad['native_path']+='.other'
        with self.assertRaises(Rejected):admit_frozen_sentinel(row,png,bad)
        with self.assertRaises(Rejected):admit_frozen_sentinel(row,png+b'!',expected)
        wrong_mode=copy.deepcopy(expected);wrong_mode['mode']='light'
        with self.assertRaises(Rejected):admit_frozen_sentinel(row,png,wrong_mode)
        with self.assertRaises(TypeError):admit_frozen_sentinel(row,png,raw,im.size,expected)
    def test_duplicate_keys_double_slash_and_nonfinite_reject(self):
        for text in [
            '{"errors":["failure"],"errors":[],"previewSnapshotPath":"/tmp/x.png"}',
            '{"errors":[],"previewSnapshotPath":"//tmp/x.png"}',
            '{"errors":[],"previewSnapshotPath":"/tmp/x.png","supportedLocalizations":NaN}',
        ]:
            with self.assertRaises(Rejected):normalize({'content':[{'type':'text','text':text}]})
    def test_optional_metadata_schema_rejects(self):
        for key,value in [('supportedLocalizations',None),('supportedLocalizations',[1]),('supportedPreviewVariantOverrides',[]),('supportedPreviewVariantOverrides',{'Color Scheme':[None]}),('supportedPreviewVariantOverrides',{'Color Scheme':['']})]:
            row=copy.deepcopy(self.results['sentinel_dark']);payload=row['structuredContent'];payload[key]=value;row['content'][0]['text']=json.dumps(payload)
            with self.assertRaises(Rejected):normalize(row)
    def test_internal_decode_rejects_alpha_uniform_and_wrong_size(self):
        name='sentinel_dark';expected=self.expected[name];row=self.results[name]
        image=Image.open(HERE/expected['local_image']).convert('RGBA');alpha=image.copy();alpha.putpixel((319,199),(255,0,255,0))
        for bad_image in [alpha,Image.new('RGBA',(320,200),(30,30,30,255)),Image.new('RGBA',(320,200),(255,0,255,255)),Image.new('RGBA',(320,201),(255,0,255,255))]:
            output=io.BytesIO();bad_image.save(output,format='PNG');data=output.getvalue();mapping=copy.deepcopy(expected);mapping['png_sha256']=hashlib.sha256(data).hexdigest()
            with self.assertRaises(Rejected):admit_frozen_sentinel(row,data,mapping)
if __name__=='__main__':unittest.main()
