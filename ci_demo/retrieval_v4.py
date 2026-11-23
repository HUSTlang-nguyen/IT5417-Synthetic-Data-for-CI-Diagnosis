"""Observable lexical scope for syntax failures; historical v3 stays unchanged."""
import ast
import io
from pathlib import Path
import re
import tokenize

from .diagnosis import failure_log
from .retrieval_v3 import excerpt, retrieve_balanced


def enclosing_header(text, line):
    depth, scopes, pending, waiting, ready, last = 0, [], None, None, None, None
    try:
        for token in tokenize.generate_tokens(io.StringIO(text).readline):
            if token.start[0] > line:
                break
            if token.type == tokenize.INDENT:
                depth += 1
                if ready:
                    scopes.append((*ready, depth))
                ready = None
            elif token.type == tokenize.DEDENT:
                depth -= 1
                scopes = [scope for scope in scopes if scope[3] <= depth]
            elif token.type == tokenize.NAME:
                if waiting:
                    pending = (waiting[0], token.string, waiting[1])
                    waiting = None
                elif token.string in {'class', 'def'}:
                    waiting = (token.string, token.start[0])
                    pending = None
                last = token.string
            elif token.type == tokenize.NEWLINE:
                ready = pending if last == ':' else None
                pending, last = None, None
            elif token.type not in {tokenize.NL, tokenize.COMMENT, tokenize.ENDMARKER}:
                last = token.string
                waiting = None
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass
    functions = [scope for scope in scopes if scope[0] == 'def']
    if not functions:
        return None
    return {'function': '.'.join(scope[1] for scope in scopes),
            'start_line': functions[-1][2], 'header_lines': [scope[2] for scope in scopes]}


def retrieve_syntax_headers(tree, log, *, max_functions=5, max_chars=6000, source_overrides=None):
    result = retrieve_balanced(tree, log, max_functions=max_functions, max_chars=max_chars,
                              source_overrides=source_overrides)
    observed = failure_log(log)
    traces = [(p.replace('\\', '/'), int(n)) for p, n in
              re.findall(r'File ["\']([^"\']+\.py)["\'], line (\d+)', observed)]
    traces += [(p.replace('\\', '/'), int(n)) for p, n in
               re.findall(r'(?:^|\s)([^\s:"\']+\.py):(\d+)', observed)]
    output = []
    for snippet in result['snippets']:
        file = snippet['file']
        line = next((n for p, n in traces if p == file or p.endswith('/' + file)), None)
        if (snippet['function'] != '<module>' or line is None
                or not re.search(r'\b(?:SyntaxError|IndentationError|TabError)\b', observed)):
            output.append(snippet)
            continue
        source = (source_overrides or {}).get(file)
        if source is None:
            source = (Path(tree) / file).read_text(encoding='utf-8', errors='replace')
        try:
            ast.parse(source.lstrip('\ufeff'))
        except SyntaxError:
            scope = enclosing_header(source, line)
        else:
            scope = None
        lines = source.splitlines(keepends=True)
        if not scope or not 1 <= line <= len(lines):
            output.append(snippet)
            continue
        start, name = scope['start_line'], scope['function']
        header = f'{file}::{name} lines {start}-{line}\n'
        header += lines[start-1]
        budget = len(snippet['text']) - len(header)
        if budget < 64:
            output.append(snippet)
            continue
        window_start = max(start, line-9)
        body = ''.join(lines[window_start:line])
        if window_start > start:
            body = '[... source lines omitted ...]\n' + body
        text = header + excerpt(body, budget, max(0, line-window_start-1))
        output.append({**snippet, 'function': name, 'start_line': start, 'end_line': line,
                       'text': text, 'truncated': True, 'scope_header_lines': scope['header_lines'],
                       'span_kind': 'lexical_header_to_observed_syntax_line'})
    return {**result, 'snippets': output, 'characters': sum(len(s['text']) for s in output),
            'method': 'balanced_syntax_headers_v4', 'parent_method': result['method']}
