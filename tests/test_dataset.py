"""Annotation boundary checks use inert source strings only."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from ci_demo.common import read_json, write_json, sha256
from ci_demo.dataset import audit_real_exports, check_assessment, export_real


class DatasetTests(unittest.TestCase):
    def test_draft_audit_preserves_small_sample_gates_and_rejects_changed_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for role, value in (("base", 1), ("head", 2)):
                path = root / "source" / role / "a.py"
                path.parent.mkdir(parents=True)
                path.write_text(f"def cause():\n    return {value}\n")
            source = {"case_id": "fixture", "source_case_id": "fixture", "experiment_role": "train",
                "repo_url": "https://github.com/example/repo", "base": "a" * 40, "head": "base+repair:fixture",
                "allowed_file": "a.py", "repair_patch_sha256": "b" * 64}
            raw = {"source": source, "environment": {"context": str(root / "source"),
                   "inventories": {role: {"a.py": sha256(root / "source" / role / "a.py")} for role in ("base", "head")}}}
            write_json(root / "raw/manifest.json", raw)
            record = root / "records/fixture"
            write_json(record / "input.json", {"execution_log": "fixture AssertionError", "code": []})
            write_json(record / "reference.json", {"sample_id": "fixture", "cause_type": "logic/value",
                       "locations": [{"file": "a.py", "function": "cause"}]})
            write_json(record / "manifest.json", {"origin": "real_local_reconstruction", "quality": "silver",
                "role": "train", "sample_id": "fixture", "repo": source["repo_url"], "run_id": "raw",
                "input_sha256": sha256(record / "input.json"), "reference_sha256": sha256(record / "reference.json"),
                "evidence_hashes": {"manifest.json": sha256(root / "raw/manifest.json")},
                "retrieval": {"method": "fixture"}})
            with patch("ci_demo.dataset.run_path", return_value=root / "raw"):
                result = audit_real_exports(root / "records")
                self.assertFalse(result["real_gate_ready"])
                self.assertEqual(result["independent_source_identities"], 1)
                self.assertIn("fewer_than_250_independent_real_situations", result["remaining_gates"])
                (record / "input.json").write_text("tampered")
                with self.assertRaises(ValueError):
                    audit_real_exports(root / "records")

    def test_silver_requires_causal_explanation_and_real_function_not_test_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "base").mkdir()
            (root / "base/a.py").write_text("raise RuntimeError('never import')\ndef cause():\n    return 1\n")
            raw = {"environment": {"context": tmp}}
            assessment = {"quality": "silver", "disposition": "include", "cause_type": "logic/value",
                "confidence": "medium", "mechanism": "A fixture causal explanation", "evidence_reason": "Fixture assertion",
                "limitations": "Software fixture only", "label_source": "fixture", "locations": [{"file": "a.py", "function": "cause"}]}
            self.assertEqual(check_assessment(assessment, raw), [("a.py", "cause")])
            assessment["locations"][0]["function"] = "test_detection"
            with self.assertRaises(ValueError):
                check_assessment(assessment, raw)
            assessment["locations"][0]["function"] = "cause"
            for key, value in (("quality", "gold"), ("mechanism", ""), ("actor", "agent")):
                changed = {**assessment, key: value}
                with self.assertRaises(ValueError):
                    check_assessment(changed, raw)

    def test_review_and_repair_information_never_enters_exported_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "source/base").mkdir(parents=True)
            (root / "source/base/a.py").write_text("def cause():\n    return 1\n")
            (root / "run").mkdir()
            (root / "run/base.stdout.txt").write_text('File "/source/base/a.py", line 2\nAssertionError')
            raw = {"source": {"source_case_id": "real-1", "case_id": "case-1", "experiment_role": "train",
                "repo_url": "https://github.com/example/source", "base": "a" * 40, "dataset_revision": "b" * 40},
                "environment": {"context": str(root / "source"), "image_id": "sha256:fixture"},
                "base": {"stdout": "base.stdout.txt"}}
            assessment = {"run_id": "run", "evidence_hashes": {"fixture": "hash"}, "quality": "silver",
                "disposition": "include", "cause_type": "logic/value", "confidence": "high",
                "locations": [{"file": "a.py", "function": "cause"}], "mechanism": "SECRET_REFERENCE_EXPLANATION",
                "evidence_reason": "fixture", "limitations": "fixture", "label_source": "fixture"}
            write_json(root / "assessment.json", assessment)
            with patch("ci_demo.dataset.real_evidence", return_value=(raw, {"fixture": "hash"})), \
                 patch("ci_demo.dataset.run_path", return_value=root / "run"):
                export_real("run", root / "assessment.json", root / "output")
                text = (root / "output/input.json").read_text()
                self.assertNotIn("SECRET_REFERENCE", text)
                self.assertNotIn("cause_type", text)
                self.assertEqual(read_json(root / "output/reference.json")["quality"], "silver")
                retriever = Mock(return_value={"snippets": [], "method": "fixture_v2_export"})
                export_real("run", root / "assessment.json", root / "new-input-version", retriever=retriever)
                retriever.assert_called_once_with(root / "source/base", (root / "run/base.stdout.txt").read_text())
                self.assertEqual(read_json(root / "new-input-version/manifest.json")["retrieval"]["method"], "fixture_v2_export")
                for field in ("sample_id", "cause_type", "locations", "explanation"):
                    self.assertEqual(read_json(root / "new-input-version/reference.json")[field], read_json(root / "output/reference.json")[field])
                with self.assertRaises(ValueError):
                    export_real("run", root / "assessment.json", root / "output")


if __name__ == "__main__":
    unittest.main()
