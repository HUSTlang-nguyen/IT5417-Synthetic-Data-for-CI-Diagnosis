"""Additive frozen binding; never edits the historical v3/v4 verifier."""
from pathlib import Path
from .common import ROOT, read_json, sha256, write_json
from .multicase import safe_relative
from . import input_protocol
from .retrieval_v5 import retrieve_configuration, METHOD


def checked_retriever(binding):
    def checked_path(name, digest):
        path = ROOT / safe_relative(name)
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(ROOT.resolve()) or sha256(path) != digest:
            raise ValueError('Frozen configuration input source/protocol changed: ' + name)
        return path
    spec = read_json(checked_path(binding['path'], binding['sha256']))
    if spec.get('protocol') != 'dataset-v2-input-v5' or spec.get('retrieval') != 'ci_demo.retrieval_v5.retrieve_configuration':
        raise ValueError('Unsupported frozen configuration retriever')
    parent = spec['parent_protocol']
    parent_spec = read_json(checked_path(parent['path'], parent['sha256']))
    if parent_spec.get('protocol') != 'dataset-v2-input-v4':
        raise ValueError('Configuration input requires frozen v4 parent')
    input_protocol.checked_retriever(parent)
    if spec['parameters'] != parent_spec['parameters']:
        raise ValueError('Frozen configuration retrieval budgets differ')
    required = {'ci_demo/retrieval_v5.py', 'ci_demo/input_protocol_v5.py', 'ci_demo/dataset.py'}
    if set(spec['source_sha256']) != required:
        raise ValueError('Incomplete configuration retrieval source inventory')
    for name, digest in spec['source_sha256'].items():
        checked_path(name, digest)
    return retrieve_configuration, METHOD


def export_real_bound(run_id, assessment_path, destination, binding):
    from .dataset import export_real
    retriever, expected_method = checked_retriever(binding)
    destination = Path(destination)
    metadata = export_real(run_id, assessment_path, destination, retriever=retriever, input_protocol=binding)
    checked_retriever(binding)
    if metadata['retrieval']['method'] != expected_method:
        raise ValueError('Export does not use the declared frozen configuration retriever')
    metadata.update(input_protocol_sha256=binding['sha256'], input_protocol_path=binding['path'])
    write_json(destination / 'manifest.json', metadata)
    return metadata
