"""Declared local compilation checks, separate from upstream regression tests."""
from .common import read_json, sha256, write_json
from .upstream_tests import cached_file
from pathlib import Path
import hashlib
import re

POLICY = 'local_compilation_smoke_v1'
TARGET = 'test_source_compiles.py::test_source_compiles'
HARNESS = '''import os
from pathlib import Path

def test_source_compiles():
    path = Path(os.environ['CI_COMPILE_SOURCE'])
    compile(path.read_bytes(), str(path), 'exec')
'''


def provenance(case):
    return source_provenance(case, POLICY, 'local_compilation_check', 'compilation')


def source_provenance(case, policy, flag, prefix):
    """Bind a declared owned local check to one original AIDev file change."""
    if (case.get(flag) is not True or case.get('source_kind') != 'aidev'
            or case.get('dataset_protocol') != 'dataset-v2' or case.get('frozen_test_files') != []
            or case.get('experiment_role') not in {'train', 'validation', 'test'}
            or case.get('test_targets') != [case['allowed_file']]
            or case.get('fail_to_pass') != [] or case.get('pass_to_pass') != []
            or case.get('install_project', True) or case.get('dependencies')
            or case.get('pytest_plugins') or case.get('test_workdir') != 'work'
            or case.get('source_id_matching', 'exact') != 'exact'
            or case.get('test_reference_policy') is not None):
        raise ValueError('Owned local checks require a separate dependency-free v2 AIDev recipe')
    info = read_json(cached_file(case[prefix + '_provenance'], case[prefix + '_provenance_sha256']))
    row = read_json(cached_file(info['source_record'], info['source_record_sha256']))
    pr = read_json(cached_file(info['pr_metadata'], info['pr_metadata_sha256']))
    files = read_json(cached_file(info['pr_files'], info['pr_files_sha256']))
    repo = case['repo_url'].removeprefix('https://github.com/')
    if (info['policy'] != policy or info['source_case_id'] != case['source_case_id']
            or info['source_record_sha256'] != case['source_record_sha256']
            or str(row['id']) != str(case['record_id']) or row['number'] != pr['number']
            or row['repo_url'] != 'https://api.github.com/repos/' + repo
            or pr['base']['repo']['full_name'].lower() != repo.lower()
            or row['merged_at'] != pr['merged_at'] or not pr['merged_at']
            or pr['base']['sha'] != case['base'] or pr['head']['sha'] != case['head']
            or pr['changed_files'] != 1 or len(files) != 1
            or files[0]['filename'] != case['allowed_file'] or files[0]['status'] != 'modified'
            or set(info.get('source_blobs', {})) != {'base', 'head'}
            or any(not isinstance(value, str) or not re.fullmatch('[0-9a-f]{40}', value)
                   for value in info['source_blobs'].values())
            or files[0].get('sha') != info['source_blobs']['head']
            or info['python_image'] != case['python_image'] or not info.get('runtime_qualification')):
        raise ValueError('Compilation source/commit/runtime provenance mismatch')
    return info


def prepare(case, work, evidence):
    info = provenance(case)
    verify_sources(case, info, work)
    file = work / 'compilation-harness' / TARGET.split('::')[0]
    file.parent.mkdir()
    file.write_text(HARNESS, encoding='utf-8', newline='\n')
    metadata = {'policy': POLICY, 'harness_sha256': sha256(file), 'target': TARGET,
                'qualification': 'Local syntax compilation only; no module import/execution, upstream test result or historical CI claim'}
    write_json(evidence / 'compilation-harness.json', metadata)
    return metadata


def verify_sources(case, info, context):
    for role in ('base', 'head'):
        file = Path(context) / role / case['allowed_file']
        if file.is_symlink() or not file.resolve().is_relative_to((Path(context) / role).resolve()):
            raise ValueError('Compilation source escaped pinned tree')
        data = file.read_bytes()
        digest = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if digest != info['source_blobs'][role]:
            raise ValueError('Compilation source differs from pinned Git blob')


def check(case, gate):
    if not case.get('local_compilation_check'):
        return
    info = provenance(case)
    metadata = gate.get('compilation_harness') or {}
    context = Path(gate['context'])
    verify_sources(case, info, context)
    file = context / 'compilation-harness' / TARGET.split('::')[0]
    if (metadata.get('policy') != POLICY or metadata.get('target') != TARGET
            or file.is_symlink() or not file.is_file() or not file.resolve().is_relative_to(context.resolve())
            or sha256(file) != metadata.get('harness_sha256')
            or file.read_bytes() != HARNESS.encode('utf-8')):
        raise ValueError('Compilation harness changed or missing')
