"""Root configuration for the declared backend smoke; other inputs retain v4."""
from pathlib import Path
from .retrieval_v4 import retrieve_syntax_headers
from .retrieval_v3 import excerpt
from .diagnosis import failure_log

METHOD = 'syntax_headers_and_owned_backend_config_v5'


def retrieve_configuration(tree, log, *, max_functions=5, max_chars=6000, source_overrides=None):
    if (isinstance(max_functions, bool) or not isinstance(max_functions, int) or not 1 <= max_functions <= 5
            or isinstance(max_chars, bool) or not isinstance(max_chars, int) or not 100 <= max_chars <= 6000):
        raise ValueError('Invalid retrieval bounds')
    root = Path(tree).resolve()
    if not root.is_dir():
        raise ValueError('Source root missing')
    if source_overrides is not None and not isinstance(source_overrides, dict):
        raise ValueError('Source overrides must map existing paths to source text')
    observed = failure_log(log)
    path = root / 'pyproject.toml'
    # This signal belongs to the owned smoke, not arbitrary package/import errors.
    if 'CI_CONFIG_SOURCE' in observed and "config['build-backend']" in observed:
        if source_overrides:
            raise ValueError('Configuration-only diagnosis does not accept candidate overlays')
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root):
            raise ValueError('Declared backend config missing or outside pinned source')
        if path.stat().st_size > 250_000:
            raise ValueError('Declared backend config exceeds scanner limit')
        text = path.read_text(encoding='utf-8', errors='replace')
        lines = text.splitlines()
        header = f'pyproject.toml::<module> lines 1-{len(lines)}\n'
        content = header + excerpt(text, max_chars - len(header))
        snippet = {'file': 'pyproject.toml', 'function': '<module>', 'start_line': 1,
                   'end_line': len(lines), 'text': content, 'truncated': len(content) < len(header) + len(text),
                   'score': 1000, 'span_kind': 'owned_backend_config'}
        return {'snippets': [snippet], 'production_files_scanned': 1, 'ranked_function_count': 1,
                'characters': len(content), 'method': METHOD,
                'qualification': 'Owned local backend smoke config; no repair, reference or application-build claim'}
    result = retrieve_syntax_headers(root, log, max_functions=max_functions, max_chars=max_chars,
                                     source_overrides=source_overrides)
    return {**result, 'method': METHOD, 'parent_method': result['method']}
