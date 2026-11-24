"""Owned fixture data only; no upstream backend or source executes on the host."""
from contextlib import ExitStack
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ci_demo import configuration, dataset, multicase, ollama, upstream_tests
from ci_demo.common import read_json, sha256, write_json
from tests import test_compilation


class ConfigurationTests(unittest.TestCase):
    def fixture(self, root):
        case, paths = test_compilation.CompilationTests().fixture(root)
        case.pop('local_compilation_check')
        case.update(local_configuration_check=True, allowed_file='pyproject.toml', test_targets=['pyproject.toml'])
        case['configuration_provenance'] = case.pop('compilation_provenance')
        case.pop('compilation_provenance_sha256')
        info = read_json(paths['provenance'])
        info['policy'] = configuration.POLICY
        files = read_json(paths['pr_files']); files[0]['filename'] = 'pyproject.toml'
        write_json(paths['pr_files'], files); info['pr_files_sha256'] = sha256(paths['pr_files'])
        write_json(paths['provenance'], info)
        case['configuration_provenance_sha256'] = sha256(paths['provenance'])
        return case

    def test_pinned_scope_harness_and_source_tampering(self):
        with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
            root = Path(tmp); case = self.fixture(root)
            stack.enter_context(patch.object(upstream_tests, 'ROOT', root))
            stack.enter_context(patch.object(upstream_tests, 'CACHE', root/'.cache'))
            multicase.validate_case(case)
            self.assertEqual(upstream_tests.references(case), ([configuration.TARGET], [], configuration.POLICY))
            for change in [{'local_configuration_check': False}, {'allowed_file': 'other.toml'},
                           {'python_image': 'python:3.10-slim-bookworm'}, {'dependencies': ['extra']},
                           {'local_compilation_check': True}, {'python_paths': ['lib']},
                           {'head': 'c'*40}, {'source_kind': 'swebench'}]:
                with self.subTest(change=change), self.assertRaises(ValueError):
                    configuration.provenance({**case, **change})
            work = root/'work'; evidence = root/'evidence'; work.mkdir(); evidence.mkdir()
            for role in ('base', 'head'):
                (work/role).mkdir(); (work/role/'pyproject.toml').write_bytes(b'# inert\n')
            metadata = configuration.prepare(case, work, evidence)
            gate = {'context': str(work), 'configuration_harness': metadata}
            configuration.check(case, gate)
            with self.assertRaises(ValueError): configuration.check(case, {'context': str(work)})
            source = work/'base/pyproject.toml'; source.write_bytes(b'# changed\n')
            with self.assertRaises(ValueError): configuration.check(case, gate)
            source.write_bytes(b'# inert\n')
            (work/'configuration-harness'/configuration.TARGET.split('::')[0]).write_bytes(b'# changed\n')
            with self.assertRaises(ValueError): configuration.check(case, gate)

    def test_isolated_runtime_and_no_generation_or_unbound_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); case = self.fixture(root); calls = []
            def command(args, *unused, **kwargs):
                calls.append(args); return {'exit_code': 0, 'timed_out': False}
            with patch.object(multicase, 'command', side_effect=command):
                multicase.execute(case, {'image_id': 'sha256:fixture'}, root/'out', 'test', 'base')
            args = calls[0]
            for value in ['--read-only', '--network=none', '65534:65534',
                          'CI_CONFIG_SOURCE=/source/base/pyproject.toml',
                          '--confcutdir=/configuration-harness', '/configuration-harness/'+configuration.TARGET]:
                self.assertIn(value, args)
            self.assertEqual(args[args.index('/opt/venv/bin/python')+1:args.index('/opt/venv/bin/python')+3], ['-I', '-B'])
            self.assertEqual(calls[1][:3], ['docker', 'rm', '-f'])
            with patch.object(ollama, 'model_info') as info, patch.object(ollama, 'request') as request, patch.object(multicase, 'execute') as execute:
                result = multicase.generate_case(case, 'http://127.0.0.1:11434', folder=root/'generation')
                self.assertEqual(result['attempt_count'], 3); self.assertEqual(result['attempts'], [])
                self.assertEqual(result['status'], 'environment_error')
                for tool in (info, request, execute): tool.assert_not_called()
            with patch.object(dataset, 'real_evidence', return_value=({'source': case, 'environment': {}}, {})):
                with self.assertRaisesRegex(ValueError, 'separately frozen'):
                    dataset.export_real('fixture', root/'missing-assessment', root/'export')
            self.assertFalse((root/'export').exists())

    def test_owned_harness_backend_resolution_and_rejection(self):
        # Only this repository's static harness and mocked backends are exercised.
        namespace = {}; exec(configuration.HARNESS, namespace)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'pyproject.toml'
            for reference, extra, valid in [('fixture.backend', '', True),
                                            ('fixture.backend:entry.point', '', True),
                                            ('fixture.backend;bad', '', False),
                                            ('fixture.backend', 'backend-path=["."]', False)]:
                path.write_text('[build-system]\nbuild-backend="'+reference+'"\n'+extra, encoding='utf-8')
                backend = SimpleNamespace(build_wheel=lambda: None)
                module = SimpleNamespace(entry=SimpleNamespace(point=backend)) if ':' in reference else backend
                with patch.dict('os.environ', CI_CONFIG_SOURCE=str(path)), patch('importlib.import_module', return_value=module) as loader:
                    if valid:
                        namespace['test_build_backend_resolves'](); loader.assert_called_once_with('fixture.backend')
                    else:
                        with self.assertRaises(AssertionError): namespace['test_build_backend_resolves']()
                        loader.assert_not_called()
            path.write_text('[build-system]\nbuild-backend="fixture.backend"', encoding='utf-8')
            with patch.dict('os.environ', CI_CONFIG_SOURCE=str(path)), patch('importlib.import_module', return_value=object()):
                with self.assertRaises(AssertionError): namespace['test_build_backend_resolves']()
