"""Build small presentation assets from the frozen, portable reporting snapshot."""
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
F = json.loads((HERE / 'facts.json').read_text(encoding='utf-8'))

def escape(value):
    return ''.join({'\\':r'\textbackslash{}','_':r'\_','%':r'\%','&':r'\&','#':r'\#','{':r'\{','}':r'\}'}.get(c,c) for c in str(value))

def table(name, scores):
    rows=[r'\providecommand{\baselineModelName}{M1-P2}',r'\begin{tabular}{lrrrrrr}\toprule',r'Model & Acc. (\%) & Macro-F1 & File T1 & Hàm T1 & Joint & Invalid\\\midrule']
    for model,m in scores.items():
        v=lambda k: '--' if model=='M0' else str(m['counts'][k])
        label = r'\baselineModelName{}' if model == 'M1-P2' else model
        rows.append(f"{label} & {m['classification_accuracy']*100:.2f} & {m['macro_f1']:.4f} & {v('file_top1_correct')} & {v('function_top1_correct')} & {v('joint_top1_correct')} & {v('invalid_output')}"+r'\\')
    rows += [r'\bottomrule\end{tabular}']
    (HERE/name).write_text('\n'.join(rows),encoding='utf-8')

table('test-table.tex', F['evaluation']['test_metrics'])
table('validation-table.tex', F['validation']['scores'])
from collections import defaultdict
repos=defaultdict(lambda:{'real':0,'synthetic':0,'role':None})
for role,stats in F['stats'].items():
    for repo,total in stats['repos'].items():
        repos[repo]['role']=role
        repos[repo]['real']=total
# The frozen selection is read only here when available; the exported table remains portable.
lock=HERE.parent.parent/'.cache/dataset-v1/locked-v1.1.json'
if lock.exists():
    for row in json.loads(lock.read_text(encoding='utf-8'))['records']:
        if row['sample_id'].startswith('synthetic-'):
            repo=row['repo_url'].split('github.com/')[-1]
            repos[repo]['synthetic']+=1;repos[repo]['real']-=1
    rows=[r'\begin{tabular}{lrrl}\toprule',r'Repo & Real & Synthetic & Vai trò\\\midrule']
    for repo,v in repos.items():rows.append(escape(repo.rsplit('/',1)[-1])+f" & {v['real']} & {v['synthetic']} & "+{'train':'Train','validation':'Validation','test':'Test'}[v['role']]+r'\\')
    rows += [r'\bottomrule\end{tabular}']
    (HERE/'repo-table.tex').write_text('\n'.join(rows),encoding='utf-8')
    F['repo_breakdown']=dict(repos)
    (HERE/'facts.json').write_text(json.dumps(F,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=[r'\begin{tikzpicture}[x=1cm,y=1cm,>=stealth, every node/.style={font=\small,align=center}]']
for row,values in enumerate(F['architecture']):
    for col,value in enumerate(values):
        lines.append(r'\node[draw,minimum height=.75cm,text width=2.8cm] (n'+str(row)+str(col)+f') at ({col*3.45},{-row*1.2}) '+'{'+escape(value)+'};')
        if col:lines.append(f'\\draw[->] (n{row}{col-1}) -- (n{row}{col});')
lines += [r'\draw[->,dashed] (n03.south) -- ++(0,-.22) -| (n10.north);',r'\draw[->,dashed] (n13.south) -- ++(0,-.22) -| (n20.north);',r'\end{tikzpicture}']
(HERE/'architecture.tex').write_text('\n'.join(lines),encoding='utf-8')
for kind,e in F['examples'].items():
    target={k:e['reference'][k] for k in ['cause_type','locations','explanation']}
    (HERE/f'{kind}-target.txt').write_text(json.dumps(target,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Generated tables, shared architecture and unmodified target-field excerpts')
