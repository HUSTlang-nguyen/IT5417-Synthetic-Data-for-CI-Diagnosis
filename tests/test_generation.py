"""Mocked transport tests ONLY; not local-model or research results."""
from contextlib import ExitStack
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from ci_demo import ollama, pipeline
from ci_demo.common import case_config, sha256


class GenerationTests(unittest.TestCase):
    def test_all_invalid_attempts_preserve_raw_output_and_denominator(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as mocks:
            root = Path(directory)
            case = case_config()
            (root / "properr").mkdir()
            (root / "tests").mkdir()
            original = root / case["allowed_file"]
            original.write_bytes(b"# original\r\nx = 1\r\n")
            tests = root / case["test_file"]
            tests.write_bytes(b"# immutable test fixture\r\n")
            folder = root / "mock-only-run"
            folder.mkdir()
            gate = {"image_id": "fixture", "source_hash": sha256(original), "test_hash": sha256(tests)}
            passed = {"exit_code": 0, "timed_out": False}
            for name, value in {
                "passing_seed": (gate, root), "new_run": folder,
                "image_identity": {"id": "fixture"}, "runner.execute": passed,
                "ollama.model_info": {"test_fixture": True}, "ollama.request": "{}",
            }.items():
                mocks.enter_context(patch("ci_demo.pipeline." + name, return_value=value))
            outside = {"path": "tests/test_import.py", "content": "x = 2", "proposed_label": "logic", "explanation": "fixture"}
            raw_outputs = ["not JSON", "[]", json.dumps({"done": True, "message": {"content": json.dumps(outside)}})]
            generate = mocks.enter_context(patch("ci_demo.pipeline.ollama.generate", side_effect=[({}, raw, 0.1) for raw in raw_outputs]))
            manifest = pipeline.generate_run(ollama.MODELS[0], 3, "http://127.0.0.1:11434")
            self.assertEqual(generate.call_count, 3)
            self.assertEqual(manifest["attempt_count"], 3)
            self.assertEqual([a["status"] for a in manifest["attempts"]], ["invalid_output"] * 3)
            self.assertEqual(sha256(folder / "original.py"), gate["source_hash"])
            self.assertEqual(sha256(folder / "tests.py"), gate["test_hash"])
            for i, raw in enumerate(raw_outputs, 1):
                attempt = folder / ("attempt-" + str(i).zfill(2))
                self.assertEqual((attempt / "response.raw.json").read_text(encoding="utf-8"), raw)
                self.assertFalse((attempt / "candidate.py").exists())

    def test_rejection_classifies_timeout_and_no_regression(self):
        from ci_demo import runner
        passed = {"exit_code": 0, "timed_out": False}
        timeout = {"exit_code": None, "timed_out": True}
        self.assertEqual(runner.rejection_reason(passed, [timeout] * 3, passed, Path(".")), "timeout")
        self.assertEqual(runner.rejection_reason(passed, [passed] * 3, passed, Path(".")), "does_not_fail_consistently")


if __name__ == "__main__":
    unittest.main()
