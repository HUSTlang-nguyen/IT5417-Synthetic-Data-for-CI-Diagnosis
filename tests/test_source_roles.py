from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ci_demo.common import write_json, sha256
from ci_demo import source_roles, upstream_tests


class SourceRoleTests(unittest.TestCase):
    def test_append_only_cohort_keeps_old_plans_valid_and_rejects_role_or_commit_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);old={'source_case_id':'old-1','repo':'example/old','role':'test','base_commit':'a'*40}
            new={'source_case_id':'new-1','repo':'example/new','role':'train','base_commit':'b'*40}
            base={'repo_roles':{'example/old':'test'},'source_revision':'c'*40,'selected':[old]}
            write_json(root/'data-manifests/base.json',base)
            write_json(root/'cache/pr.json',{'base':{'repo':{'full_name':'example/new','fork':False}}})
            supplement={'schema':'v2-source-role-supplement-v1','repo_roles':{'example/new':'train'},
                'source_revision':'d'*40,'selected':[new],'repo_provenance':{'example/new':{
                    'pr_metadata':'cache/pr.json','pr_metadata_sha256':sha256(root/'cache/pr.json')}}}
            write_json(root/'data-manifests/extra.json',supplement)
            state={'source_role_lock':{'path':'data-manifests/base.json','sha256':sha256(root/'data-manifests/base.json')},
                'source_role_supplements':[{'path':'data-manifests/extra.json','sha256':sha256(root/'data-manifests/extra.json')}]}
            with patch.object(source_roles,'ROOT',root),patch.object(upstream_tests,'ROOT',root),patch.object(upstream_tests,'CACHE',root/'cache'):
                for row in [old,new]:
                    plan={'repo_roles':{row['repo']:row['role']},'selected':[row]}
                    self.assertIn(row['source_case_id'],source_roles.validate_plan_sources(state,plan))
                with self.assertRaises(ValueError):source_roles.validate_plan_sources(state,{'repo_roles':{'example/old':'train'},'selected':[old]})
                with self.assertRaises(ValueError):source_roles.validate_plan_sources(state,{'repo_roles':{'example/new':'train'},'selected':[{**new,'base_commit':'e'*40}]})
                supplement['selected'][0]['base_commit']=old['base_commit']
                write_json(root/'data-manifests/extra.json',supplement)
                state['source_role_supplements'][0]['sha256']=sha256(root/'data-manifests/extra.json')
                with self.assertRaisesRegex(ValueError,'Shared commit'):source_roles.allowed_sources(state)
                (root/'data-manifests/extra.json').write_text('tampered')
                with self.assertRaises(ValueError):source_roles.allowed_sources(state)

    def test_new_fork_or_changed_existing_role_cannot_be_admitted(self):
        for fork,role in [(True,'train'),(False,'validation')]:
            with self.subTest(fork=fork),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)
                write_json(root/'data-manifests/base.json',{'repo_roles':{'example/old':'test'},'selected':[],'source_revision':'a'*40})
                write_json(root/'cache/pr.json',{'base':{'repo':{'full_name':'example/new','fork':fork}}})
                extra={'schema':'v2-source-role-supplement-v1','repo_roles':{'example/new':'train','example/old':role},
                    'selected':[],'source_revision':'b'*40,'repo_provenance':{'example/new':{
                      'pr_metadata':'cache/pr.json','pr_metadata_sha256':sha256(root/'cache/pr.json')}}}
                write_json(root/'data-manifests/extra.json',extra)
                state={'source_role_lock':{'path':'data-manifests/base.json','sha256':sha256(root/'data-manifests/base.json')},
                    'source_role_supplements':[{'path':'data-manifests/extra.json','sha256':sha256(root/'data-manifests/extra.json')}]}
                with patch.object(source_roles,'ROOT',root),patch.object(upstream_tests,'ROOT',root),patch.object(upstream_tests,'CACHE',root/'cache'):
                    with self.assertRaises(ValueError):source_roles.allowed_sources(state)
