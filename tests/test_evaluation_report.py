import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ci_demo.common import write_json,sha256
from ci_demo.evaluation_report import flags,paired,reference_evidence


class EvaluationReportTests(unittest.TestCase):
    def test_invalid_and_retrieval_misses_are_not_silently_removed(self):
        ref={'sample_id':'x','cause_type':'logic/value','locations':[{'file':'a.py','function':'f'}],'retrieved_locations':[]}
        correct={'cause_type':'logic/value','locations':[{'file':'a.py','function':'f'}],'explanation':'fixture'}
        result=flags(ref,correct)
        self.assertTrue(result['classification_correct']);self.assertFalse(result['reference_function_visible'])
        self.assertFalse(result['joint_top1_correct']);self.assertTrue(flags(ref,None)['invalid'])
        self.assertIn('reference_match_not_counted_due_to_visibility_gate',result['diagnostic_groups'])

    def test_paired_counts_preserve_every_case(self):
        cases=[{'models':{'M2':{'ok':a},'M5':{'ok':b}}} for a,b in [(True,True),(True,False),(False,True),(False,False)]]
        self.assertEqual(paired(cases,'ok'),{'both_correct':1,'m2_only':1,'m5_only':1,'both_wrong':1})

    def test_reference_evidence_reads_code_as_ast_and_keeps_missing_definition_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);rep=root/'reproduction';source=root/'context/base/a.py';source.parent.mkdir(parents=True)
            source.write_text("raise RuntimeError('fixture must never execute')\ndef f():\n    return 1\n")
            log=rep/'historical-base.stdout.txt';log.parent.mkdir();log.write_text('saved fixture failure')
            write_json(rep/'manifest.json',{'source':{},'environment':{'context':str(root/'context'),'inventories':{'base':{'a.py':sha256(source)}}}})
            meta={'run_id':'reproduction','source_commit':'fixture','evidence_hashes':{log.name:sha256(log)}}
            ref={'locations':[{'file':'a.py','function':'missing'}]}
            with patch('ci_demo.evaluation_report.ROOT',root),patch('ci_demo.evaluation_report.run_path',return_value=rep):
                result=reference_evidence(meta,ref,root/'export')
                self.assertEqual(result['changed'],[]);self.assertEqual(result['missing'],[])
                self.assertEqual(result['cause_sources'][0]['status'],'definition_absent_in_base_requires_patch_context')
                self.assertTrue(result['cause_sources'][0]['hash_verified'])
                log.write_text('modified')
                self.assertTrue(reference_evidence(meta,ref,root/'export')['changed'])


if __name__=='__main__':unittest.main()
