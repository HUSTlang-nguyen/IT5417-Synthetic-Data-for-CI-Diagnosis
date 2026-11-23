"""Software fixtures only; upstream source is never compiled on the host."""
import ast
import hashlib
from contextlib import ExitStack
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ci_demo import compilation, upstream_tests, multicase, ollama
from ci_demo.common import write_json, sha256


class CompilationTests(unittest.TestCase):
    def fixture(self, root):
        cache=root/'.cache';cache.mkdir()
        paths={}
        def save(name,value):
            p=cache/(name+'.json');write_json(p,value);paths[name]=p
            return str(p.relative_to(root)).replace('\\','/'),sha256(p)
        row={'id':1,'number':2,'repo_url':'https://api.github.com/repos/example/project','merged_at':'2025-01-01T00:00:00Z'}
        pr={'number':2,'merged_at':row['merged_at'],'changed_files':1,
            'base':{'sha':'a'*40,'repo':{'full_name':'example/project'}},'head':{'sha':'b'*40}}
        info={'policy':compilation.POLICY,'source_case_id':'aidev-1','python_image':'python:3.11-slim-bookworm',
              'runtime_qualification':'Declared local Python3.11 syntax smoke, not historical CI runtime',
              'source_blobs':dict.fromkeys(('base','head'),hashlib.sha1(b'blob 8\0# inert\n').hexdigest())}
        for name,value in [('source_record',row),('pr_metadata',pr),('pr_files',[{'filename':'module.py','status':'modified','sha':info['source_blobs']['head']}])]:
            info[name],info[name+'_sha256']=save(name,value)
        relative,digest=save('provenance',info)
        case={'source_case_id':'aidev-1','record_id':1,'source_kind':'aidev','dataset_protocol':'dataset-v2',
              'case_id':'compilation-fixture','runner_kind':'python-source-v2','split':'development',
              'experiment_role':'train','license':'MIT','resources':{'memory_mb':512,'cpus':1},
              'repo_url':'https://github.com/example/project','base':'a'*40,'head':'b'*40,
              'local_compilation_check':True,'frozen_test_files':[],'allowed_file':'module.py',
              'test_targets':['module.py'],'fail_to_pass':[],'pass_to_pass':[],'install_project':False,
              'dependencies':[],'test_workdir':'work','source_record_sha256':info['source_record_sha256'],'python_image':info['python_image'],
              'compilation_provenance':relative,'compilation_provenance_sha256':digest}
        return case,paths

    def test_provenance_scope_and_harness_immutability(self):
        with tempfile.TemporaryDirectory() as tmp,ExitStack() as stack:
            root=Path(tmp);case,paths=self.fixture(root)
            stack.enter_context(patch.object(upstream_tests,'ROOT',root))
            stack.enter_context(patch.object(upstream_tests,'CACHE',root/'.cache'))
            compilation.provenance(case)
            multicase.validate_case(case)
            self.assertEqual(upstream_tests.references(case),([compilation.TARGET],[],compilation.POLICY))
            for changes in [{'source_kind':'swebench'},{'dataset_protocol':'dataset-v1'},
                            {'dependencies':['numpy==1.0']},{'install_project':True},
                            {'test_targets':['other.py']},{'fail_to_pass':['fake']},{'head':'c'*40},
                            {'local_compilation_check':False},{'test_reference_policy':'upstream_pr_recovered_v1'}]:
                with self.subTest(changes=changes),self.assertRaises(ValueError):
                    compilation.provenance({**case,**changes})
            work=root/'work';work.mkdir();evidence=root/'evidence';evidence.mkdir()
            for role in ('base','head'):
                (work/role).mkdir();(work/role/'module.py').write_bytes(b'# inert\n')
            metadata=compilation.prepare(case,work,evidence)
            gate={'context':str(work),'compilation_harness':metadata}
            compilation.check(case,gate)
            self.assertEqual(metadata['policy'],compilation.POLICY)
            with self.assertRaises(ValueError):compilation.check(case,{'context':str(work)})
            file=work/'compilation-harness/test_source_compiles.py';file.write_text('# changed\n')
            with self.assertRaises(ValueError):compilation.check(case,gate)
            paths['pr_metadata'].write_text('{}')
            with self.assertRaises(ValueError):compilation.provenance(case)

    def test_runtime_isolates_python_and_generation_is_refused_before_any_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);case,_=self.fixture(root);calls=[]
            def command(args,folder,name,**kwargs):
                calls.append(args)
                return {'exit_code':0,'timed_out':False}
            with patch.object(multicase,'command',side_effect=command):
                multicase.execute(case,{'image_id':'sha256:fixture'},root/'out','test','base')
            args=calls[0]
            self.assertIn('--read-only',args);self.assertIn('--network=none',args)
            self.assertIn('CI_COMPILE_SOURCE=/source/base/module.py',args)
            self.assertIn('--confcutdir=/compilation-harness',args)
            self.assertIn('/compilation-harness/'+compilation.TARGET,args)
            pos=args.index('/opt/venv/bin/python')
            self.assertEqual(args[pos+1:pos+3],['-I','-B'])
            with patch.object(ollama,'request') as request,patch.object(ollama,'model_info') as info,patch.object(multicase,'execute') as execute:
                result=multicase.generate_case(case,'http://127.0.0.1:11434',folder=root/'generation')
            self.assertEqual(result['status'],'environment_error')
            self.assertEqual(result['attempt_count'],3);self.assertEqual(result['attempts'],[])
            for tool in (request,info,execute):tool.assert_not_called()

    def test_harness_only_compiles_without_importing_or_executing_target(self):
        tree=ast.parse(compilation.HARNESS)
        names=[n.func.id for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)]
        self.assertEqual(names.count('compile'),1)
        self.assertFalse({'exec','eval','__import__'} & set(names))
        compilation.check({}, {})


if __name__=='__main__':
    unittest.main()
