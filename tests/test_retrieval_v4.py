from pathlib import Path
import tempfile
import unittest

from ci_demo.retrieval_v3 import retrieve_balanced
from ci_demo.retrieval_v4 import enclosing_header, retrieve_syntax_headers


class SyntaxHeaderTests(unittest.TestCase):
    def test_scope_ignores_fake_headers_and_leaves_completed_functions(self):
        text='class Outer:\n    def method(self):\n        value = "def fake():"\n        # class Wrong:\n        if True:\n            value = 1\n         value = 2\n'
        scope=enclosing_header(text,7)
        self.assertEqual(scope['function'],'Outer.method')
        self.assertEqual(scope['header_lines'],[1,2])
        self.assertIsNone(enclosing_header('def done():\n    return 1\nx = )\n',3))
        self.assertIsNone(enclosing_header('def incomplete(\n',1))
        self.assertIsNone(enclosing_header('def inline(): return 1\nx = )\n',2))
        self.assertEqual(enclosing_header('def outer():\n    def inner():\n        x = )\n',3)['function'],'outer.inner')

    def test_long_invalid_method_keeps_observed_fault_and_source_header_in_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            text='class Real:\n    def broken(self):\n'+80*'        item = 1\n'+'        if True:\n            item = 2\n         item = 3\n'
            (root/'product.py').write_text(text)
            log='File "/source/base/product.py", line 85\nIndentationError: unindent does not match'
            old=retrieve_balanced(root,log,max_chars=450)
            new=retrieve_syntax_headers(root,log,max_chars=450)
            self.assertEqual(old['snippets'][0]['function'],'<module>')
            self.assertEqual(new['snippets'][0]['function'],'Real.broken')
            self.assertIn('def broken(self):',new['snippets'][0]['text'])
            self.assertIn('item = 3',new['snippets'][0]['text'])
            self.assertLessEqual(new['characters'],old['characters'])

    def test_valid_source_and_module_fault_keep_v3_snippets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'valid.py').write_text('def run():\n    raise SyntaxError("input grammar")\n')
            log='File "valid.py", line 2\nSyntaxError: input grammar'
            self.assertEqual(retrieve_balanced(root,log)['snippets'],retrieve_syntax_headers(root,log)['snippets'])
            (root/'valid.py').write_text('x = )\n')
            self.assertEqual(retrieve_syntax_headers(root,'File "valid.py", line 1\nSyntaxError')['snippets'][0]['function'],'<module>')
