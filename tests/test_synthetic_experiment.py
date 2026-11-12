"""Resume fixtures contain no real model calls or Docker execution."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from ci_demo.common import sha256, write_json
from ci_demo.synthetic_experiment import generate_one


class SyntheticExperimentTests(unittest.TestCase):
    def test_completed_generation_and_verification_are_read_without_reissue(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root / "generation/manifest.json", {"kind": "fixture"})
            write_json(root / "verification/manifest.json", {"status": "verification_finished", "attempts": [{"status": "execution_verified"}]})
            operations = {"synthetic-generate-fault": {"status": "finished", "result": {"run_id": "generation", "manifest_sha256": sha256(root / "generation/manifest.json")}},
                          "synthetic-verify-fault": {"status": "finished", "result": {"run_id": "verification", "manifest_sha256": sha256(root / "verification/manifest.json")}}}
            write_json(root / "manifest.json", {"operations": operations})
            experiment = Mock(manifest=root / "manifest.json")
            with patch("ci_demo.synthetic_experiment.run_path", side_effect=lambda name: root / name), \
                 patch("ci_demo.synthetic_experiment.multicase.generate_case") as generate, \
                 patch("ci_demo.synthetic_experiment.multicase.verify_case") as verify:
                result = generate_one(experiment, {"source_case_id": "fault"}, "http://127.0.0.1:11434", root)
                self.assertEqual(result["execution_verified"], 1)
                generate.assert_not_called()
                verify.assert_not_called()
                experiment.reserve.assert_not_called()
                (root / "generation/manifest.json").write_text("changed")
                with self.assertRaises(ValueError):
                    generate_one(experiment, {"source_case_id": "fault"}, "http://127.0.0.1:11434", root)


if __name__ == "__main__":
    unittest.main()
