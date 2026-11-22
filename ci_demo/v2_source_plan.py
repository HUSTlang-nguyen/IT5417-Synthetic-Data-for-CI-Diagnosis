"""Freeze source identities/repository roles from pinned cached metadata, before execution."""
from collections import Counter
import json
from pathlib import Path

from .common import CACHE, ROOT, now, read_json, sha256, write_json
from .multicase import patch_paths, is_test

ROLES = {
    **{r:'train' for r in ['sympy/sympy','pydicom/pydicom','pvlib/pvlib-python','pylint-dev/astroid',
        'marshmallow-code/marshmallow','sqlfluff/sqlfluff','pylint-dev/pylint','sphinx-doc/sphinx','pytest-dev/pytest','pallets/flask']},
    **{r:'validation' for r in ['django/django','matplotlib/matplotlib','mwaskom/seaborn','pyvista/pyvista']},
    **{r:'test' for r in ['psf/requests','pydata/xarray','scikit-learn/scikit-learn']}}


def screen(rows, excluded, exposed):
    selected, rejected, seen = [], Counter(), set()
    for row in rows:
        identity, repo = row['instance_id'], row['repo']
        if identity in seen:
            rejected['duplicate_source_identity'] += 1; continue
        seen.add(identity)
        role = ROLES.get(repo)
        if role is None or (role != 'train' and repo.lower() in exposed):
            rejected['unassigned_or_previously_exposed_repo'] += 1; continue
        if identity in excluded:
            rejected['v1_heldout_development_only'] += 1; continue
        try:
            f2p = json.loads(row['FAIL_TO_PASS']) if isinstance(row['FAIL_TO_PASS'],str) else row['FAIL_TO_PASS']
            p2p = json.loads(row.get('PASS_TO_PASS') or '[]') if isinstance(row.get('PASS_TO_PASS',''),str) else row.get('PASS_TO_PASS',[])
            product = sorted(p for p in patch_paths(row['patch']) if p.endswith('.py') and not is_test(p))
            tests = sorted(p for p in patch_paths(row['test_patch']) if p.endswith('.py') and is_test(p))
            if not f2p or not tests or not 1 <= len(product) <= 5 or not all(isinstance(t,str) for t in f2p+p2p):
                raise ValueError('Unsupported metadata')
        except (KeyError,ValueError,TypeError):
            rejected['missing_or_unsupported_patch_test_metadata'] += 1; continue
        selected.append({'source_case_id':identity,'repo':repo,'role':role,'base_commit':row['base_commit'],
            'source_version':row['version'],'product_files':product,'test_files':tests,
            'repair_bytes':len(row['patch'].encode()),'f2p_count':len(f2p),'p2p_count':len(p2p),
            'case_recipe_status':'not_prepared','license_status':'requires_pinned_file_evidence'})
    selected.sort(key=lambda r:(len(r['product_files']),r['repair_bytes'],r['source_case_id']))
    return selected,dict(rejected)


def prepare(destination):
    destination=Path(destination)
    if destination.exists():raise ValueError('Never overwrite a frozen source plan')
    files=[CACHE/'dataset-v1-source/records.json',CACHE/'dataset-v1-source/test-records.json']
    lock=read_json(CACHE/'dataset-v1/locked-v1.1.json')
    excluded={r['sample_id'] for r in lock['records'] if r['role']!='train'}
    exposed={'astropy/astropy'}
    for group in read_json(ROOT/'data-manifests/development-groups-v1.json')['groups']:
        exposed.update(url.removeprefix('https://github.com/').lower() for url in group['repo_urls'])
    exposed.update(r['repo_url'].removeprefix('https://github.com/').lower() for r in lock['records'])
    # v1 already indexed the full source; only metadata-complete identities enter this new screen.
    rows=[r for p in files for r in read_json(p) if r.get('patch') and r.get('test_patch') and r.get('FAIL_TO_PASS') not in (None,'','[]',[])]
    if len({r['instance_id'] for r in rows})>5000:raise ValueError('Source screen cap exceeded')
    selected,rejected=screen(rows,excluded,exposed)
    plan={'created_at':now(),'schema':'v2-source-role-lock-v1','repo_roles':ROLES,
        'sources':{p.relative_to(ROOT).as_posix():sha256(p) for p in files},
        'source_revision':read_json(ROOT/'data-manifests/dataset-v1-plan-scm-ready.json')['source_revision'],
        'exposed_repositories':sorted(exposed),'excluded_v1_heldout_ids':sorted(excluded),
        'screened_source_identities':len({r['instance_id'] for r in rows}),
        'selected':selected,'rejection_counts':rejected,
        'selection_order':'product_file_count, repair_bytes, source_case_id; no model/test outcomes',
        'qualification':'Frozen SWE repository roles and candidate metadata only; not execution evidence, recipe/license clearance or selected dataset. AIDev supplements require separate append-only role lock for new repositories before execution.'}
    write_json(destination,plan)
    return {'candidates':len(selected),'by_role':dict(Counter(r['role'] for r in selected)),
            'repositories':dict(Counter(r['repo'] for r in selected)),'rejected':rejected}


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination',type=Path,required=True)
    print(prepare(parser.parse_args().destination))
