"""Software-only fixtures. No model calls, Docker daemon or upstream code execution."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import tempfile
import tarfile
import unittest
from unittest.mock import Mock, patch
from ci_demo import batch, multicase, ollama
from ci_demo.common import write_json


def config(name="example"):
    return {"case_id": name, "runner_kind": "python-source-v2", "split": "development", "source_kind": "aidev",
            "repo_url": "https://github.com/example/" + name, "base": "a" * 40, "head": "b" * 40,
            "allowed_file": "package/api.py", "license": "MIT", "test_targets": ["tests/test_api.py"],
            "frozen_test_files": ["tests/test_api.py"], "resources": {"memory_mb": 512, "cpus": 1}, "dependencies": []}


class CaseTests(unittest.TestCase):
    def test_stdlib_distutils_is_explicit_and_runtime_isolation_stays_enabled(self):
        for value in ["stdlib", "true", 1, None, {"PYTHONPATH": "/host"}]:
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "stdlib_distutils"):
                multicase.validate_case({**config(), "stdlib_distutils": value})
        with tempfile.TemporaryDirectory() as tmp:
            for setting in [None, False, True]:
                case = config()
                if setting is not None:
                    case["stdlib_distutils"] = setting
                multicase.validate_case(case)
                calls = []
                def command(args, folder, name, **kwargs):
                    calls.append(args)
                    return {"exit_code": 0, "timed_out": False}
                with patch.object(multicase, "command", side_effect=command):
                    multicase.execute(case, {"image_id": "sha256:fixture"}, Path(tmp) / str(setting), "test")
                args = calls[0]
                self.assertEqual(args.count("SETUPTOOLS_USE_DISTUTILS=stdlib"), int(setting is True))
                self.assertIn("--network=none", args)
                self.assertIn("--read-only", args)
                self.assertIn("65534:65534", args)
                self.assertIn("PYTEST_DISABLE_PLUGIN_AUTOLOAD=1", args)
                self.assertEqual(calls[-1][:3], ["docker", "rm", "-f"])

    def test_conflicting_bootstrap_pins_fail_before_build(self):
        case = config()
        case['pytest_version'] = '6.2.5'
        multicase.check_bootstrap_pins({**case, 'dependencies': multicase.bootstrap_dependencies(case)})
        for requirement in ['setuptools==57.5.0', 'wheel==0.37.1', 'pytest==7.4.4']:
            with self.subTest(requirement=requirement), self.assertRaisesRegex(ValueError, 'bootstrap pin'):
                multicase.check_bootstrap_pins({**case, 'dependencies': [requirement]})
        multicase.check_bootstrap_pins({**case, 'dependencies': ['setuptools-scm==7.0.5']})
        historical = {**case, 'dependencies': ['setuptools==57.5.0']}
        multicase.validate_case(historical)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root / 'cases/example/case.json', historical)
            from ci_demo import common
            with patch.object(common, 'ROOT', root):
                self.assertEqual(common.case_config('example'), historical)
            with patch.object(multicase, 'checked') as command:
                with self.assertRaisesRegex(ValueError, 'bootstrap pin'):
                    multicase.prepare_case(historical, root / 'evidence')
                command.assert_not_called()
                self.assertFalse((root / 'evidence').exists())

    def test_pinned_git_fixture_is_self_contained_and_detects_tampering(self):
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);repo=root/'repo';repo.mkdir();work=root/('long-path-'+160*'a');work.mkdir();evidence=root/'evidence';evidence.mkdir()
            subprocess.run(['git','init',str(repo)],check=True,capture_output=True)
            (repo/'inert.txt').write_bytes(b'fixture only\n')
            subprocess.run(['git','-C',str(repo),'add','inert.txt'],check=True,capture_output=True)
            subprocess.run(['git','-C',str(repo),'-c','user.name=fixture','-c','user.email=fixture@example.invalid',
                            'commit','-m','inert fixture'],check=True,capture_output=True)
            revision=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
            case={'git_test_fixture':True,'base':revision}
            guard=Mock()
            try:metadata=multicase.prepare_git_fixture(case,repo,work,evidence,guard)
            except RuntimeError:
                self.fail('\n'.join(p.read_text() for p in evidence.glob('*.stderr.txt')))
            self.assertEqual(metadata['commit'],revision)
            self.assertFalse((work/'fixture.git/objects/info/alternates').exists())
            self.assertFalse((work/'fixture.git/hooks').exists())
            gate={'context':str(work),'git_test_fixture':metadata}
            multicase.check_git_fixture(case,gate)
            self.assertEqual(guard.call_count,4)
            (work/'fixture.git/config').write_text('tampered',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'fixture changed'):multicase.check_git_fixture(case,gate)
            with self.assertRaises(ValueError):multicase.check_git_fixture(case,{'context':str(work)})

    def test_git_fixture_recipe_scope_and_docker_readonly_location(self):
        case=config();case.update(repo_url='https://github.com/gitpython-developers/GitPython',system_tools=['git'],git_test_fixture=True,install_project=False)
        multicase.validate_case(case)
        for changes in [{'repo_url':'https://github.com/example/repo'},{'system_tools':[]},{'git_test_fixture':'../host.git'}]:
            with self.subTest(changes=changes),self.assertRaises(ValueError):multicase.validate_case({**case,**changes})
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);evidence=root/'evidence';evidence.mkdir()
            def export(repo,revision,destination,*args):
                for name in ['package/api.py','tests/test_api.py']:
                    p=destination/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('# inert\n')
                return {}
            def checked(args,folder,name,**kwargs):
                if name=='image-inspect':
                    identity=args[-1].split(':')[-1]
                    write_json(folder/'image.json',[{'Id':'sha256:fixture','Config':{'Labels':{'it5417.case':identity}}}])
                return {'stdout':'image.json'}
            metadata={'commit':case['base'],'inventory':{},'runtime_path':'/fixtures/source.git'}
            with patch.object(multicase,'CACHE',root/'cache'),patch.object(multicase,'export_commit',side_effect=export), \
                    patch.object(multicase,'checked',side_effect=checked),patch.object(multicase,'prepare_git_fixture',return_value=metadata):
                gate=multicase.prepare_case(case,evidence)
            dockerfile=(Path(gate['context'])/'Dockerfile').read_text()
            self.assertIn('COPY fixture.git /fixtures/source.git',dockerfile)
            self.assertIn('safe.directory /fixtures/source.git',dockerfile)
            self.assertNotIn('safe.directory *',dockerfile)
            self.assertIn('GIT_PYTHON_TEST_GIT_REPO_BASE=/fixtures/source.git',dockerfile)
            self.assertIn('USER 65534:65534',dockerfile)
            self.assertEqual(gate['git_test_fixture'],metadata)

    def test_swe_option_mapping_checks_every_member_of_an_official_canonical_group(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);file=folder/'report.xml'
            result={'junit':file.name,'timed_out':False}
            file.write_text('<testsuite><testcase classname="tests.test_utils.TestPaths" name="test_path[/source/base/tests/example.py]"/></testsuite>')
            target='tests/test_utils.py::TestPaths::test_path[/example.py]'
            self.assertFalse(multicase.resolve_targets(result,folder,[target],'pass')[0])
            ok,rows=multicase.resolve_targets(result,folder,[target],'pass','swebench_pytest_options')
            self.assertTrue(ok);self.assertEqual(rows[0]['resolved_name'],'test_path[/source/base/tests/example.py]')
            file.write_text('<testsuite><testcase classname="tests.test_utils.TestPaths" name="test_path[/source/a/example.py]"/><testcase classname="tests.test_utils.TestPaths" name="test_path[/source/b/example.py]"/></testsuite>')
            ok,rows=multicase.resolve_targets(result,folder,[target],'pass','swebench_pytest_options')
            self.assertTrue(ok);self.assertEqual(len(rows[0]['resolved_names']),2)
            file.write_text('<testsuite><testcase classname="tests.test_utils.TestPaths" name="test_path[/source/a/example.py]"/><testcase classname="tests.test_utils.TestPaths" name="test_path[/source/b/example.py]"><failure>fixture</failure></testcase></testsuite>')
            self.assertFalse(multicase.resolve_targets(result,folder,[target],'pass','swebench_pytest_options')[0])
            file.write_text('<testsuite><testcase classname="tests.test_utils.TestPaths" name="test_path[a space one]"/><testcase classname="tests.test_utils.TestPaths" name="test_path[a space two]"/></testsuite>')
            truncated='tests/test_utils.py::TestPaths::test_path[a'
            self.assertTrue(multicase.resolve_targets(result,folder,[truncated],'pass','swebench_pytest_options')[0])
            for value in ['//server/example.py','/source/*.py','relative/example.py','https://host/example.py']:
                file.write_text('<testsuite><testcase classname="tests.test_utils.TestPaths" name="test_path['+value+']"/></testsuite>')
                self.assertFalse(multicase.resolve_targets(result,folder,[target],'pass','swebench_pytest_options')[0])

    def test_swe_whitespace_group_is_strict_and_does_not_fold_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);file=folder/'report.xml';result={'junit':file.name,'timed_out':False}
            target='tests/test_api.py::TestAPI::test_url[http://'
            file.write_text('<testsuite><testcase classname="tests.test_api.TestAPI" name="test_url[http:// bad one]"/><testcase classname="tests.test_api.TestAPI" name="test_url[http:// bad two]"/></testsuite>')
            self.assertFalse(multicase.resolve_targets(result,folder,[target],'pass')[0])
            ok,rows=multicase.resolve_targets(result,folder,[target],'pass','swebench_pytest_whitespace')
            self.assertTrue(ok);self.assertEqual(len(rows[0]['resolved_names']),2)
            file.write_text('<testsuite><testcase classname="tests.test_api.TestAPI" name="test_url[http:// bad one]"/><testcase classname="tests.test_api.TestAPI" name="test_url[http:// bad two]"><failure>fixture</failure></testcase></testsuite>')
            self.assertFalse(multicase.resolve_targets(result,folder,[target],'pass','swebench_pytest_whitespace')[0])
            file.write_text('<testsuite><testcase classname="tests.test_api.TestAPI" name="test_path[/source/base/example.py]"/></testsuite>')
            shortened='tests/test_api.py::TestAPI::test_path[/example.py]'
            self.assertFalse(multicase.resolve_targets(result,folder,[shortened],'pass','swebench_pytest_whitespace')[0])
            self.assertTrue(multicase.resolve_targets(result,folder,[shortened],'pass','swebench_pytest_options')[0])

    def test_swe_whitespace_recipe_requires_original_references_and_known_parser(self):
        case={**config(),'source_kind':'swebench','source_id_matching':'swebench_pytest_whitespace',
              'repo_url':'https://github.com/marshmallow-code/marshmallow'}
        multicase.validate_case(case)
        for change in [{'source_kind':'aidev'}, {'repo_url':'https://github.com/example/project'},
                       {'test_reference_policy':'upstream_pr_recovered_v1'}]:
            with self.subTest(change=change),self.assertRaises(ValueError):
                multicase.validate_case({**case,**change})

    def test_pinned_license_markdown_and_apache_still_reject_missing_or_wrong_family(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            with self.assertRaisesRegex(ValueError, "missing"):
                multicase.pinned_license(base, "Apache-2.0")
            license_file = base / "LICENSE.md"
            license_file.write_text("Apache License\nVersion 2.0", encoding="utf-8")
            result = multicase.pinned_license(base, "Apache-2.0")
            self.assertEqual(result["path"], "LICENSE.md")
            self.assertEqual(result["sha256"], multicase.sha256(license_file))
            for declared in ("MIT", "unknown"):
                with self.assertRaisesRegex(ValueError, "does not match"):
                    multicase.pinned_license(base, declared)
            license_file.write_text("Redistribution and use in source and binary forms", encoding="utf-8")
            self.assertEqual(multicase.pinned_license(base, "BSD-3-Clause")["declared_license"], "BSD-3-Clause")
            license_file.write_text("This is free and unencumbered software released into the public domain.", encoding="utf-8")
            self.assertEqual(multicase.pinned_license(base, "Unlicense")["declared_license"], "Unlicense")

    def test_recovered_local_regression_uses_explicit_nodes_and_retains_dataset_reference_format(self):
        for recovered in [False,True]:
            with self.subTest(recovered=recovered),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);folder=root/'run';folder.mkdir()
                for role,failure in [('base','<failure type="AssertionError">fixture</failure>'),('head','')]:
                    (folder/(role+'.xml')).write_text('<testsuite><testcase classname="tests.test_api.TestAPI" name="test_regression">'+failure+'</testcase><testcase classname="tests.test_api.TestAPI" name="test_control"/></testsuite>')
                fail=['tests/test_api.py::TestAPI::test_regression'];passed=['tests/test_api.py::TestAPI::test_control']
                case={**config(),'source_kind':'swebench','fail_to_pass':fail,'pass_to_pass':passed}
                if recovered:
                    case.update(test_reference_policy='upstream_pr_recovered_v1',fail_to_pass=[],pass_to_pass=[],
                                local_expected_failures=fail,local_expected_passes=passed)
                outcomes=[{'exit_code':1,'timed_out':False,'container_removed':True,'junit':'base.xml'},
                          {'exit_code':0,'timed_out':False,'container_removed':True,'junit':'head.xml'}]
                with patch.object(multicase,'CACHE',root/'cache'), \
                     patch.object(multicase,'prepare_case',return_value={'case_hash':'fixture'}), \
                     patch.object(multicase,'execute',side_effect=outcomes), \
                     patch('ci_demo.upstream_tests.provenance',return_value={}):
                    result=multicase.reproduce_case(case,folder)
                self.assertTrue(result['historical_supported'])
                key='local_test_resolution' if recovered else 'source_test_resolution'
                self.assertEqual(len(result[key]),4)
                if recovered:self.assertNotIn('source_test_resolution',result)
                # An unrelated failure cannot substitute for the selected regression.
                (folder/'base.xml').write_text('<testsuite><testcase classname="tests.test_api.TestAPI" name="test_regression"/><testcase classname="tests.test_api.TestAPI" name="test_control"><failure type="AssertionError">unrelated</failure></testcase></testsuite>')
                with patch.object(multicase,'CACHE',root/'cache'), \
                     patch.object(multicase,'prepare_case',return_value={'case_hash':'fixture'}), \
                     patch.object(multicase,'execute',side_effect=outcomes), \
                     patch('ci_demo.upstream_tests.provenance',return_value={}):
                    result=multicase.reproduce_case(case,folder)
                self.assertFalse(result['historical_supported'])

    def test_parameter_node_separators_are_literal_parameter_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "results.xml").write_text('<testsuite><testcase classname="tests.test_api.TestCase" name="test_it[a/b::C[inner]-expected]"/></testsuite>')
            result = {"exit_code": 0, "timed_out": False, "junit": "results.xml"}
            target = "tests/test_api.py::TestCase::test_it[a/b::C[inner]-expected]"
            self.assertTrue(multicase.targets_match(result, root, [target], "pass"))
            ok, rows = multicase.resolve_targets(result, root, [target], "pass")
            self.assertTrue(ok)
            self.assertEqual(rows[0]["resolution"], "exact")
            self.assertFalse(multicase.resolve_targets(result, root, [target.replace("::C[", "::D[")], "pass")[0])

    def test_scm_metadata_builds_both_revisions_without_changing_regular_install(self):
        case = config()
        normal = multicase.project_install_steps(case)
        self.assertIn('"/source/head"', normal)
        self.assertNotIn('"/source/base"', normal)
        self.assertNotIn("--no-deps", normal)
        self.assertEqual(multicase.project_install_steps({**case, "install_project": False}), "")
        case.update(scm_build_version="6.2.1.dev4+ga7e38c5", install_project=True)
        multicase.validate_case(case)
        steps = multicase.project_install_steps(case)
        self.assertIn("SETUPTOOLS_SCM_PRETEND_VERSION=6.2.1.dev4+ga7e38c5", steps)
        self.assertEqual(steps.count("--no-deps"), 2)
        self.assertIn('"/source/base"', steps)
        self.assertIn('"/source/head"', steps)
        for invalid in ("6.2\nRUN unsafe", "$(command)", None):
            bad = {**case, "scm_build_version": invalid}
            if invalid is None:
                bad["scm_build_version"] = "6.2"
                bad["install_project"] = False
            with self.assertRaises(ValueError):
                multicase.validate_case(bad)

    def test_pinned_cached_commit_exports_offline_and_still_checks_identity(self):
        import io
        import tarfile
        revision = "a" * 40
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w") as bundle:
            data = b"fixture source text\n"
            member = tarfile.TarInfo("package/api.py")
            member.size = len(data)
            bundle.addfile(member, io.BytesIO(data))
        for cached in (True, False):
            with self.subTest(cached=cached), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                with patch.object(multicase, "command", return_value={"exit_code": 0 if cached else 1, "timed_out": False}), \
                     patch.object(multicase, "checked") as fetch, \
                     patch.object(multicase.subprocess, "check_output", side_effect=[revision + "\n", buffer.getvalue()]):
                    multicase.export_commit(root / "repo", revision, root / "export", root, "base", None)
                    self.assertEqual((root / "export/package/api.py").read_bytes(), data)
                    self.assertEqual(fetch.call_count, 0 if cached else 1)
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(multicase, "command", return_value={"exit_code": 0, "timed_out": False}), \
             patch.object(multicase.subprocess, "check_output", return_value="b" * 40):
            with self.assertRaises(ValueError):
                multicase.export_commit(Path(tmp), revision, Path(tmp) / "export", Path(tmp), "base", None)

    def test_top_level_pytest_harness_is_frozen_without_reclassifying_library_testing_modules(self):
        self.assertTrue(multicase.is_test("testing/example_scripts/fixture.py"))
        self.assertFalse(multicase.is_test("sympy/testing/runtests.py"))
        self.assertFalse(multicase.is_test("src/_pytest/python.py"))
        case = config()
        case["pytest_version"] = "6.2.5"
        multicase.validate_case(case)
        case["allowed_file"] = "testing/fixture.py"
        with self.assertRaises(ValueError):
            multicase.validate_case(case)

    def test_writable_cwd_keeps_source_readonly_and_test_ids_rooted(self):
        with tempfile.TemporaryDirectory() as tmp:
            calls = []
            def command(args, folder, name, **kwargs):
                calls.append(args)
                return {"exit_code": 0, "timed_out": False}
            case = config()
            case.update(test_workdir="work", system_tools=["git"])
            multicase.validate_case(case)
            with patch.object(multicase, "command", side_effect=command):
                multicase.execute(case, {"image_id": "sha256:fixture"}, Path(tmp) / "out", "test")
            args = calls[0]
            self.assertEqual(args[args.index("--workdir") + 1], "/work")
            self.assertIn("/work:rw,noexec,nosuid,size=64m,mode=1777", args)
            self.assertIn("--rootdir=/source/head", args)
            self.assertIn("/source/head/tests/test_api.py", args)
            self.assertIn("--read-only", args)
            self.assertIn("--network=none", args)
            for field, value in (("test_workdir", "/source/head"), ("system_tools", ["curl"])):
                with self.assertRaises(ValueError):
                    multicase.validate_case({**case, field: value})

    def test_heldout_case_generation_is_saved_and_refused_before_docker_or_model(self):
        case = config()
        case["experiment_role"] = "test"
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            with patch.object(multicase, "execute") as execute, patch.object(ollama, "model_info") as info, patch.object(ollama, "request") as request:
                result = multicase.generate_case(case, "http://127.0.0.1:11434", folder=folder)
            self.assertEqual(result["status"], "environment_error")
            self.assertIn("Held-out", result["error"])
            self.assertEqual(result["attempt_count"], 3)
            self.assertEqual(result["attempts"], [])
            execute.assert_not_called()
            info.assert_not_called()
            request.assert_not_called()

    def test_archive_symlinks_preserve_internal_targets_and_refuse_escape_cycles_and_special_files(self):
        source = tarfile.TarInfo("pkg/target.py")
        link = tarfile.TarInfo("tests/alias.py")
        link.type = tarfile.SYMTYPE
        link.linkname = "../pkg/target.py"
        self.assertEqual(multicase.archive_links(Mock(getmembers=lambda: [source, link])), {"tests/alias.py": "../pkg/target.py"})
        for target in ("../../outside.py", "/etc/passwd", "alias.py", "C:/secrets", "../missing.py"):
            link.linkname = target
            with self.assertRaises(ValueError):
                multicase.archive_links(Mock(getmembers=lambda: [source, link]))
        link.linkname = "../pkg/target.py"
        child = tarfile.TarInfo("tests/alias.py/child.py")
        with self.assertRaises(ValueError):
            multicase.archive_links(Mock(getmembers=lambda: [source, link, child]))
        link.type = tarfile.LNKTYPE
        with self.assertRaises(ValueError):
            multicase.archive_links(Mock(getmembers=lambda: [source, link]))

    def test_sympy_source_names_resolve_exactly_and_ambiguity_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tests").mkdir()
            (root / "tests/test_api.py").write_text("def test_a():\n    pass\ndef test_ab():\n    pass\n")
            case = {"frozen_test_files": ["tests/test_api.py"], "fail_to_pass": ["test_a"], "pass_to_pass": ["test_ab"]}
            self.assertEqual(multicase.source_function_targets(case, root), ["tests/test_api.py::test_a", "tests/test_api.py::test_ab"])
            case.update(source_id_matching="exact_unique_function_name", test_targets=["tests/test_api.py"])
            self.assertIn("def test_a", multicase.test_excerpt(case, root))
            (root / "results.xml").write_text('<testsuite><testcase classname="tests.test_api" name="test_a"/></testsuite>')
            result = {"timed_out": False, "junit": "results.xml"}
            self.assertTrue(multicase.resolve_targets(result, root, ["test_a"], "pass", "exact_unique_function_name")[0])
            self.assertFalse(multicase.resolve_targets(result, root, ["test"], "pass", "exact_unique_function_name")[0])
            (root / "tests/test_other.py").write_text("def test_a():\n    pass\n")
            case["frozen_test_files"].append("tests/test_other.py")
            with self.assertRaises(ValueError):
                multicase.source_function_targets(case, root)

    def test_windows_export_names_and_repo_identity_cannot_escape_cache(self):
        for value in ["../escape", "dir/.. /escape.py", "dir./module.py", "dir/NUL.py"]:
            with self.assertRaises(ValueError): multicase.safe_relative(value)
        for url in ["https://github.com/../..", "https://github.com/owner./repo", "https://github.com/owner/CON"]:
            with self.assertRaises(ValueError): multicase.validate_case({**config(), "repo_url":url})

    def test_upstream_plural_test_suffix_and_explicit_plugin_recipe_are_bounded(self):
        self.assertTrue(multicase.is_test("package/resources/resource_tests.py"))
        c = config(); c["pytest_version"] = "8.3.5"; c["pytest_plugins"] = ["inline_snapshot.pytest_plugin"]
        multicase.validate_case(c)
        for field, value in [("pytest_version", "unbounded"), ("pytest_plugins", ["--override-ini=unsafe"])]:
            with self.assertRaises(ValueError): multicase.validate_case({**c, field: value})

    def test_site_edits_preserve_indentation_crlf_and_refuse_undeclared_sites(self):
        original = "def f(x):\r\n    if x > 3:\r\n        return x + 1\r\n    return 0\r\n"
        sites = multicase.mutation_sites(original, 2)
        site = next(s for s in sites if s["line"] == 2)
        proposal = {"path": "package/api.py", "site_id": site["site_id"], "replacement": "if x >= 3:", "explanation": "fixture"}
        changed = multicase.apply_site_edit(proposal, original, proposal["path"], [site])
        self.assertEqual(changed, original.replace("if x > 3:", "if x >= 3:"))
        self.assertEqual(changed.count("\r\n"), 4)
        for replacement in [" if x >= 3:", "if x >= 3:\nreturn 9", "if x > 3:"]:
            with self.assertRaises(ValueError): multicase.apply_site_edit({**proposal, "replacement": replacement}, original, proposal["path"], [site])
        with self.assertRaises(ValueError): multicase.apply_site_edit(proposal, original, proposal["path"], [])
        self.assertNotIn("proposed_label", multicase.SITE_SCHEMA["properties"])

    def test_truncated_parameter_mapping_requires_unique_explicit_parameter_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); p = root / "results.xml"
            p.write_text('<testsuite><testcase classname="tests.test_api.TestAPI" name="test_error[required-Missing data]"/></testsuite>')
            result = {"exit_code": 0, "timed_out": False, "junit": p.name}
            target = "tests/test_api.py::TestAPI::test_error[required-Missing"
            self.assertFalse(multicase.resolve_targets(result, root, [target], "pass")[0])
            ok, rows = multicase.resolve_targets(result, root, [target], "pass", "exact_or_unique_truncated_param")
            self.assertTrue(ok); self.assertEqual(rows[0]["resolution"], "unique_truncated_parameter_prefix")
            p.write_text('<testsuite><testcase classname="tests.test_api.TestAPI" name="test_error[required-Missing data]"/><testcase classname="tests.test_api.TestAPI" name="test_error[required-Missing other]"/></testsuite>')
            self.assertFalse(multicase.resolve_targets(result, root, [target], "pass", "exact_or_unique_truncated_param")[0])
            self.assertFalse(multicase.resolve_targets(result, root, ["tests/test_api.py::TestAPI::test_error"], "pass", "exact_or_unique_truncated_param")[0])

    def test_site_diversity_uses_only_passing_source_tests_and_stable_case_identity(self):
        original = "def unrelated(x):\n    return x + 1\n\n" + "\n" * 120 + "def target(x):\n"
        original += "".join(f"    x = x + {i}\n" for i in range(40)) + "    return x\n"
        sites = multicase.mutation_sites(original, 1, identity="case-a", test_context="assert target(2) == 3")
        self.assertEqual(len(sites), 18)
        self.assertTrue(all(s['line'] > 123 for s in sites))
        self.assertEqual(sites, multicase.mutation_sites(original, 999, identity="case-a", test_context="assert target(2) == 3"))
        other = multicase.mutation_sites(original, 1, identity="case-b", test_context="assert target(2) == 3")
        self.assertNotEqual({s['line'] for s in sites}, {s['line'] for s in other})
        context = multicase.site_context(original, sites[::3])
        self.assertIn("LINE ", context)
        self.assertIn("x = x +", context)
        self.assertLessEqual(len(context), 3600)
        fallback = multicase.mutation_sites(original, 1, identity="case-a", test_context="no matched source function")
        self.assertEqual(len(fallback), 18)

    def test_declared_log_tmpfs_must_not_mask_source_or_tests(self):
        case = config(); case["writable_dirs"] = ["test_logs"]
        multicase.validate_case(case)
        case["allowed_file"] = "test_logs/api.py"
        with self.assertRaises(ValueError): multicase.validate_case(case)

    def test_case_loader_prefers_canonical_directory_and_keeps_legacy_fallback(self):
        from ci_demo import common
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); c = config("registered")
            legacy = root / "data-manifests/cases/registered.json"
            write_json(legacy, c)
            with patch.object(common, "ROOT", root):
                self.assertEqual(common.case_config("registered"), c)
                canonical = root / "cases/registered/case.json"
                newer = {**c, "focus_line": 42}; write_json(canonical, newer)
                self.assertEqual(common.case_config("registered"), newer)
                with self.assertRaises(ValueError): common.case_config("../escape")

    def test_patch_applies_to_export_not_outer_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); tree = root / "export"; tree.mkdir(); evidence = root / "evidence"; evidence.mkdir()
            (tree / "fixture.txt").write_bytes(b"before\n")
            patch_file = root / "fix.patch"
            patch_file.write_bytes(b"--- a/fixture.txt\n+++ b/fixture.txt\n@@ -1 +1 @@\n-before\n+after\n")
            with patch.dict('os.environ',{'GIT_CONFIG_COUNT':'1','GIT_CONFIG_KEY_0':'core.autocrlf','GIT_CONFIG_VALUE_0':'true'}):
                multicase.apply_patch_file(tree, patch_file, evidence, "fixture-patch", None)
            self.assertEqual((tree / "fixture.txt").read_bytes(), b"after\n")

    def test_archive_and_patch_preserve_blob_bytes_under_host_crlf_configuration(self):
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);repo=root/'repo';repo.mkdir();evidence=root/'evidence';evidence.mkdir()
            subprocess.run(['git','init',str(repo)],check=True,capture_output=True)
            subprocess.run(['git','-C',str(repo),'config','core.autocrlf','false'],check=True,capture_output=True)
            (repo/'fixture.txt').write_bytes(b'before\n')
            subprocess.run(['git','-C',str(repo),'add','fixture.txt'],check=True,capture_output=True)
            subprocess.run(['git','-C',str(repo),'-c','user.name=fixture','-c','user.email=fixture@example.invalid',
                            'commit','-m','inert software fixture'],check=True,capture_output=True)
            revision=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
            subprocess.run(['git','-C',str(repo),'config','core.autocrlf','true'],check=True,capture_output=True)
            tree=root/'export'
            multicase.export_commit(repo,revision,tree,evidence,'fixture-base',None)
            self.assertEqual((tree/'fixture.txt').read_bytes(),b'before\n')
            patch_file=root/'fix.patch';patch_file.write_bytes(b'--- a/fixture.txt\n+++ b/fixture.txt\n@@ -1 +1 @@\n-before\n+after\n')
            with patch.dict('os.environ',{'GIT_CONFIG_COUNT':'1','GIT_CONFIG_KEY_0':'core.autocrlf','GIT_CONFIG_VALUE_0':'true'}):
                multicase.apply_patch_file(tree,patch_file,evidence,'fixture-fix',None)
            self.assertEqual((tree/'fixture.txt').read_bytes(),b'after\n')

    def test_validation_rejects_unsafe_or_unapproved_cases(self):
        multicase.validate_case(config())
        for field, value in [("allowed_file", "../other.py"), ("allowed_file", "tests/test_api.py"),
                             ("repo_url", "https://example.com/a/b"), ("license", "NOASSERTION"),
                             ("split", "test"), ("dependencies", ["--extra-index-url=secret"])]:
            with self.subTest(field=field, value=value):
                case = config(); case[field] = value
                with self.assertRaises(ValueError): multicase.validate_case(case)

    def test_exact_edit_is_single_unique_allowlisted_change(self):
        proposal = {"path": "package/api.py", "before": "return x + 1", "after": "return x - 1",
                    "proposed_label": "logic", "explanation": "software fixture"}
        self.assertEqual(multicase.apply_edit(proposal, "def f(x):\n    return x + 1\n", proposal["path"]),
                         "def f(x):\n    return x - 1\n")
        for source, allowed in [("return x + 1\nreturn x + 1", proposal["path"]), ("different", proposal["path"]),
                                ("return x + 1", "other.py")]:
            with self.assertRaises(ValueError): multicase.apply_edit(proposal, source, allowed)

    def test_patch_paths_refuse_traversal_and_metadata(self):
        self.assertEqual(multicase.patch_paths("--- a/pkg/a.py\n+++ b/pkg/a.py\n"), ["pkg/a.py"])
        for path in ("../../escape", ".git/config", "/absolute"):
            with self.assertRaises(ValueError): multicase.patch_paths("--- a/" + path + "\n+++ b/" + path + "\n")

    def test_gate_rejects_other_case_and_modified_tests(self):
        import hashlib
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); head = root / "head"; head.mkdir(); (head / "test.py").write_text("fixture")
            c = config(); gate = {"head_passed": True, "case_id": c["case_id"], "context": str(root),
                 "case_hash": hashlib.sha256(json.dumps(c, sort_keys=True).encode()).hexdigest()[:16],
                 "inventories": {"head": multicase.inventory(head)}}
            self.assertEqual(multicase.check_gate(c, gate), head)
            with self.assertRaises(ValueError): multicase.check_gate(config("other"), gate)
            (head / "test.py").write_text("changed fixture")
            with self.assertRaises(ValueError): multicase.check_gate(c, gate)

    def test_undeclared_conftest_or_fixture_change_is_not_a_product_regression(self):
        inventories = {"base": {"package/api.py": "a", "package/conftest.py": "same", "tests/data.json": "same"},
                       "head": {"package/api.py": "b", "package/conftest.py": "same", "tests/data.json": "same"}}
        multicase.ensure_frozen_tests(inventories)
        inventories["head"]["package/conftest.py"] = "changed"
        with self.assertRaises(ValueError): multicase.ensure_frozen_tests(inventories)

    def test_junit_target_mapping_and_skip_not_a_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); p = root / "results.xml"
            p.write_text('<testsuite><testcase classname="tests.test_api.TestAPI" name="test_f"><failure message="fixture"/></testcase></testsuite>')
            result = {"exit_code": 1, "timed_out": False, "junit": p.name, "container_removed": True}
            self.assertTrue(multicase.targets_match(result, root, ["tests/test_api.py::TestAPI::test_f"], "fail"))
            self.assertFalse(multicase.targets_match(result, root, ["tests/test_api.py::TestAPI::missing"], "fail"))
            p.write_text('<testsuite><testcase classname="tests.test_api" name="test_f"><skipped/></testcase></testsuite>')
            result["exit_code"] = 0
            self.assertFalse(multicase.test_passed(result, root))

    def test_runner_mounts_only_candidate_and_fresh_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); candidate = root / "candidate.py"; candidate.write_text("# inert fixture; never executed")
            calls = []
            def command(args, folder, name, **kw):
                calls.append(args)
                return {"exit_code": 0, "timed_out": False}
            with patch.object(multicase, "command", side_effect=command):
                multicase.execute(config(), {"image_id": "sha256:fixture"}, root / "out", "test", candidate=candidate)
            args = calls[0]
            for flag in ("--network=none", "--read-only", "--cap-drop=ALL", "--pids-limit=128"):
                self.assertIn(flag, args)
            self.assertIn("--user", args)
            self.assertTrue(any(",dst=/source/head/package/api.py,readonly" in str(x) for x in args))
            self.assertFalse(any("docker.sock" in str(x) for x in args))
            self.assertEqual(calls[-1][:3], ["docker", "rm", "-f"])

    def test_dynamic_schema_does_not_mutate_legacy_schema(self):
        before = copy.deepcopy(ollama.SCHEMA)
        self.assertEqual(ollama.schema_for_path("p/file.py")["properties"]["path"]["enum"], ["p/file.py"])
        self.assertEqual(ollama.SCHEMA, before)

    def test_batch_report_escapes_errors_and_has_manifest_fallback(self):
        from ci_demo.report import render
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); folder = root / "batch-fixture"; folder.mkdir()
            html = render(folder, {"kind": "development_batch", "run_id": "batch-fixture", "status": "batch_incomplete",
                "cases": [{"case_id": "<script>alert(1)</script>", "source_kind": "aidev", "status": "failed",
                           "error": '<img src=x onerror="bad()">', "stages": {"reproduce": {"run_id": "source-fixture"}}}]})
            self.assertNotIn('<script>', html)
            self.assertIn('&lt;script&gt;', html)
            self.assertIn('../source-fixture/manifest.json', html)
            generated = render(folder, {"kind":"synthetic_generation", "schema_version":2, "run_id":"fixture", "status":"generation_finished",
                                        "protocol":multicase.SITE_PROTOCOL, "attempts":[], "attempt_count":3})
            self.assertIn(multicase.SITE_PROTOCOL, generated)

    def test_three_model_timeouts_keep_denominator_and_exclude_reference_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); head = root / "head"; (head / "package").mkdir(parents=True)
            (head / "package/api.py").write_bytes(b"def f(x):\n    return x + 1\n")
            reproduced = root / "reproduced"; reproduced.mkdir()
            write_json(reproduced / "manifest.json", {"environment": {"test_hashes": {"tests/test_api.py": "fixture"}}})
            c = config(); c["reference_label"] = "SWE_GOLD_SENTINEL"
            calls = []
            def request(endpoint, path, payload=None, **kw):
                if path == "/api/version": return '{"version":"software-fixture"}'
                calls.append((payload, kw)); raise TimeoutError("software fixture timeout")
            with patch.object(multicase, "run_path", return_value=reproduced), patch.object(multicase, "check_gate", return_value=head), \
                 patch.object(multicase, "execute", return_value={"exit_code": 0, "timed_out": False}), \
                 patch.object(multicase, "test_passed", return_value=True), patch.object(ollama, "model_info", return_value={}), \
                 patch.object(ollama, "request", side_effect=request):
                folder = root / "generation"; folder.mkdir()
                result = multicase.generate_case(c, "http://127.0.0.1:11434", folder, "fixture")
            self.assertEqual(result["attempt_count"], 3)
            self.assertEqual([a["status"] for a in result["attempts"]], ["generation_error"] * 3, result.get("error"))
            self.assertEqual(len(calls), 3)
            self.assertEqual([p["options"]["seed"] for p, kw in calls], [5417, 5418, 5419])
            self.assertTrue(all(kw["timeout"] == 180 and p["model"] == ollama.GENERATOR_MODEL for p, kw in calls))
            self.assertNotIn("SWE_GOLD_SENTINEL", (folder / "prompt.txt").read_text())

    def test_site_prompt_revision_preserves_model_budget_and_reference_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); head=root/'head'; (head/'package').mkdir(parents=True)
            (head/'package/api.py').write_bytes(b'def f(x):\n    return x\n')
            reproduced=root/'reproduced'; reproduced.mkdir()
            write_json(reproduced/'manifest.json', {'environment':{'test_hashes':{}}})
            c=config(); c.update(generation_protocol=multicase.SITE_PROTOCOL, reference_label='GOLD_SENTINEL')
            payloads=[]
            def request(endpoint,path,payload=None,**kwargs):
                if path=='/api/version':return '{}'
                payloads.append(payload); raise TimeoutError('software fixture')
            with patch.object(multicase,'run_path',return_value=reproduced), patch.object(multicase,'check_gate',return_value=head), \
                 patch.object(multicase,'execute',return_value={}), patch.object(multicase,'test_passed',return_value=True), \
                 patch.object(multicase,'test_excerpt',return_value='immutable test fixture'), \
                 patch.object(ollama,'model_info',return_value={}), patch.object(ollama,'request',side_effect=request):
                folder=root/'generation'; folder.mkdir()
                result=multicase.generate_case(c,'http://127.0.0.1:11434',folder,'fixture')
            self.assertEqual(result['prompt_revision'],multicase.SITE_PROMPT_REVISION)
            self.assertEqual(result['protocol'],multicase.SITE_PROTOCOL)
            self.assertEqual(len(payloads),3)
            self.assertEqual([p['options']['seed'] for p in payloads],[5417,5418,5419])
            for index,payload in enumerate(payloads,1):
                self.assertEqual(payload['model'],ollama.GENERATOR_MODEL)
                prompt=payload['messages'][0]['content']
                self.assertIn('Do not append arbitrary numeric offsets',prompt)
                self.assertIn("Do not force conditions with 'or True' or 'and False'",prompt)
                self.assertNotIn('GOLD_SENTINEL',prompt)
                self.assertEqual((folder/f'attempt-{index:02}'/'prompt.txt').read_text(),prompt)

    def test_tampered_candidate_is_refused_without_execution_or_raw_rewrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); generation = root / "generation"; d = generation / "attempt-01"; d.mkdir(parents=True)
            original = b"# inert fixture\n"; (generation / "original.py").write_bytes(original)
            (d / "candidate.py").write_bytes(b"# tampered inert fixture\n")
            import hashlib
            raw = {"kind": "synthetic_generation", "status": "generation_finished", "model": ollama.GENERATOR_MODEL, "source": config(), "passing_seed": {"source_hash": hashlib.sha256(original).hexdigest()},
                   "attempts": [{"index": 1, "directory": d.name, "status": "awaiting_verification", "candidate_sha256": "wrong"}]}
            write_json(generation / "manifest.json", raw); saved = (generation / "manifest.json").read_bytes()
            verify = root / "verify"; verify.mkdir()
            with patch.object(multicase, "run_path", return_value=generation), patch.object(multicase, "check_gate", return_value=root), \
                 patch.object(multicase, "execute") as execute:
                result = multicase.verify_case("generation", verify)
            execute.assert_not_called()
            self.assertEqual(result["status"], "environment_error")
            self.assertEqual((generation / "manifest.json").read_bytes(), saved)

    def test_candidate_timeout_stops_repetition_but_restores_and_preserves_attempt_denominator(self):
        from ci_demo.common import sha256
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); generation=root/'generation'; attempt=generation/'attempt-01'; attempt.mkdir(parents=True)
            (generation/'original.py').write_bytes(b'def inert():\n    return 1\n')
            (attempt/'candidate.py').write_bytes(b'def inert():\n    return 2\n')
            raw={'kind':'synthetic_generation','status':'generation_finished','model':ollama.GENERATOR_MODEL,
                 'source':config(),'passing_seed':{'source_hash':sha256(generation/'original.py')},
                 'attempts':[{'index':1,'directory':'attempt-01','status':'awaiting_verification',
                              'candidate_sha256':sha256(attempt/'candidate.py')},
                             {'index':2,'directory':'attempt-02','status':'invalid_output'},
                             {'index':3,'directory':'attempt-03','status':'invalid_output'}]}
            write_json(generation/'manifest.json',raw)
            passed={'exit_code':0,'timed_out':False,'container_removed':True}
            timeout={'exit_code':None,'timed_out':True,'container_removed':True}
            with patch.object(multicase,'run_path',return_value=generation), patch.object(multicase,'check_gate',return_value=root), \
                 patch.object(multicase,'execute',side_effect=[passed,timeout,passed]) as execute, \
                 patch.object(multicase,'test_passed',return_value=True):
                result=multicase.verify_case('generation',root/'verified')
            self.assertEqual([c.args[3] for c in execute.call_args_list],['baseline','candidate-1','restored'])
            self.assertEqual(len(result['attempts']),3)
            self.assertEqual(len(result['attempts'][0]['repetitions']),1)
            self.assertEqual(result['attempts'][0]['rejection_reason'],'timeout')
            self.assertEqual(result['attempts'][0]['restored'],passed)
            self.assertEqual(result['status'],'verification_finished')

    def test_missing_passing_gate_is_saved_before_preflight_without_model_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); folder = root / "generation"; folder.mkdir()
            with patch.object(multicase, "CACHE", root / "missing-cache"), patch.object(ollama, "request") as request:
                result = multicase.generate_case(config(), "http://127.0.0.1:11434", folder)
            request.assert_not_called()
            self.assertEqual(result["status"], "environment_error")
            self.assertEqual(result["attempt_count"], 3)
            self.assertEqual(result["attempts"], [])
            self.assertTrue((folder / "manifest.json").is_file())


class BatchTests(unittest.TestCase):
    def test_budget_carry_cannot_extend_the_six_hour_limit(self):
        self.assertEqual(batch.initial_budget_charge({"initial_budget_charge_seconds":414.546}),414.546)
        for value in [-1,21601,float('nan'),float('inf'),True]:
            with self.assertRaises(ValueError): batch.initial_budget_charge({"initial_budget_charge_seconds":value})

    def test_lock_refuses_concurrent_resume_and_releases(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "batch.lock"
            with batch.batch_lock(path):
                with self.assertRaises(RuntimeError):
                    with batch.batch_lock(path): self.fail("Concurrent lock acquired")
            with batch.batch_lock(path): pass

    def test_selection_preserves_source_quota_and_repo_cap(self):
        records = [{"case_id": s + str(i), "source_kind": s, "eligible": True, "environment_cost": 0,
                    "changed_file_count": 1, "repo_url": "shared" if i < 7 else s + str(i)}
                   for s in ("aidev", "swebench") for i in range(10)]
        selected = batch.select_cases(records)
        lookup = {r["case_id"]: r for r in records}
        self.assertLessEqual(sum(lookup[x]["repo_url"] == "shared" for x in selected), 4)
        self.assertEqual(len(selected), 10)
        for r in records:
            if r["source_kind"] == "aidev": r["eligible"] = False
        self.assertTrue(all(x.startswith("swebench") for x in batch.select_cases(records)))
        self.assertEqual(len(batch.select_cases(records)), 5)

    def test_resume_never_reissues_unknown_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); b = root / "batch-fixture"; g = root / "generate-fixture"; b.mkdir(); g.mkdir()
            write_json(g / "manifest.json", {"run_id": g.name, "kind": "synthetic_generation", "status": "running",
                                           "attempts": [{"index": 1, "status": "generation_in_progress"}]})
            write_json(b / "manifest.json", {"run_id": b.name, "kind": "development_batch", "status": "batch_incomplete",
                       "active_seconds": 0, "unaccounted_time_bound_seconds": 0, "budget_seconds": 21600,
                       "minimum_free_bytes": 0, "screening": [], "cases": [{"case_id": "fixture", "source_kind": "aidev",
                       "repo_url": "fixture", "status": "pending", "stages": {"generate": {"run_id": g.name, "status": "running"}}}]})
            with patch.object(batch, "run_path", side_effect=lambda x: root / x), patch.object(batch, "case_config") as cfg, \
                 patch("ci_demo.report.report_run"), patch.object(multicase, "generate_case") as generate:
                result = batch.run_batch(resume=b.name)
            generate.assert_not_called(); cfg.assert_not_called()
            self.assertEqual(result["cases"][0]["status"], "interrupted_unknown")
            self.assertEqual(result["summary"]["generation_attempted"], 1)
            self.assertEqual(result["summary"]["requested_generation_attempts"], 3)
            self.assertEqual(read_json_for_test(g / "manifest.json")["status"], "running")

    def test_disk_guard_stops_before_first_external_stage(self):
        import hashlib
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); b = root / "batch-fixture"; b.mkdir(); c = config()
            write_json(b / "manifest.json", {"run_id": b.name, "kind": "development_batch", "status": "batch_stopped",
                       "active_seconds": 0, "unaccounted_time_bound_seconds": 0, "budget_seconds": 21600,
                       "minimum_free_bytes": 20 * 2**30, "screening": [], "cases": [{"case_id": c["case_id"], "source_kind": "aidev",
                       "repo_url": c["repo_url"], "config_sha256": hashlib.sha256(json.dumps(c, sort_keys=True).encode()).hexdigest(),
                       "status": "pending", "stages": {}}]})
            with patch.object(batch, "run_path", side_effect=lambda x: root / x), patch.object(batch, "case_config", return_value=c), \
                 patch.object(batch.shutil, "disk_usage", return_value=type("Usage", (), {"free": 1})()), \
                 patch("ci_demo.report.report_run"), patch.object(multicase, "reproduce_case") as reproduce:
                result = batch.run_batch(resume=b.name)
            reproduce.assert_not_called()
            self.assertEqual(result["status"], "batch_stopped")
            self.assertEqual(result["summary"]["generation_unexecuted"], 3)


def read_json_for_test(path):
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__": unittest.main()
