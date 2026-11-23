"""Bind real exports to the exact frozen retrieval implementation."""
import hashlib
import inspect
from pathlib import Path

from .common import ROOT, read_json, sha256, write_json
from .dataset import export_real
from .multicase import is_test, safe_relative
from .retrieval_v3 import retrieve_balanced
from .retrieval_v4 import retrieve_syntax_headers


def checked_retriever(binding):
    path = ROOT / safe_relative(binding['path'])
    if sha256(path) != binding['sha256']:
        raise ValueError('Frozen input protocol changed')
    spec = read_json(path)
    supported = {
        'ci_demo.retrieval_v3.retrieve_balanced': (retrieve_balanced, 'balanced_source_excerpts_v3'),
        'ci_demo.retrieval_v4.retrieve_syntax_headers': (retrieve_syntax_headers, 'balanced_syntax_headers_v4'),
    }
    if spec['retrieval'] not in supported:
        raise ValueError('Unsupported frozen retriever')
    fn, method = supported[spec['retrieval']]
    required = {'ci_demo/retrieval_v3.py', 'ci_demo/diagnosis.py', 'ci_demo/ml.py'}
    if fn is retrieve_syntax_headers:
        required.add('ci_demo/retrieval_v4.py')
    if not required <= spec['source_sha256'].keys():
        raise ValueError('Incomplete retrieval source inventory')
    for name, expected in spec['source_sha256'].items():
        if sha256(ROOT / safe_relative(name)) != expected:
            raise ValueError('Frozen retrieval source changed: ' + name)
    for helper in (is_test, safe_relative):
        if hashlib.sha256(inspect.getsource(helper).encode()).hexdigest() != spec['helper_source_sha256'][helper.__name__]:
            raise ValueError('Frozen retrieval helper changed')
    if spec['parameters'] != {'max_functions': 5, 'max_chars': 6000, 'context': 2048, 'output_budget': 384}:
        raise ValueError('Frozen retrieval budgets differ')
    return fn, method


def export_real_bound(run_id, assessment_path, destination, binding):
    destination = Path(destination)
    retriever, expected_method = checked_retriever(binding)
    metadata = export_real(run_id, assessment_path, destination, retriever=retriever)
    checked_retriever(binding)
    if metadata['retrieval']['method'] != expected_method:
        raise ValueError('Export does not use the declared frozen retriever')
    metadata['input_protocol_sha256'] = binding['sha256']
    metadata['input_protocol_path'] = binding['path']
    write_json(destination / 'manifest.json', metadata)
    return metadata
