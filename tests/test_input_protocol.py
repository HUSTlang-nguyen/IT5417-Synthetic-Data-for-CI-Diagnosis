from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ci_demo import input_protocol as protocol
from ci_demo.common import ROOT, read_json, sha256, write_json


class InputProtocolTests(unittest.TestCase):
    def test_real_v3_binding_and_tampered_protocol_source_and_budget(self):
        spec = read_json(ROOT / 'data-manifests/dataset-v2-input-protocol.json')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in spec['source_sha256']:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / name).read_bytes())
            path = root / 'protocol.json'
            write_json(path, spec)
            binding = {'path': 'protocol.json', 'sha256': sha256(path)}
            with patch.object(protocol, 'ROOT', root):
                self.assertIs(protocol.checked_retriever(binding)[0], protocol.retrieve_balanced)
                with self.assertRaisesRegex(ValueError, 'protocol changed'):
                    protocol.checked_retriever({**binding, 'sha256': '0' * 64})
                spec['parameters']['max_chars'] = 1
                write_json(path, spec)
                binding['sha256'] = sha256(path)
                with self.assertRaisesRegex(ValueError, 'budgets differ'):
                    protocol.checked_retriever(binding)
                (root / 'ci_demo/retrieval_v3.py').write_text('changed')
                with self.assertRaisesRegex(ValueError, 'source changed'):
                    protocol.checked_retriever(binding)
                (root / 'ci_demo/retrieval_v3.py').write_bytes((ROOT / 'ci_demo/retrieval_v3.py').read_bytes())
                spec['parameters']['max_chars'] = 6000
                spec['retrieval'] = 'ci_demo.retrieval_v4.retrieve_syntax_headers'
                write_json(path, spec)
                binding['sha256'] = sha256(path)
                with self.assertRaisesRegex(ValueError, 'Incomplete'):
                    protocol.checked_retriever(binding)
                name = 'ci_demo/retrieval_v4.py'
                (root / name).write_bytes((ROOT / name).read_bytes())
                spec['source_sha256'][name] = sha256(ROOT / name)
                write_json(path, spec)
                binding['sha256'] = sha256(path)
                self.assertIs(protocol.checked_retriever(binding)[0], protocol.retrieve_syntax_headers)

    def test_export_cannot_mislabel_another_retrieval_method(self):
        binding = {'path': 'protocol.json', 'sha256': 'frozen'}
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp)
            metadata = {'retrieval': {'method': 'wrong'}}
            with patch.object(protocol, 'checked_retriever', return_value=(protocol.retrieve_syntax_headers, 'balanced_syntax_headers_v4')), patch.object(protocol, 'export_real', return_value=metadata) as exporter:
                with self.assertRaisesRegex(ValueError, 'declared frozen retriever'):
                    protocol.export_real_bound('run', 'assessment', destination, binding)
                self.assertFalse((destination / 'manifest.json').exists())
                metadata['retrieval']['method'] = 'balanced_syntax_headers_v4'
                result = protocol.export_real_bound('run', 'assessment', destination, binding)
                self.assertEqual(result['input_protocol_sha256'], 'frozen')
                self.assertIs(exporter.call_args.kwargs['retriever'], protocol.retrieve_syntax_headers)
