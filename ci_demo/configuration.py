"""Owned backend-resolution smoke, not an application build or functional seed."""
from pathlib import Path
from .common import sha256, write_json
from .compilation import source_provenance, verify_sources

POLICY = 'local_build_backend_resolution_v1'
TARGET = 'test_build_backend.py::test_build_backend_resolves'
QUALIFICATION = 'Local pyproject backend import/hook-presence check only; no wheel build, application test or historical CI claim'
HARNESS = '''import importlib
import os
from pathlib import Path
import re
import tomllib

def test_build_backend_resolves():
    path = Path(os.environ['CI_CONFIG_SOURCE'])
    config = tomllib.loads(path.read_text(encoding='utf-8'))['build-system']
    assert not config.get('backend-path'), 'In-tree backends are outside this local check'
    reference = config['build-backend']
    identifier = r'[A-Za-z_][A-Za-z0-9_]*'
    dotted = identifier + r'(?:\\.' + identifier + r')*'
    assert isinstance(reference, str) and re.fullmatch(dotted + r'(?::' + dotted + r')?', reference)
    module, separator, attribute = reference.partition(':')
    backend = importlib.import_module(module)
    if separator:
        for component in attribute.split('.'):
            backend = getattr(backend, component)
    assert callable(getattr(backend, 'build_wheel', None)), 'Required build_wheel hook missing'
'''


def provenance(case):
    if (case.get('local_compilation_check') or case.get('allowed_file') != 'pyproject.toml'
            or case.get('python_image') != 'python:3.11-slim-bookworm'
            or case.get('python_paths', ['.']) != ['.'] or case.get('system_tools', [])
            or case.get('writable_dirs', []) or case.get('stdlib_distutils', False)
            or case.get('git_test_fixture') or case.get('scm_build_version')):
        raise ValueError('Backend smoke requires an isolated Python3.11 root pyproject recipe')
    return source_provenance(case, POLICY, 'local_configuration_check', 'configuration')


def prepare(case, work, evidence):
    info = provenance(case)
    verify_sources(case, info, work)
    file = work / 'configuration-harness' / TARGET.split('::')[0]
    file.parent.mkdir()
    file.write_text(HARNESS, encoding='utf-8', newline='\n')
    metadata = {'policy': POLICY, 'harness_sha256': sha256(file), 'target': TARGET,
                'qualification': QUALIFICATION}
    write_json(evidence / 'configuration-harness.json', metadata)
    return metadata


def check(case, gate):
    if not case.get('local_configuration_check'):
        return
    info = provenance(case)
    context = Path(gate['context'])
    verify_sources(case, info, context)
    metadata = gate.get('configuration_harness') or {}
    file = context / 'configuration-harness' / TARGET.split('::')[0]
    if (metadata.get('policy') != POLICY or metadata.get('target') != TARGET
            or file.is_symlink() or not file.is_file() or not file.resolve().is_relative_to(context.resolve())
            or sha256(file) != metadata.get('harness_sha256')
            or file.read_bytes() != HARNESS.encode('utf-8')):
        raise ValueError('Configuration harness changed or missing')
