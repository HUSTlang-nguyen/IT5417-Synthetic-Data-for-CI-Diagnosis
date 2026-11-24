import copy
from contextlib import ExitStack
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ci_demo import input_protocol, input_protocol_v5 as protocol, retrieval_v5, dataset
from ci_demo.common import ROOT, read_json, sha256, write_json
from ci_demo.retrieval_v4 import retrieve_syntax_headers

LOG = "path = Path(os.environ['CI_CONFIG_SOURCE'])\nreference = config['build-backend']\nModuleNotFoundError: missing backend"


class ConfigurationInputTests(unittest.TestCase):
    def test_only_owned_backend_log_selects_bounded_config_without_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); config = root/'pyproject.toml'
            content = '[build-system]\nbuild-backend="fixture.backend"\n' + '# long data\n'*1000
            config.write_text(content, encoding='utf-8')
            (root/'module.py').write_text('def build_backend():\n    raise RuntimeError("never execute")\n', encoding='utf-8')
            result = retrieval_v5.retrieve_configuration(root, LOG, max_chars=100)
            self.assertEqual([(s['file'], s['function']) for s in result['snippets']], [('pyproject.toml', '<module>')])
            self.assertLessEqual(result['characters'], 100); self.assertTrue(result['snippets'][0]['truncated'])
            for log in ['module.py:2 RuntimeError', 'No module named setuptools.backends; build-backend']:
                old = retrieve_syntax_headers(root, log)
                new = retrieval_v5.retrieve_configuration(root, log)
                self.assertEqual(old['snippets'], new['snippets'])
            for kwargs in [{'max_functions': 0}, {'max_chars': 99}, {'max_chars': True},
                           {'source_overrides': []}, {'source_overrides': {'module.py': 'different'}}]:
                with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                    retrieval_v5.retrieve_configuration(root, LOG, **kwargs)
            with patch.object(Path, 'is_symlink', return_value=True), self.assertRaises(ValueError):
                retrieval_v5.retrieve_configuration(root, LOG)
            config.write_bytes(b'x'*250001)
            with self.assertRaisesRegex(ValueError, 'scanner limit'): retrieval_v5.retrieve_configuration(root, LOG)
            config.unlink()
            with self.assertRaisesRegex(ValueError, 'missing'): retrieval_v5.retrieve_configuration(root, LOG)

    def fixture(self, root):
        parent_path = 'data-manifests/dataset-v2-input-protocol-v4.json'
        parent = read_json(ROOT/parent_path)
        extra = {'ci_demo/retrieval_v5.py', 'ci_demo/input_protocol_v5.py', 'ci_demo/dataset.py'}
        for name in {*parent['source_sha256'], *extra, parent_path}:
            dest = root/name; dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes((ROOT/name).read_bytes())
        spec = {'protocol': 'dataset-v2-input-v5', 'retrieval': 'ci_demo.retrieval_v5.retrieve_configuration',
                'parent_protocol': {'path': parent_path, 'sha256': sha256(root/parent_path)},
                'parameters': parent['parameters'], 'source_sha256': {name: sha256(root/name) for name in extra}}
        path = root/'protocol.json'; write_json(path, spec)
        return path, spec

    def test_frozen_parent_sources_budgets_and_binding_cannot_drift(self):
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
            root = Path(tmp); path, spec = self.fixture(root)
            stack.enter_context(patch.object(protocol, 'ROOT', root))
            stack.enter_context(patch.object(input_protocol, 'ROOT', root))
            binding = {'path': 'protocol.json', 'sha256': sha256(path)}
            self.assertIs(protocol.checked_retriever(binding)[0], retrieval_v5.retrieve_configuration)
            with self.assertRaises(ValueError): protocol.checked_retriever({**binding, 'sha256': '0'*64})
            for change in ['parameters', 'source_sha256', 'protocol', 'parent_protocol']:
                broken = copy.deepcopy(spec)
                if change == 'parameters': broken[change]['context'] = 1024
                elif change == 'source_sha256': broken[change].pop('ci_demo/dataset.py')
                elif change == 'parent_protocol': broken[change]['sha256'] = '0'*64
                else: broken[change] = 'unknown'
                write_json(path, broken)
                with self.subTest(change=change), self.assertRaises(ValueError):
                    protocol.checked_retriever({**binding, 'sha256': sha256(path)})
            write_json(path, spec)
            binding['sha256'] = sha256(path)
            (root/'ci_demo/retrieval_v5.py').write_text('changed', encoding='utf-8')
            with self.assertRaises(ValueError): protocol.checked_retriever(binding)
            (root/'ci_demo/retrieval_v5.py').write_bytes((ROOT/'ci_demo/retrieval_v5.py').read_bytes())
            (root/'ci_demo/retrieval_v4.py').write_text('changed', encoding='utf-8')
            with self.assertRaises(ValueError): protocol.checked_retriever(binding)

    def test_bound_export_passes_verified_binding_and_refuses_wrong_method(self):
        binding = {'path': 'protocol.json', 'sha256': 'frozen'}
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp); meta = {'retrieval': {'method': retrieval_v5.METHOD}}
            with patch.object(protocol, 'checked_retriever', return_value=(retrieval_v5.retrieve_configuration, retrieval_v5.METHOD)), patch.object(dataset, 'export_real', return_value=meta) as exporter:
                result = protocol.export_real_bound('run', 'assessment', dest, binding)
                self.assertEqual(result['input_protocol_sha256'], 'frozen')
                self.assertEqual(exporter.call_args.kwargs['input_protocol'], binding)
                self.assertIs(exporter.call_args.kwargs['retriever'], retrieval_v5.retrieve_configuration)
                (dest/'manifest.json').unlink(); meta['retrieval']['method'] = 'wrong'
                with self.assertRaises(ValueError): protocol.export_real_bound('run', 'assessment', dest, binding)
                self.assertFalse((dest/'manifest.json').exists())
            raw = {'source': {'local_configuration_check': True}, 'environment': {}}
            with patch.object(dataset, 'real_evidence', return_value=(raw, {})), patch.object(protocol, 'checked_retriever', return_value=(retrieval_v5.retrieve_configuration, retrieval_v5.METHOD)):
                with self.assertRaisesRegex(ValueError, 'exact frozen retriever'):
                    dataset.export_real('run', 'missing', dest/'unused', retriever=retrieve_syntax_headers, input_protocol=binding)
