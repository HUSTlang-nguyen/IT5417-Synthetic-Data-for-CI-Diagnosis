"""Recovered upstream tests stay distinct from dataset-supplied F2P/P2P references."""
import hashlib
import json
import re
from pathlib import Path

from .common import ROOT, CACHE, read_json, sha256

POLICY = 'upstream_pr_recovered_v1'


def cached_file(path, digest):
    from .multicase import safe_relative
    literal = ROOT / safe_relative(path)
    resolved = literal.resolve()
    if literal.is_symlink() or not resolved.is_relative_to(CACHE.resolve()) or not resolved.is_file():
        raise ValueError('Recovered-test evidence must be a cache file')
    if sha256(resolved) != digest:
        raise ValueError('Recovered-test evidence hash mismatch')
    return resolved


def provenance(case):
    from .multicase import patch_paths, is_test, safe_relative
    if (case.get('test_reference_policy') != POLICY or case.get('source_kind') != 'swebench'
            or case.get('dataset_protocol') != 'dataset-v2' or case.get('experiment_role') != 'train'
            or case.get('source_id_matching', 'exact') != 'exact'):
        raise ValueError('Recovered tests require a separately declared v2 train policy')
    info = read_json(cached_file(case['upstream_test_provenance'], case['upstream_test_provenance_sha256']))
    source = read_json(cached_file(info['source_record'], info['source_record_sha256']))
    pr = read_json(cached_file(info['pr_metadata'], info['pr_metadata_sha256']))
    if (info['policy'] != POLICY or info['source_case_id'] != case['source_case_id']
            or info['source_record_sha256'] != case['source_record_sha256']
            or source['instance_id'] != case['source_case_id'] or source['repo'] != case['repo_url'].removeprefix('https://github.com/')
            or source['base_commit'] != case['base'] or source.get('original_split') != 'train'
            or info['base_commit'] != case['base'] or pr['base']['sha'] != case['base']
            or pr['base']['repo']['full_name'].lower() != source['repo'].lower()
            or info['upstream_head'] != pr['head']['sha'] or not re.fullmatch('[0-9a-f]{40}', info['upstream_head'])):
        raise ValueError('Recovered-test source/commit identity mismatch')
    for name in ['FAIL_TO_PASS', 'PASS_TO_PASS']:
        value = source.get(name) or []
        if (json.loads(value) if isinstance(value, str) else value):
            raise ValueError('Supplied dataset test references must not be replaced')
    if case['fail_to_pass'] or case.get('pass_to_pass'):
        raise ValueError('Local expectations must not masquerade as source references')
    repair = cached_file(case['repair_patch'], case['repair_patch_sha256'])
    tests = cached_file(case['test_patch'], case['test_patch_sha256'])
    if (hashlib.sha256(source['patch'].encode('utf-8')).hexdigest() != sha256(repair)
            or info['repair_patch_sha256'] != sha256(repair) or info['test_patch_sha256'] != sha256(tests)):
        raise ValueError('Recovered test or original source repair changed')
    test_paths = patch_paths(tests.read_text(encoding='utf-8'))
    if not all(is_test(path) for path in test_paths) or set(test_paths) != set(case['frozen_test_files']):
        raise ValueError('Recovered test patch must contain only declared upstream tests')
    blobs = info['product_blobs']
    if (not blobs or {row['path'] for row in blobs} != set(patch_paths(repair.read_text(encoding='utf-8')))
            or len({row['path'] for row in blobs}) != len(blobs)):
        raise ValueError('Incomplete recovered product-blob provenance')
    for row in blobs:
        safe_relative(row['path'])
        if is_test(row['path']) or not re.fullmatch('[0-9a-f]{40}', row['upstream_blob']):
            raise ValueError('Invalid recovered product blob')
    for field in ['local_expected_failures', 'local_expected_passes']:
        targets = case.get(field, [])
        if (not isinstance(targets, list) or any(not isinstance(target, str) for target in targets)
                or len(targets) > 600 or len(set(targets)) != len(targets)
                or (field == 'local_expected_failures' and not targets)):
            raise ValueError('Explicit bounded local test expectations required')
        for target in targets:
            if not isinstance(target, str) or '\x00' in target:
                raise ValueError('Invalid local test identity')
            path, separator, node = target.partition('::')
            if not separator or not node or path not in test_paths or target not in case['test_targets']:
                raise ValueError('Local expectations must select declared upstream test nodes')
    return info


def verify_products(case, fixed_tree):
    info = provenance(case)
    for row in info['product_blobs']:
        path = Path(fixed_tree) / row['path']
        if path.is_symlink() or not path.resolve().is_relative_to(Path(fixed_tree).resolve()):
            raise ValueError('Recovered product escaped source tree')
        content = path.read_bytes()
        actual = hashlib.sha1(b'blob ' + str(len(content)).encode() + b'\0' + content).hexdigest()
        if actual != row['upstream_blob']:
            raise ValueError('Repaired product differs from pinned upstream blob')


def references(case):
    if case.get('local_configuration_check'):
        from . import configuration
        configuration.provenance(case)
        return [configuration.TARGET], [], configuration.POLICY
    if case.get('local_compilation_check'):
        from . import compilation
        compilation.provenance(case)
        return [compilation.TARGET], [], compilation.POLICY
    if case.get('test_reference_policy') is None:
        return case['fail_to_pass'], case.get('pass_to_pass', []), 'dataset_supplied'
    provenance(case)
    return case['local_expected_failures'], case.get('local_expected_passes', []), 'upstream_recovered_local'
