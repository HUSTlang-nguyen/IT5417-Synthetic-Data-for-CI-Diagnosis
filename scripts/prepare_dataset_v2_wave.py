"""Prepare an append-only wave using same-repo/version recipes with prior environment fixes."""
from pathlib import Path
import copy
import json
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ci_demo.common import CACHE,read_json,write_json,sha256,now
from ci_demo.multicase import validate_case


def prepare(destination, per_repo=4):
    destination=Path(destination)
    if destination.exists():raise ValueError('Never overwrite an execution plan')
    if isinstance(per_repo,bool) or not isinstance(per_repo,int) or not 1<=per_repo<=140:
        raise ValueError('Per-repo wave size must be between1and140')
    wave=destination.stem.removeprefix('dataset-v2-')
    if not re.fullmatch(r'[a-zA-Z0-9-]{1,32}',wave):raise ValueError('Invalid wave identifier')
    roles=read_json(ROOT/'data-manifests/dataset-v2-source-roles.json')
    rows={r['instance_id']:r for name in ['records.json','test-records.json'] for r in read_json(CACHE/'dataset-v1-source'/name)}
    tried=set()
    pointers=[ROOT/'runs/experiment-20261111T192045721211Z/manifest.json',ROOT/'runs'/read_json(CACHE/'dataset-v2-active.json')['run_id']/'manifest.json']
    for pointer in pointers:
        for op in read_json(pointer)['operations'].values():
            identity=op.get('artifacts',{}).get('case_id')
            if identity:tried.add(read_json(ROOT/'cases'/identity/'case.json')['source_case_id'])
    prototypes={}
    for file in sorted((ROOT/'cases').glob('*/case.json')):
        case=read_json(file);row=rows.get(case.get('source_case_id'))
        if not row or case.get('source_kind')!='swebench' or case.get('dataset_protocol')=='dataset-v2':continue
        key=(row['repo'],row['version'])
        score=sum(tag in case['case_id'] for tag in ['env2','-r1','deps','scm'])
        if key not in prototypes or score>prototypes[key][0]:prototypes[key]=(score,case)
    selected=[]
    for repo,role in sorted(roles['repo_roles'].items()):
        if role!='train':continue
        choices=[r for r in roles['selected'] if r['repo']==repo and r['role']=='train' and r['source_case_id'] not in tried and (repo,r['source_version']) in prototypes]
        for item in choices[:per_repo]:
            source=rows[item['source_case_id']];parent=prototypes[(repo,item['source_version'])][1];case=copy.deepcopy(parent)
            identity=item['source_case_id']+'-ds2-'+wave
            raw=CACHE/'dataset-v2-source/cases'/identity
            if raw.exists() or (ROOT/'cases'/identity).exists():raise ValueError('Existing profile; inspect instead of overwrite')
            raw.mkdir(parents=True);write_json(raw/'source-record.json',source)
            for name,field in [('repair.patch','patch'),('test.patch','test_patch')]:
                (raw/name).write_text(source[field],encoding='utf-8',newline='\n')
            f2p=json.loads(source['FAIL_TO_PASS']) if isinstance(source['FAIL_TO_PASS'],str) else source['FAIL_TO_PASS']
            p2p=json.loads(source['PASS_TO_PASS']) if isinstance(source['PASS_TO_PASS'],str) else source['PASS_TO_PASS']
            case.update(case_id=identity,source_case_id=item['source_case_id'],record_id=item['source_case_id'],
                base=item['base_commit'],head='base+repair:'+sha256(raw/'repair.patch'),allowed_file=item['product_files'][0],
                experiment_role='train',focus_line=1,fail_to_pass=f2p,pass_to_pass=p2p,
                test_targets=sorted({t.split('::')[0] for t in f2p+p2p}),frozen_test_files=item['test_files'],
                repair_patch=(raw/'repair.patch').relative_to(ROOT).as_posix(),repair_patch_sha256=sha256(raw/'repair.patch'),
                test_patch=(raw/'test.patch').relative_to(ROOT).as_posix(),test_patch_sha256=sha256(raw/'test.patch'),
                source_record_sha256=sha256(raw/'source-record.json'),dataset_protocol='dataset-v2',recipe_parent_case_id=parent['case_id'])
            if repo=='pvlib/pvlib-python' and not any(d.startswith('pytest-mock') for d in case['dependencies']):
                case['dependencies'].append('pytest-mock==3.14.0');case['pytest_plugins']=['pytest_mock']
            validate_case(case);write_json(ROOT/'cases'/identity/'case.json',case)
            selected.append({**item,'case_id':identity,'case_sha256':sha256(ROOT/'cases'/identity/'case.json')})
    assert len({x['source_case_id'] for x in selected})==len(selected)
    assert not {x['source_case_id'] for x in selected}&tried
    write_json(destination,{'created_at':now(),'source_role_lock_sha256':sha256(ROOT/'data-manifests/dataset-v2-source-roles.json'),
        'repo_roles':roles['repo_roles'],'selected':selected,'targets':{'real':1000,'train':700,'validation':150,'test':150},
        'qualification':'Bounded new-source train wave; metadata/version recipe matching only, not reproduced samples. Pinned license checked before build.'})
    print({'prepared':len(selected),'case_ids':[r['case_id'] for r in selected]})


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--destination',type=Path,required=True)
    parser.add_argument('--per-repo',type=int,default=4)
    args=parser.parse_args()
    prepare(args.destination,args.per_repo)
