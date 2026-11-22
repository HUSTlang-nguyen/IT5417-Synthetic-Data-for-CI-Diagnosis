from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from ci_demo.common import read_json, sha256, write_json
from ci_demo.portable_dataset import export
from ci_demo.publication_audit import audit


class PublicationAuditTests(unittest.TestCase):
    def test_pinned_license_and_privacy_findings_never_imply_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'record';source.mkdir()
            write_json(source/'input.json',{'execution_log':'/home/user/project test','code':[]})
            write_json(source/'reference.json',{'sample_id':'fixture','quality':'silver'})
            write_json(source/'assessment.json',{'quality':'silver'})
            write_json(source/'manifest.json',{'sample_id':'fixture','role':'train','origin':'real_local_reconstruction',
                'run_id':'fixture-run','repo':'https://github.com/example/repo','source_commit':'immutable',
                **{k+'_sha256':sha256(source/(k+'.json')) for k in ('input','reference','assessment')}})
            lock=root/'lock.json';write_json(lock,{'status':'locked','protocol':'v1.1','records':[{
                'sample_id':'fixture','role':'train','group_id':'repo:fixture','directory':str(source),
                'manifest_sha256':sha256(source/'manifest.json')}]})
            package=root/'package';export(lock,package)
            context=root/'context';(context/'base').mkdir(parents=True)
            license=context/'base/LICENSE';license.write_bytes(b'fixture license, no legal claim')
            run=root/'runs/fixture-run'
            write_json(run/'manifest.json',{'environment':{'context':str(context)},'source':{'base':'immutable'}})
            write_json(run/'license-evidence.json',{'path':'LICENSE','sha256':sha256(license),'declared_license':'fixture'})
            with patch('ci_demo.publication_audit.ROOT',root):
                result=audit(package,root/'audit')
                self.assertEqual(result['license_variants'],1)
                self.assertEqual(result['privacy_findings'],1)
                self.assertEqual(result['status'],'attribution_prepared_review_pending')
                license.write_bytes(b'tampered')
                with self.assertRaises(ValueError):audit(package,root/'bad-audit')
