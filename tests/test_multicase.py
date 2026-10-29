"""Software-only fixtures. No model calls, Docker daemon or upstream code execution."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from ci_demo import batch, multicase, ollama
from ci_demo.common import write_json


def config(name="example"):
    return {"case_id": name, "runner_kind": "python-source-v2", "split": "development", "source_kind": "aidev",
            "repo_url": "https://github.com/example/" + name, "base": "a" * 40, "head": "b" * 40,
            "allowed_file": "package/api.py", "license": "MIT", "test_targets": ["tests/test_api.py"],
            "frozen_test_files": ["tests/test_api.py"], "resources": {"memory_mb": 512, "cpus": 1}, "dependencies": []}


class CaseTests(unittest.TestCase):
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
            (tree / "fixture.txt").write_text("before\n")
            patch_file = root / "fix.patch"
            patch_file.write_text("--- a/fixture.txt\n+++ b/fixture.txt\n@@ -1 +1 @@\n-before\n+after\n")
            multicase.apply_patch_file(tree, patch_file, evidence, "fixture-patch", None)
            self.assertEqual((tree / "fixture.txt").read_text(), "after\n")

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
            self.assertEqual([a["status"] for a in result["attempts"]], ["generation_error"] * 3)
            self.assertEqual(len(calls), 3)
            self.assertEqual([p["options"]["seed"] for p, kw in calls], [5417, 5418, 5419])
            self.assertTrue(all(kw["timeout"] == 180 and p["model"] == ollama.GENERATOR_MODEL for p, kw in calls))
            self.assertNotIn("SWE_GOLD_SENTINEL", (folder / "prompt.txt").read_text())

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
