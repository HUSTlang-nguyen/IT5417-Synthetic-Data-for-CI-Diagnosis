"""Prediction/resume checks use saved fixture JSON, never an LLM or GPU."""
from pathlib import Path
import tempfile
import importlib.util
import unittest
from unittest.mock import Mock, patch

from ci_demo.common import sha256, write_json, read_json
from ci_demo.ml import SYSTEM
from ci_demo.sft import CHECKPOINT_FILES, collate_examples, final_model_lock, predict_rows, resume_checkpoint, run_learning, seal_checkpoint


class SFTTests(unittest.TestCase):
    def test_test_lock_requires_all_completed_models_on_identical_dataset(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset = root / "dataset.json"
            write_json(dataset, {"status": "locked"})
            runs = ["M0", "M1", "M2", "M5"]
            for name in runs:
                write_json(root / name / "manifest.json", {"kind": "diagnosis_learning",
                    "status": "validation_finished" if name in {"M0", "M1"} else "training_finished" if name == "M2" else "failed",
                    "config": {"model": name, "dataset_sha256": sha256(dataset), "system_prompt": SYSTEM}})
            with patch("ci_demo.sft.run_path", side_effect=lambda name: root / name):
                with self.assertRaises(ValueError):
                    final_model_lock(dataset, runs)
                with self.assertRaises(ValueError):
                    final_model_lock(dataset, runs[:3])

    def test_draft_dataset_rejected_before_training_reservation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "dataset.json"
            write_json(path, {"status": "draft_audit"})
            experiment = Mock()
            with patch("ci_demo.sft.active_experiment", return_value=experiment):
                with self.assertRaises(ValueError):
                    run_learning(path, "M2")
            experiment.reserve.assert_not_called()

    @unittest.skipUnless(importlib.util.find_spec("torch"), "Run this compatibility fixture in the isolated ML environment")
    def test_actual_torch_collator_preserves_response_mask_and_padding(self):
        batch = collate_examples([{"sample_id": "a", "input_ids": [1, 2, 3], "attention_mask": [1, 1, 1], "labels": [-100, -100, 3]},
                                  {"sample_id": "b", "input_ids": [4, 5], "attention_mask": [1, 1], "labels": [-100, 5]}], 0)
        self.assertEqual(tuple(batch["input_ids"].shape), (2, 8))
        self.assertEqual(batch["labels"][0].tolist(), [-100, -100, 3, -100, -100, -100, -100, -100])
        self.assertEqual(batch["sample_ids"], ["a", "b"])

    def test_prediction_resume_reads_completed_result_without_duplicate_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prediction = {"cause_type": "logic/value", "locations": [{"file": "a.py", "function": "f"}], "explanation": "fixture"}
            write_json(root / "result.json", {"parsed": prediction})
            experiment = Mock()
            experiment.reserve.return_value = {"status": "finished", "result": {"artifact": "result.json", "sha256": sha256(root / "result.json")}}
            row = {"sample_id": "fixture", "input_sha256": "fixture-sha", "prepared": {"prompt_sha256": "prompt-sha"},
                   "reference": {"sample_id": "fixture", **prediction, "retrieved_locations": prediction["locations"]}}
            with patch("ci_demo.sft.ROOT", root), patch("ci_demo.sft.infer") as inference:
                for _ in range(2):
                    result = predict_rows(experiment, None, None, [row], root / "phase", stage="evaluation", identity="fixture")
                    self.assertEqual(result["joint_top1"], 1)
                inference.assert_not_called()

                experiment.finish.assert_not_called()
                (root / "result.json").write_text("tampered response")
                with self.assertRaises(ValueError):
                    predict_rows(experiment, None, None, [row], root / "phase", stage="evaluation", identity="fixture")
                inference.assert_not_called()
                row["prepared"]["prompt_sha256"] = "changed"
                with self.assertRaises(ValueError):
                    predict_rows(experiment, None, None, [row], root / "phase", stage="evaluation", identity="fixture")

    def test_resume_checkpoint_requires_full_state_hashes_and_ignores_incomplete_save(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);config={'max_steps':104,'dataset_sha256':'fixture-data'}
            folder=root/'checkpoints/checkpoint-20';folder.mkdir(parents=True)
            for name in CHECKPOINT_FILES:write_json(folder/name,{'fixture':name})
            write_json(folder/'trainer_state.json',{'global_step':20})
            write_json(folder/'experiment-config.json',config);seal_checkpoint(folder)
            partial=root/'checkpoints/checkpoint-40';partial.mkdir();write_json(partial/'trainer_state.json',{'global_step':40})
            self.assertEqual(resume_checkpoint(root,config),folder.resolve())
            with self.assertRaises(ValueError):resume_checkpoint(root,{**config,'dataset_sha256':'changed'})
            (folder/'optimizer.pt').write_bytes(b'tampered-fixture')
            with self.assertRaises(ValueError):resume_checkpoint(root,config)

    def test_explicit_prediction_resume_never_reissues_uncertain_request(self):
        import hashlib
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);key=hashlib.sha256(b'fixture').hexdigest()[:20];operation='fixture-'+key
            write_json(root/'manifest.json',{'operations':{operation:{'status':'reserved'}}})
            exp=Mock(manifest=root/'manifest.json')
            row={'sample_id':'fixture','input_sha256':'fixture-input','prepared':{'prompt_sha256':'fixture-prompt'},
                 'reference':{'sample_id':'fixture','cause_type':'logic/value','locations':[{'file':'f.py','function':'f'}],'retrieved_locations':[]}}
            with patch('ci_demo.sft.infer') as inference:
                metrics=predict_rows(exp,None,None,[row],root/'phase',stage='evaluation',identity='fixture',resume=True)
            inference.assert_not_called();exp.reserve.assert_not_called()
            exp.finish.assert_called_once_with(operation,'unknown',error='Unreturned prediction at explicit resume; not reissued')
            saved=read_json(root/'phase/metrics.json');self.assertEqual(saved['requested'],1);self.assertEqual(saved['returned'],0)


if __name__ == "__main__":
    unittest.main()
