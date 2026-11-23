"""Reference-free balanced excerpts; v1/v2 retrieval and historical outputs stay unchanged."""
import re
from .diagnosis import retrieve, failure_log


def excerpt(text, budget, focal=None):
    if len(text)<=budget:return text
    marker='\n[... source lines omitted ...]\n'
    if budget<=len(marker):return text[:budget]
    usable=budget-len(marker)
    if focal is not None:
        lines=text.splitlines(keepends=True)
        offset=sum(len(line) for line in lines[:max(0,focal)])
        start=max(0,min(len(text)-usable,offset-usable//2))
        return marker+text[start:start+usable]
    return text[:usable//2]+marker+text[-(usable-usable//2):]


def retrieve_balanced(tree, log, *, max_functions=5, max_chars=6000, source_overrides=None):
    if isinstance(max_chars,bool) or not isinstance(max_chars,int) or not 100<=max_chars<=6000:
        raise ValueError('Invalid excerpt budget')
    # Five source files are each bounded at250KB by the existing scanner.
    result=retrieve(tree,log,max_functions=max_functions,max_chars=2_000_000,source_overrides=source_overrides)
    snippets=result['snippets'];remaining=max_chars;output=[]
    observed=failure_log(log)
    traces=[(p.replace('\\','/'),int(n)) for p,n in re.findall(r'File ["\']([^"\']+\.py)["\'], line (\d+)',observed)]
    traces += [(p.replace('\\','/'),int(n)) for p,n in re.findall(r'(?:^|\s)([^\s:"\']+\.py):(\d+)',observed)]
    for index,snippet in enumerate(snippets):
        share=remaining//(len(snippets)-index)
        header,body=snippet['text'].split('\n',1);header+='\n'
        if share<=len(header):continue
        focal=next((n-snippet['start_line'] for p,n in traces if (p==snippet['file'] or p.endswith('/'+snippet['file'])) and snippet['start_line']<=n<=snippet['end_line']),None)
        clipped=excerpt(body,share-len(header),focal)
        text=header+clipped
        output.append({**snippet,'text':text,'truncated':len(clipped)<len(body)})
        remaining-=len(text)
    return {**result,'snippets':output,'characters':max_chars-remaining,'method':'balanced_source_excerpts_v3',
            'ranking_method':result['method']}
