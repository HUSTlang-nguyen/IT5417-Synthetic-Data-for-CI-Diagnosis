"""Scheduler fixtures never execute source/candidates, Docker, or models."""
from pathlib import Path
from datetime import datetime, timedelta, timezone
import tempfile
import unittest
from unittest.mock import patch

from ci_demo.common import read_json, write_json, sha256
from ci_demo.dataset_experiment import freeze_plan, ordered_cases, reproduce, summary
from ci_demo.experiment import Experiment


class DatasetExperimentTests(unittest.TestCase):
    def test_plan_lock_refuses_source_patch_mutation_and_role_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "run"
            folder.mkdir()
            write_json(root / "cases/case/case.json", {"case_id": "case"})
            (root / "repair.patch").write_text("fixture repair")
            (root / "test.patch").write_text("fixture tests")
            case = {"experiment_role": "train", "repo_url": "https://github.com/example/repo", "source_case_id": "source",
                    "repair_patch": "repair.patch", "test_patch": "test.patch", "repair_patch_sha256": sha256(root / "repair.patch"),
                    "test_patch_sha256": sha256(root / "test.patch")}
            plan = {"targets": {"real": 250}, "repo_roles": {"example/repo": "train"},
                    "selected": [{"case_id": "case", "source_case_id": "source", "repo": "example/repo", "role": "train"}]}
            path = root / "dataset-v1-plan.json"
            write_json(path, plan)
            experiment = type("FixtureExperiment", (), {"folder": folder})()
            with patch("ci_demo.dataset_experiment.ROOT", root), patch("ci_demo.dataset_experiment.case_config", return_value=case):
                freeze_plan(experiment, path)
                (root / "test.patch").write_text("changed tests")
                with self.assertRaises(ValueError):
                    freeze_plan(experiment, path)
                plan["repo_roles"]["example/repo"] = "test"
                alternate = root / "other-plan.json"
                write_json(alternate, plan)
                with self.assertRaises(ValueError):
                    freeze_plan(experiment, alternate)

    def test_environment_profiles_preserve_attempt_denominator_but_deduplicate_real_cases(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            state = {"operations": {"real-old": {"status": "finished", "artifacts": {"case_id": "old"},
                         "result": {"historical_supported": False}},
                    "real-corrected": {"status": "finished", "artifacts": {"case_id": "corrected"},
                         "result": {"historical_supported": True, "head_passed": True}}}}
            write_json(folder / "manifest.json", state)
            experiment = type("FixtureExperiment", (), {"folder": folder, "manifest": folder / "manifest.json"})()
            plan = {"selected": [{"case_id": "corrected", "role": "test"}]}
            with patch("ci_demo.dataset_experiment.case_config", return_value={"source_case_id": "same-real", "experiment_role": "test"}):
                result = summary(experiment, plan)["by_role"]["test"]
            self.assertEqual(result["attempted"], 2)
            self.assertEqual(result["attempted_source_cases"], 1)
            self.assertEqual(result["strict_reproduced"], 1)

    def test_roles_are_interleaved_and_resume_never_replays_failure(self):
        plan = {"selected": [{"case_id": "t1", "role": "train"}, {"case_id": "t2", "role": "train"},
                             {"case_id": "v1", "role": "validation"}, {"case_id": "e1", "role": "test"}],
                "targets": {"train": 2, "validation": 1, "test": 1}}
        self.assertEqual([r["case_id"] for r in ordered_cases(plan)], ["t1", "v1", "e1", "t2"])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "experiment"
            folder.mkdir()
            write_json(folder / "manifest.json", {"kind": "dataset_sft_experiment", "status": "running",
                "deadline": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
                "stage_limits_seconds": {"real_reproduction": 4000}, "request_limits": {}})
            def new_run(_):
                destination = root / ("reproduce-" + str(len(list(root.glob("reproduce-*")))))
                destination.mkdir()
                return destination
            with patch("ci_demo.experiment.run_path", return_value=folder), patch("ci_demo.experiment.CACHE", root), \
                 patch("ci_demo.dataset_experiment.new_run", side_effect=new_run), \
                 patch("ci_demo.dataset_experiment.case_config", side_effect=lambda x: {"case_id": x, "source_case_id": x, "experiment_role": next(r["role"] for r in plan["selected"] if r["case_id"] == x)}), \
                 patch("ci_demo.dataset_experiment.sha256", return_value="fixture-hash"), \
                 patch("ci_demo.dataset_experiment.multicase.reproduce_case", return_value={"status": "environment_error", "error": "fixture"}) as run:
                exp = Experiment("run")
                result = reproduce(exp, plan)
                self.assertEqual(run.call_count, 4)
                self.assertEqual(result["by_role"]["train"]["attempted"], 2)
                self.assertEqual(result["by_role"]["train"]["strict_reproduced"], 0)
                reproduce(exp, plan)
                self.assertEqual(run.call_count, 4)
                state = read_json(exp.manifest)
                state["operations"]["real-t1"]["status"] = "reserved"
                write_json(exp.manifest, state)
                with self.assertRaises(RuntimeError):
                    reproduce(exp, plan)
                self.assertEqual(run.call_count, 4)


if __name__ == "__main__":
    unittest.main()
