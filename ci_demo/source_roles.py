"""Append-only source cohorts preserve existing repo roles and pinned identities."""
from .common import ROOT, read_json, sha256


def allowed_sources(state):
    from .multicase import safe_relative
    from .upstream_tests import cached_file
    roles, candidates, commit_roles = {}, {}, {}
    bindings = [state['source_role_lock'], *state.get('source_role_supplements', [])]
    for index, binding in enumerate(bindings):
        relative = safe_relative(binding['path'])
        literal = ROOT / relative
        if (not relative.startswith('data-manifests/') or literal.is_symlink()
                or not literal.resolve().is_relative_to(ROOT.resolve()) or sha256(literal) != binding['sha256']):
            raise ValueError('Source-role lock changed or escaped repository')
        cohort = read_json(literal)
        if index:
            if cohort.get('schema') != 'v2-source-role-supplement-v1':
                raise ValueError('Unknown source-role supplement')
            for repo, role in cohort['repo_roles'].items():
                if repo not in roles:
                    evidence = cohort['repo_provenance'][repo]
                    pr = read_json(cached_file(evidence['pr_metadata'], evidence['pr_metadata_sha256']))
                    upstream = pr['base']['repo']
                    if upstream['full_name'].lower() != repo.lower() or upstream['fork'] is not False:
                        raise ValueError('New repository canonical/fork provenance unresolved')
        for repo, role in cohort['repo_roles'].items():
            if role not in {'train', 'validation', 'test'} or (repo in roles and roles[repo] != role):
                raise ValueError('Repository role conflict across source cohorts')
            if any(name.lower() == repo.lower() and name != repo for name in roles):
                raise ValueError('Repository case alias must not create another role')
            roles[repo] = role
        for row in cohort['selected']:
            key = row['source_case_id']
            candidate = {**row, 'source_revision': cohort['source_revision']}
            if roles.get(row['repo']) != row['role'] or (key in candidates and candidates[key] != candidate):
                raise ValueError('Source identity or role conflict across cohorts')
            for commit in [row['base_commit'], *([row['upstream_head']] if row.get('upstream_head') else [])]:
                if commit in commit_roles and commit_roles[commit] != row['role']:
                    raise ValueError('Shared commit would cross dataset roles')
                commit_roles[commit] = row['role']
            candidates[key] = candidate
    return roles, candidates


def validate_plan_sources(state, plan):
    roles, candidates = allowed_sources(state)
    if any(roles.get(repo) != role for repo, role in plan['repo_roles'].items()):
        raise ValueError('Plan repository roles differ from frozen source cohorts')
    for row in plan['selected']:
        expected = candidates.get(row['source_case_id'])
        if (expected is None or row['repo'] != expected['repo'] or row['role'] != expected['role']
                or row['base_commit'] != expected['base_commit']):
            raise ValueError('Plan identity/commit differs from frozen source cohorts')
    return candidates
