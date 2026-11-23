"""Recovered-test provenance fixtures use inert text, never execute target code."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ci_demo.common import write_json, sha256
from ci_demo import upstream_tests


class UpstreamTests(unittest.TestCase):
    def fixture(self, root):
        cache=root/'cache';cache.mkdir()
        repair='--- a/product.py\n+++ b/product.py\n@@ -1 +1 @@\n-old\n+new\n'
        tests='--- a/tests/test_product.py\n+++ b/tests/test_product.py\n@@ -1 +1 @@\n-old\n+new\n'
        (cache/'repair.patch').write_text(repair,encoding='utf-8',newline='\n')
        (cache/'test.patch').write_text(tests,encoding='utf-8',newline='\n')
        source={'instance_id':'example__library-1','repo':'example/library','base_commit':'a'*40,
                'original_split':'train','patch':repair,'FAIL_TO_PASS':'[]','PASS_TO_PASS':'[]'}
        write_json(cache/'source.json',source)
        write_json(cache/'pr.json',{'base':{'sha':'a'*40,'repo':{'full_name':'example/library'}},'head':{'sha':'b'*40}})
        content=b'new\n';(root/'fixed').mkdir();(root/'fixed/product.py').write_bytes(content)
        provenance={'policy':upstream_tests.POLICY,'source_case_id':source['instance_id'],
            'source_record':'cache/source.json','source_record_sha256':sha256(cache/'source.json'),
            'pr_metadata':'cache/pr.json','pr_metadata_sha256':sha256(cache/'pr.json'),
            'base_commit':'a'*40,'upstream_head':'b'*40,
            'repair_patch_sha256':sha256(cache/'repair.patch'),'test_patch_sha256':sha256(cache/'test.patch'),
            'product_blobs':[{'path':'product.py','upstream_blob':hashlib.sha1(b'blob 4\0'+content).hexdigest()}]}
        write_json(cache/'provenance.json',provenance)
        case={'source_kind':'swebench','dataset_protocol':'dataset-v2','experiment_role':'train',
            'test_reference_policy':upstream_tests.POLICY,'source_case_id':source['instance_id'],
            'repo_url':'https://github.com/example/library','base':'a'*40,
            'upstream_test_provenance':'cache/provenance.json','upstream_test_provenance_sha256':sha256(cache/'provenance.json'),
            'source_record_sha256':sha256(cache/'source.json'),
            'repair_patch':'cache/repair.patch','repair_patch_sha256':sha256(cache/'repair.patch'),
            'test_patch':'cache/test.patch','test_patch_sha256':sha256(cache/'test.patch'),
            'frozen_test_files':['tests/test_product.py'],'fail_to_pass':[],'pass_to_pass':[],
            'local_expected_failures':['tests/test_product.py::TestAPI::test_regression'],
            'local_expected_passes':['tests/test_product.py::TestAPI::test_control'],
            'test_targets':['tests/test_product.py::TestAPI::test_regression','tests/test_product.py::TestAPI::test_control']}
        return case

    def test_local_expectations_stay_separate_and_fixed_product_bytes_must_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);case=self.fixture(root)
            with patch.object(upstream_tests,'ROOT',root),patch.object(upstream_tests,'CACHE',root/'cache'):
                failures,passes,origin=upstream_tests.references(case)
                self.assertEqual(origin,'upstream_recovered_local')
                self.assertEqual(failures,case['local_expected_failures']);self.assertEqual(passes,case['local_expected_passes'])
                self.assertEqual(case['fail_to_pass'],[])
                upstream_tests.verify_products(case,root/'fixed')
                (root/'fixed/product.py').write_text('wrong fixture')
                with self.assertRaisesRegex(ValueError,'product differs'):upstream_tests.verify_products(case,root/'fixed')
                (root/'cache/test.patch').write_text('altered test')
                with self.assertRaisesRegex(ValueError,'hash mismatch'):upstream_tests.references(case)

    def test_scope_reference_identity_and_path_errors_are_rejected(self):
        for field,value in [('experiment_role','test'),('test_reference_policy','unknown'),('base','c'*40),
                            ('fail_to_pass',['invented']),('local_expected_failures',[]),
                            ('local_expected_failures',[{}]),('local_expected_failures',['other.py::test_x']),
                            ('upstream_test_provenance','../outside.json')]:
            with self.subTest(field=field),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);case=self.fixture(root);case[field]=value
                with patch.object(upstream_tests,'ROOT',root),patch.object(upstream_tests,'CACHE',root/'cache'):
                    with self.assertRaises((ValueError,FileNotFoundError)):upstream_tests.references(case)

    def test_dataset_supplied_references_are_unchanged(self):
        source={'fail_to_pass':['tests/test_api.py::test_fails'],'pass_to_pass':['tests/test_api.py::test_control']}
        self.assertEqual(upstream_tests.references(source),(source['fail_to_pass'],source['pass_to_pass'],'dataset_supplied'))
        with self.assertRaises(KeyError):upstream_tests.references({})
