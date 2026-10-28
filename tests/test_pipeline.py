"""Host-only regression tests; no generated code executes on the host."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from ci_demo import ollama, pipeline, runner
from ci_demo.common import case_config, command, write_json
from ci_demo.report import render

class ProposalTests(unittest.TestCase):
    def proposal(self, **changes):
        value = {"path": "properr/__init__.py", "content": "nominal = lambda v: 0\n",
                 "proposed_label": "logic", "explanation": "controlled regression"}
        value.update(changes)
        return value

    def test_only_allowlisted_file(self):
        for path in ("../outside.py", "/tmp/a.py", "tests/test_import.py", ".github/workflows/ci.yml"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                pipeline.validate_proposal(self.proposal(path=path), "original")

    def test_invalid_envelopes_and_unchanged(self):
        for content in ("", "original", "\x00", "```python\nx=1\n```", "x" * 32769):
            with self.subTest(content=content[:20]), self.assertRaises(ValueError):
                pipeline.validate_proposal(self.proposal(content=content), "original")
        with self.assertRaises(ValueError):
            pipeline.validate_proposal({**self.proposal(), "extra": True}, "original")
        with self.assertRaises(ValueError):
            pipeline.validate_proposal(self.proposal(content=42), "original")

    def test_accepts_new_source_without_evaluating_it(self):
        source = "raise RuntimeError('test fixture only')\n"
        self.assertEqual(pipeline.validate_proposal(self.proposal(content=source), "original"), source)

    def test_local_endpoint_only(self):
        self.assertEqual(ollama.endpoint_url("http://127.0.0.1:11434"), "http://127.0.0.1:11434")
        for url in ("https://example.com", "http://127.0.0.1:11434/api", "http://u:p@localhost", "http://localhost?x=y"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                ollama.endpoint_url(url)

    def test_case_is_pinned(self):
        case = case_config()
        self.assertEqual(case["record_id"], 3256868569)
        self.assertEqual(case["head"], "8fd30245ed66b5145d651efc9203eb9a911e95d5")
        self.assertEqual(case["allowed_file"], "properr/__init__.py")

class VerificationTests(unittest.TestCase):
    def test_addresses_vary_but_assertion_values_must_match(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            results = []
            for index, message in enumerate(("assert 1 == 0 at 0xabc", "assert 1 == 0 at 0xdef", "assert 2 == 0 at 0xdef")):
                name = str(index) + ".xml"
                (folder / name).write_text('<testsuites><testcase name="x"><failure message="' + message + '"/></testcase></testsuites>')
                results.append({"exit_code": 1, "timed_out": False, "junit": name})
            self.assertEqual(runner.failure_signature(results[0], folder), runner.failure_signature(results[1], folder))
            self.assertNotEqual(runner.failure_signature(results[0], folder), runner.failure_signature(results[2], folder))

    def test_three_matching_failures_and_restored_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "failure.xml").write_text('<testsuites><testsuite><testcase name="x"><failure type="AssertionError" message="bad"/></testcase></testsuite></testsuites>')
            passed = {"exit_code": 0, "timed_out": False}
            failed = {"exit_code": 1, "timed_out": False, "junit": "failure.xml"}
            self.assertTrue(runner.accepted(passed, [failed] * 3, passed, folder))
            self.assertFalse(runner.accepted(passed, [failed] * 2, passed, folder))
            self.assertFalse(runner.accepted(passed, [passed] * 3, passed, folder))
            self.assertFalse(runner.accepted(failed, [failed] * 3, passed, folder))
            self.assertFalse(runner.accepted(passed, [failed] * 3, failed, folder))
            timed = {**failed, "timed_out": True}
            self.assertFalse(runner.accepted(passed, [failed, timed, failed], passed, folder))
            (folder / "different.xml").write_text('<testsuites><testcase name="different"><error message="other"/></testcase></testsuites>')
            different = {**failed, "junit": "different.xml"}
            self.assertFalse(runner.accepted(passed, [failed, different, failed], passed, folder))

    def test_missing_or_malformed_reports_do_not_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "bad.xml").write_text("not XML")
            self.assertFalse(runner.evidence_failure({"exit_code": 1, "timed_out": False}, folder))
            self.assertFalse(runner.evidence_failure({"exit_code": 2, "timed_out": False, "junit": "bad.xml"}, folder))

    def test_docker_is_constrained_and_no_shell(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            candidate = folder / "candidate.py"
            candidate.write_text("pass")
            fake = {"exit_code": 0, "timed_out": False, "stdout": "x", "stderr": "y"}
            with patch("ci_demo.runner.command", return_value=fake.copy()) as call:
                runner.execute(case_config(), folder, "candidate", candidate=candidate)
            args = call.call_args_list[0].args[0]
            for option in ("--network=none", "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges", "--pids-limit=128", "--memory=512m"):
                self.assertIn(option, args)
            self.assertIn("readonly", next(x for x in args if "type=bind" in x))
            self.assertNotIn("--privileged", args)
            self.assertIn("rm", call.call_args_list[-1].args[0])

    def test_test_manifest_is_not_gold(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            manifest = {"kind": "synthetic_generation", "run_id": "<script>alert(1)</script>",
                        "status": "generation_finished", "created_at": "now", "model": "<b>model</b>",
                        "attempt_count": 3, "attempts": [{"index": 1, "directory": "attempt-01", "status": "invalid_output"}]}
            html = render(folder, manifest)
            self.assertNotIn("<script>alert", html)
            self.assertIn("&lt;script&gt;", html)
            self.assertIn("0/3", html)
            self.assertIn("chờ người duyệt", html)

    def test_timeout_is_evidence_not_exception(self):
        import sys
        with tempfile.TemporaryDirectory() as directory:
            result = command([sys.executable, "-c", "import time; time.sleep(2)"],
                             Path(directory), "timeout", timeout=0.05)
            self.assertTrue(result["timed_out"])
            self.assertIsNone(result["exit_code"])

if __name__ == "__main__":
    unittest.main()
