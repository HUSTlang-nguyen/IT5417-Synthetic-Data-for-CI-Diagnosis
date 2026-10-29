"""Software fixtures only: no model calls, generated-code execution or research data."""
from contextlib import ExitStack
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ci_demo import comparison, ollama
from ci_demo.common import read_json, sha256, write_json
from scripts import demo


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        workspace = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.root = workspace / "runs"
        self.root.mkdir()
        self.stack.enter_context(patch("ci_demo.common.RUNS", self.root))

    def make_run(self, index, *, status="verification_finished", attempts=3, image="fixture-image"):
        folder = self.root / ("fixture-" + str(index))
        folder.mkdir()
        for name in ("prompt.txt", "original.py", "tests.py"):
            (folder / name).write_text("# software fixture only\n", encoding="utf-8")
        manifest = {"kind": "synthetic_generation", "run_id": folder.name,
                    "model": ollama.MODELS[index], "status": status, "source": {"head": "fixture-head"},
                    "options": ollama.OPTIONS, "attempt_count": 3,
                    "passing_seed": {"source_commit": "fixture-head", "image_id": image,
                                     "source_hash": sha256(folder / "original.py"),
                                     "test_hash": sha256(folder / "tests.py")},
                    "attempts": [{"index": i + 1, "status": "invalid_output", "generation_seconds": 0.2}
                                 for i in range(attempts)]}
        write_json(folder / "manifest.json", manifest)
        return folder.name

    def test_zero_accepted_is_a_complete_comparison_with_full_denominators(self):
        ids = [self.make_run(i) for i in range(2)]
        before = [(self.root / run / "manifest.json").read_bytes() for run in ids]
        result = comparison.compare_runs(ids)
        self.assertEqual(result["status"], "comparison_finished")
        for model in result["models"]:
            self.assertEqual(model["execution_verified"], 0)
            self.assertEqual(model["requested"], 3)
            self.assertEqual(model["status_counts"], {"invalid_output": 3})
            self.assertEqual(model["generation_seconds"], 0.6)
        html = (self.root / result["run_id"] / "report.html").read_text(encoding="utf-8")
        self.assertIn("0/3", html)
        self.assertIn("chờ người duyệt", html)
        self.assertEqual(before, [(self.root / run / "manifest.json").read_bytes() for run in ids])

    def test_environment_failure_preserves_unexecuted_attempts_and_unknown_timing(self):
        failed = self.make_run(0, status="environment_error", attempts=0)
        finished = self.make_run(1)
        result = comparison.compare_runs([failed, finished])
        self.assertEqual(result["status"], "comparison_incomplete")
        self.assertTrue(result["protocol_compatible"])
        self.assertEqual(result["models"][0]["unexecuted"], 3)
        self.assertIsNone(result["models"][0]["generation_seconds"])
        self.assertEqual(result["models"][1]["recorded_attempts"], 3)

    def test_mismatched_images_are_not_comparable(self):
        result = comparison.compare_runs([self.make_run(0), self.make_run(1, image="other-fixture")])
        self.assertFalse(result["protocol_compatible"])
        self.assertIn("protocol_mismatch:image_id", result["comparison_issues"])
        self.assertEqual(result["status"], "comparison_incomplete")

    def test_modified_snapshot_is_reported(self):
        ids = [self.make_run(i) for i in range(2)]
        (self.root / ids[0] / "tests.py").write_text("# modified fixture\n", encoding="utf-8")
        result = comparison.compare_runs(ids)
        self.assertIn(ollama.MODELS[0] + ":snapshot_hash_mismatch", result["comparison_issues"])
        self.assertFalse(result["protocol_compatible"])

    def test_saved_error_text_is_escaped_in_comparison_report(self):
        ids = [self.make_run(0, status="environment_error", attempts=0), self.make_run(1)]
        path = self.root / ids[0] / "manifest.json"
        manifest = read_json(path)
        manifest["error"] = '<script>alert("fixture")</script>'
        write_json(path, manifest)
        result = comparison.compare_runs(ids)
        html = (self.root / result["run_id"] / "report.html").read_text(encoding="utf-8")
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_duplicate_model_and_historical_runs_are_rejected(self):
        run = self.make_run(0)
        with self.assertRaises(ValueError):
            comparison.compare_runs([run, run])
        path = self.root / run / "manifest.json"
        manifest = read_json(path)
        manifest["kind"] = "historical_reproduction"
        write_json(path, manifest)
        with self.assertRaises(ValueError):
            comparison.compare_runs([run, run])

    def test_preflight_failure_still_saves_both_denominators(self):
        checks = {"run_id": "fixture-doctor", "target_gpu_matches": True,
                  "checks": {"docker": {"exit_code": 1, "timed_out": False, "server_os": None},
                             "ollama": {"ok": False}}}
        with patch("sys.argv", ["demo.py"]), patch.object(demo, "doctor", return_value=checks), \
                patch.object(demo, "cli"):
            with self.assertRaises(RuntimeError):
                demo.main()
        folders = list(self.root.glob("comparison-*"))
        self.assertEqual(len(folders), 1)
        manifest = read_json(folders[0] / "manifest.json")
        self.assertEqual(manifest["status"], "comparison_incomplete")
        self.assertIn("Docker", manifest["error"])
        self.assertIn("Ollama", manifest["error"])
        self.assertEqual([m["unexecuted"] for m in manifest["models"]], [3, 3])

    def test_first_model_failure_does_not_skip_second_model(self):
        second = self.make_run(1)
        checks = {"run_id": "fixture-doctor", "target_gpu_matches": True,
                  "checks": {"docker": {"exit_code": 0, "timed_out": False, "server_os": "linux"},
                             "ollama": {"ok": True}}}
        generated = []

        def stage(*args, **kwargs):
            if args[0] == "generate":
                generated.append(args[2])
                if args[2] == ollama.MODELS[0]:
                    raise RuntimeError("fixture transport failure")
                return second

        with patch("sys.argv", ["demo.py", "--skip-reproduce"]), \
                patch.object(demo, "doctor", return_value=checks), patch.object(demo, "cli", side_effect=stage), \
                patch.object(demo, "ROOT", self.root.parent):
            with self.assertRaises(RuntimeError):
                demo.main()
        self.assertEqual(generated, list(ollama.MODELS))
        folder = next(self.root.glob("comparison-*"))
        manifest = read_json(folder / "manifest.json")
        self.assertEqual(manifest["models"][0]["unexecuted"], 3)
        self.assertEqual(manifest["models"][1]["run_id"], second)


if __name__ == "__main__":
    unittest.main()
