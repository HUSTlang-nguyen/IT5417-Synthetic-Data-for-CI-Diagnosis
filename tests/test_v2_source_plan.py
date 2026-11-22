import unittest
from ci_demo.v2_source_plan import screen


class SourcePlanTests(unittest.TestCase):
    def test_exposure_old_heldout_and_duplicates_are_not_eligible(self):
        row={'instance_id':'requests-fixture','repo':'psf/requests','base_commit':'a'*40,'version':'1',
            'patch':'diff --git a/requests/api.py b/requests/api.py\n--- a/requests/api.py\n+++ b/requests/api.py\n@@ -1 +1 @@\n-a\n+b\n',
            'test_patch':'diff --git a/tests/test_api.py b/tests/test_api.py\n--- a/tests/test_api.py\n+++ b/tests/test_api.py\n@@ -1 +1 @@\n-a\n+b\n',
            'FAIL_TO_PASS':'["tests/test_api.py::test_fixture"]','PASS_TO_PASS':'[]'}
        candidates,rejected=screen([row,row],set(),set())
        self.assertEqual(len(candidates),1)
        self.assertEqual(candidates[0]['role'],'test')
        self.assertEqual(rejected['duplicate_source_identity'],1)
        self.assertFalse(screen([row],{'requests-fixture'},set())[0])
        self.assertFalse(screen([row],set(),{'psf/requests'})[0])
