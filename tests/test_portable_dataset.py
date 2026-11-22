from pathlib import Path
import shutil
import tempfile
import unittest
from ci_demo.common import sha256, write_json, read_json
from ci_demo.portable_dataset import export, verify, checked_file


class PortableTests(unittest.TestCase):
    def test_move_preserves_bytes_and_detects_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); source = root / 'source'; source.mkdir()
            write_json(source/'input.json', {'execution_log': 'inert log', 'code': []})
            write_json(source/'reference.json', {'sample_id': 'fixture', 'quality': 'silver'})
            write_json(source/'assessment.json', {'quality': 'silver'})
            write_json(source/'manifest.json', {'sample_id': 'fixture', 'role': 'train', 'origin': 'real_local_reconstruction',
                'injected_by':{'model_info':{'details':{'modelfile':r'FROM C:\Users\fixture\private-model'}}},
                **{k+'_sha256': sha256(source/(k+'.json')) for k in ('input','reference','assessment')}})
            lock=root/'lock.json'
            write_json(lock, {'status':'locked','protocol':'v1.1','records':[{'sample_id':'fixture','role':'train',
                'directory':str(source),'manifest_sha256':sha256(source/'manifest.json'),'group_id':'repo:fixture'}]})
            destination=root/'export'; export(lock,destination)
            moved=root/'elsewhere'; shutil.move(destination,moved)
            self.assertEqual(verify(moved)['records'],1)
            portable=read_json(moved/'package.json')['records'][0]
            self.assertEqual(portable['source_manifest_sha256'],sha256(source/'manifest.json'))
            self.assertTrue(portable['transformations'])
            self.assertNotIn('modelfile',read_json(moved/'records/fixture/manifest.json')['injected_by']['model_info']['details'])
            self.assertIn('modelfile',read_json(source/'manifest.json')['injected_by']['model_info']['details'])
            (moved/'NOTICE.txt').write_bytes(b'original notice')
            package=read_json(moved/'package.json');package['attachments']={'NOTICE.txt':sha256(moved/'NOTICE.txt')}
            write_json(moved/'package.json',package);self.assertEqual(verify(moved)['records'],1)
            (moved/'NOTICE.txt').write_bytes(b'changed notice')
            with self.assertRaises(ValueError):verify(moved)
            (moved/'NOTICE.txt').write_bytes(b'original notice')
            self.assertEqual((source/'input.json').read_bytes(),(moved/'records/fixture/input.json').read_bytes())
            with self.assertRaises(ValueError): export(lock,moved)
            with self.assertRaises(ValueError): checked_file(moved,'../source/input.json')
            (moved/'records/fixture/input.json').write_text('{}')
            with self.assertRaises(ValueError): verify(moved)

    def test_invalid_lock_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);write_json(p/'lock.json',{'status':'draft','protocol':'v1.1'})
            with self.assertRaises(ValueError):export(p/'lock.json',p/'out')
