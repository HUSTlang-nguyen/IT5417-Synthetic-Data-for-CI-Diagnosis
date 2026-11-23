from pathlib import Path
import tempfile
import unittest
from ci_demo.retrieval_v3 import retrieve_balanced,excerpt


class BalancedRetrievalTests(unittest.TestCase):
    def test_large_first_function_cannot_consume_other_function_budgets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'product.py').write_text('def relevant_big():\n'+''.join('    value = "relevant payload"\n' for _ in range(100))+'\ndef relevant_small():\n    return "relevant small"\n')
            result=retrieve_balanced(root,'relevant',max_functions=2,max_chars=450)
            self.assertEqual(len(result['snippets']),2)
            self.assertLessEqual(sum(len(x['text']) for x in result['snippets']),450)
            self.assertTrue(result['snippets'][0]['truncated'])
            self.assertIn('omitted',result['snippets'][0]['text'])

    def test_observed_syntax_line_has_context_without_reference_locations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'bad.py').write_text('x = 1\n'*100+'broken(\n'+'x = 2\n'*100)
            result=retrieve_balanced(root,'File "bad.py", line 101\nSyntaxError: invalid syntax',max_chars=350)
            self.assertIn('broken(',result['snippets'][0]['text'])
            self.assertEqual(result['snippets'][0]['function'],'<module>')
            self.assertLessEqual(result['characters'],350)

    def test_small_excerpt_unchanged_and_invalid_budget_rejected(self):
        self.assertEqual(excerpt('source',20),'source')
        for value in [True,0,-1,6001,1.5]:
            with self.assertRaises(ValueError):retrieve_balanced('.', 'log', max_chars=value)
