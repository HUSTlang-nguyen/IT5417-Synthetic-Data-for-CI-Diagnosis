"""Software-only checks of reservation safety, not fabricated experiment outputs."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ci_demo.common import write_json, read_json
from ci_demo.experiment import Experiment
from ci_demo.batch import BudgetStop


class ExperimentTests(unittest.TestCase):
    def test_short_checkpoint_contention_waits_without_weakening_worker_lock(self):
        from concurrent.futures import ThreadPoolExecutor
        import threading
        from ci_demo.batch import batch_lock
        with tempfile.TemporaryDirectory() as tmp, ThreadPoolExecutor(max_workers=1) as executor:
            path = Path(tmp) / "metadata.lock"
            ready, acquired = threading.Event(), threading.Event()

            def writer():
                ready.set()
                with batch_lock(path, wait_seconds=2):
                    acquired.set()

            with batch_lock(path):
                future = executor.submit(writer)
                self.assertTrue(ready.wait(1))
                with self.assertRaises(RuntimeError):
                    with batch_lock(path, wait_seconds=0.03):
                        self.fail("A live lock was bypassed")
                self.assertFalse(acquired.is_set())
            future.result(timeout=2)
            self.assertTrue(acquired.is_set())

    def test_usage_limit_resume_charges_prior_work_and_preserves_deadline_and_caps(self):
        with tempfile.TemporaryDirectory() as tmp:
            current = datetime.now(timezone.utc)
            folder = self.make(tmp, stage_limits_seconds={"real_reproduction": 300, "synthetic": 600},
                stage_budget_started={"real_reproduction": (current-timedelta(hours=3)).isoformat()},
                operations={"done": {"stage": "real_reproduction", "status": "finished",
                    "reserved_at": (current-timedelta(seconds=120)).isoformat(), "finished_at": (current-timedelta(seconds=30)).isoformat()},
                    "running": {"stage": "real_reproduction", "status": "reserved", "reserved_at": (current-timedelta(seconds=10)).isoformat()}})
            original = read_json(folder / "manifest.json")
            with patch("ci_demo.experiment.run_path", return_value=folder), patch("ci_demo.experiment.CACHE", Path(tmp)):
                exp = Experiment("run")
                exp.configure_execution_accounting()
                exp.configure_execution_accounting()
                remaining = exp.check("real_reproduction")
                self.assertTrue(198 <= remaining <= 202)
                state = read_json(exp.manifest)
                self.assertEqual(state["deadline"], original["deadline"])
                self.assertEqual(state["stage_limits_seconds"], original["stage_limits_seconds"])
                self.assertEqual(state["operations"], original["operations"])
                self.assertEqual(len(state["budget_policy_events"]), 1)

    def test_later_reservation_cannot_reset_an_earlier_manual_stage_clock(self):
        with tempfile.TemporaryDirectory() as tmp:
            current = datetime.now(timezone.utc)
            folder = self.make(tmp, stages={"synthetic": {"started_at": (current-timedelta(seconds=601)).isoformat()}},
                               stage_budget_started={"synthetic": current.isoformat()})
            with patch("ci_demo.experiment.run_path", return_value=folder), patch("ci_demo.experiment.CACHE", Path(tmp)):
                exp = Experiment("run")
                with self.assertRaises(BudgetStop):
                    exp.reserve("no-reset", "synthetic")

    def make(self, root, **kwargs):
        folder = Path(root) / "run"
        folder.mkdir()
        state = {"kind": "dataset_sft_experiment", "status": "running",
                 "deadline": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
                 "stage_limits_seconds": {"synthetic": 600}, "request_limits": {"generator_7b": 1}, **kwargs}
        write_json(folder / "manifest.json", state)
        return folder

    def test_resume_completed_does_not_reserve_or_charge_second_model_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = self.make(tmp)
            with patch("ci_demo.experiment.run_path", return_value=folder), patch("ci_demo.experiment.CACHE", Path(tmp)):
                exp = Experiment("run")
                exp.reserve("model-1", "synthetic", request_role="generator_7b", timeout=10)
                with self.assertRaises(RuntimeError):
                    exp.reserve("model-1", "synthetic", request_role="generator_7b")
                exp.finish("model-1", "finished", result={"artifact": "response.raw.json"})
                self.assertEqual(exp.reserve("model-1", "synthetic")["status"], "finished")
                with self.assertRaises(BudgetStop):
                    exp.reserve("model-2", "synthetic", request_role="generator_7b")
                with self.assertRaises(ValueError):
                    exp.finish("model-1", "finished")

    def test_deadline_and_invalid_role_reject_before_reservation(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = self.make(tmp, deadline=(datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat())
            with patch("ci_demo.experiment.run_path", return_value=folder), patch("ci_demo.experiment.CACHE", Path(tmp)):
                exp = Experiment("run")
                with self.assertRaises(BudgetStop):
                    exp.reserve("late", "synthetic")
                self.assertFalse(read_json(exp.manifest).get("operations"))

    def test_nested_stage_check_and_artifact_link_preserve_reservation(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = self.make(tmp)
            with patch("ci_demo.experiment.run_path", return_value=folder), patch("ci_demo.experiment.CACHE", Path(tmp)):
                exp = Experiment("run")
                exp.reserve("case-1", "synthetic")
                exp.attach("case-1", run_id="reproduce-evidence")
                self.assertEqual(read_json(exp.manifest)["operations"]["case-1"]["artifacts"]["run_id"], "reproduce-evidence")
                self.assertGreater(exp.check("synthetic", timeout=10), 10)
                state = read_json(exp.manifest)
                state["stage_budget_started"]["synthetic"] = (datetime.now(timezone.utc) - timedelta(seconds=601)).isoformat()
                write_json(exp.manifest, state)
                with self.assertRaises(BudgetStop):
                    exp.check("synthetic")
                for value in (float("nan"), float("inf"), True, -1):
                    with self.assertRaises(ValueError):
                        exp.check("synthetic", timeout=value)

    def test_evaluation_budget_excludes_idle_gap_without_double_charging_nested_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            current = datetime.now(timezone.utc)
            folder = self.make(tmp, stage_limits_seconds={"evaluation": 600, "training_each": 7200},
                operations={"outer": {"stage": "evaluation", "reserved_at": (current-timedelta(seconds=200)).isoformat(),
                                      "finished_at": (current-timedelta(seconds=100)).isoformat()},
                            "inner": {"stage": "evaluation", "reserved_at": (current-timedelta(seconds=180)).isoformat(),
                                      "finished_at": (current-timedelta(seconds=120)).isoformat()}},
                stage_budget_started={"evaluation": (current-timedelta(hours=3)).isoformat()})
            with patch("ci_demo.experiment.run_path", return_value=folder), patch("ci_demo.experiment.CACHE", Path(tmp)):
                exp = Experiment("run")
                exp.configure_learning_stages()
                remaining = exp.check("evaluation")
                self.assertGreater(remaining, 499)
                self.assertLess(remaining, 501)
                state = read_json(exp.manifest)
                self.assertEqual(state["stage_limits_seconds"]["training_M2"], 7200)
                self.assertEqual(state["stage_limits_seconds"]["training_M5"], 7200)


if __name__ == "__main__":
    unittest.main()
