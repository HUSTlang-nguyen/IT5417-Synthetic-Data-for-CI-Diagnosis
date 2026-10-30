"""Software fixtures for read-only lineage; no research output is fabricated."""
import unittest
from ci_demo.curation import source_groups, edit_fingerprint


class CurationTests(unittest.TestCase):
    def test_shared_commit_unifies_aliases_across_sources_without_assigning_train(self):
        records = [{"case_id":"a","repo_url":"https://github.com/Owner/Repo"},
                   {"case_id":"b","repo_url":"https://github.com/Fork/Repo.git"},
                   {"case_id":"c","repo_url":"https://github.com/Other/Repo"}]
        configs = {"a":{"base":"a"*40},"b":{"base":"a"*40},"c":{"base":"b"*40}}
        groups, edges = source_groups(records, configs)
        self.assertEqual(len(groups),2)
        self.assertTrue(any(set(g['case_ids'])=={'a','b'} for g in groups))
        self.assertTrue(all(g['split']=='development' for g in groups))
        self.assertEqual(edges[0]['reason'],'shared_immutable_commit')

    def test_lexical_edit_key_ignores_spacing_but_preserves_string_literal_values(self):
        a = edit_fingerprint('return x + 1\n','return x - 1\n','m.py')
        b = edit_fingerprint('return x+1\n','return x-1\n','m.py')
        self.assertEqual(a,b)
        self.assertNotEqual(edit_fingerprint("return 'a b'\n","return 'x'\n",'m.py'),
                            edit_fingerprint("return 'ab'\n","return 'x'\n",'m.py'))


if __name__ == '__main__': unittest.main()
