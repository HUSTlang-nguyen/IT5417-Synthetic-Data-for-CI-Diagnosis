"""One frozen M1-P2 validation and final-test trial, with explicit no-reissue resume."""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time

from .batch import batch_lock, BudgetStop
from .common import ROOT, CACHE, now, new_run, read_json, write_json, sha256, run_path
from .diagnosis import evaluate
from .experiment import Experiment
from .learning import load_locked_dataset
from .ml import SYSTEM, prepare_input, load_model, verify_checkpoint
from .sft import final_model_lock, predict_rows, bound_json
from .synthetic_experiment import gpu_trace


M1_P2 = SYSTEM.replace(
    "Diagnose the technical cause of the observed CI failure using only the execution log and retrieved code. ",
    "Diagnose this CI failure. ").replace(
    "Return one JSON object and no markdown:",
    "Output JSON only, starting with { and ending with }. No ``` fences:")
CODE_FILES = ("ci_demo/evaluation.py", "ci_demo/ml.py", "ci_demo/sft.py", "ci_demo/learning.py", "ci_demo/diagnosis.py",
              "ci_demo/experiment.py", "ci_demo/continuation.py", "ci_demo/common.py")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def project_path(relative):
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT.resolve()):
        raise ValueError("Evaluation artifact escaped workspace")
    return path


def verify_spec(path):
    spec = read_json(path)
    if (spec.get("evaluation_protocol") != "evaluation-v1" or spec.get("parser") != "strict-json-v1"
            or spec.get("m1_prompt") != M1_P2 or spec.get("old_prompt") != SYSTEM
            or spec.get("max_requests") != 151):
        raise ValueError("Evaluation policy differs from frozen plan")
    if spec["code_sha256"] != {name: sha256(ROOT / name) for name in CODE_FILES}:
        raise ValueError("Evaluation code changed; do not resume silently")
    dataset = project_path(spec["dataset_path"])
    if sha256(dataset) != spec["dataset_sha256"]:
        raise ValueError("Evaluation dataset lock changed")
    if final_model_lock(dataset, spec["run_ids"]) != spec["trained_model_lock"]:
        raise ValueError("Evaluation model lineage changed")
    state = read_json(run_path(spec["experiment_run_id"]) / "manifest.json")
    if (state["mode"] != "manual_learning_v1.2" or state["stage_limits_seconds"]["evaluation"] != 7200
            or state["request_limits"] != {"generator_7b": 0, "diagnoser_3b_inference": 1500}):
        raise ValueError("Existing evaluation budget policy changed")
    return spec


class EvaluationRequests:
    def __init__(self, experiment, run_id):
        self.experiment, self.run_id = experiment, run_id

    def __getattr__(self, name):
        return getattr(self.experiment, name)

    def reserve(self, operation, stage, *, request_role=None, timeout=0):
        operations = read_json(self.experiment.manifest)["operations"]
        used = sum(k.startswith(self.run_id + "-") and r.get("request_role") == "diagnoser_3b_inference" for k, r in operations.items())
        if request_role and operation not in operations and used >= 151:
            raise BudgetStop("Frozen evaluation request cap 151 reached")
        return self.experiment.reserve(operation, stage, request_role=request_role, timeout=timeout)


def frozen_rows(spec, tokenizer, role):
    rows, _ = load_locked_dataset(project_path(spec["dataset_path"]), tokenizer)
    rows = [r for r in rows if r["role"] == role]
    if len(rows) != (37 if role == "validation" else 38):
        raise ValueError("Unexpected evaluation denominator")
    lock = read_json(project_path(spec["dataset_path"]))
    exports = {r["sample_id"]: project_path(r["directory"]) for r in lock["records"]}
    for row in rows:
        reconstructed = prepare_input(read_json(exports[row["sample_id"]] / "input.json"), tokenizer, include_messages=True)
        messages = reconstructed.pop("messages")
        if reconstructed != row["prepared"] or messages[0]["content"] != SYSTEM:
            raise ValueError("Original user-message reconstruction changed")
        row["user_message_sha256"] = digest(messages[1]["content"])
        changed = [{"role": "system", "content": M1_P2}, messages[1]]
        ids = tokenizer.apply_chat_template(changed, tokenize=True, add_generation_prompt=True)
        if len(ids) + 384 > 2048:
            raise ValueError("M1-P2 exceeds budget; do not trim frozen user message")
        row["prepared_p2"] = {**row["prepared"], "input_ids": ids, "input_tokens": len(ids),
                              "prompt_sha256": hashlib.sha256(json.dumps(ids).encode()).hexdigest()}
    cohort = [{"sample_id": r["sample_id"], "input_sha256": r["input_sha256"],
               "prompt_sha256": r["prepared"]["prompt_sha256"]} for r in rows]
    if cohort != spec["cohorts"][role]:
        raise ValueError("Frozen evaluation cohort/input changed")
    if role == "validation":
        old = read_json(run_path(spec["run_ids"][1]) / "prepared-inputs.json")
        cached = {r["sample_id"]: r["prepared"] for r in old if r["role"] == role}
        if any(cached[r["sample_id"]] != r["prepared"] for r in rows):
            raise ValueError("M1-P2 differs from historical user inputs")
    return rows


def gpu_ready():
    if shutil.disk_usage(ROOT).free < 20 * 1024 ** 3:
        raise BudgetStop("Evaluation requires 20 GiB free")
    result = subprocess.run(["nvidia-smi", "--query-gpu=memory.free,utilization.gpu", "--format=csv,noheader,nounits"],
                            capture_output=True, text=True, timeout=15, check=True)
    values = [float(v.strip()) for v in result.stdout.splitlines()[0].split(",")]
    if values[0] < 6144 or values[1] > 10:
        raise BudgetStop("GPU busy or less than 6 GiB available; do not interfere with other work")
    return {"free_mib": values[0], "utilization_percent": values[1], "checked_at": now()}


def cached_phase(folder):
    path = folder / "completed.json"
    if not path.exists():
        return None
    saved = read_json(path)
    for relative, expected in saved["files"].items():
        if sha256(project_path(relative)) != expected:
            raise ValueError("Completed evaluation phase changed")
    return saved["metrics"]


def model_phase(experiment, spec, root, role, name, rows, model_info):
    folder = root / (role + "-" + name)
    previous = cached_phase(folder)
    if previous is not None:
        return previous
    experiment.check("evaluation", timeout=180)
    records = spec["trained_model_lock"]["models"]
    selected_rows = [{**r, "prepared": r["prepared_p2"]} for r in rows] if name == "M1-P2" else rows
    if name == "M0":
        import joblib
        classifier = joblib.load(run_path(records[name]["run_id"]) / "classifier.joblib")
        values = classifier.predict([r["model_text"] for r in rows])
        predictions = {r["sample_id"]: {"cause_type": str(v), "locations": [], "explanation": ""} for r, v in zip(rows, values)}
        metrics = evaluate([r["reference"] for r in rows], predictions)
        metrics = {k: metrics[k] for k in ("macro_f1", "classification_accuracy", "per_class", "confusion", "reference_quality")}
        metrics["localization"] = "not_applicable_classifier_only"
        write_json(folder / "predictions.json", predictions)
        write_json(folder / "metrics.json", metrics)
    else:
        import torch
        from transformers import set_seed
        from peft import PeftModel
        usage = gpu_ready()
        monitor = root / "gpu-monitor" / (role + "-" + name + "-" + str(time.time_ns()))
        monitor.mkdir(parents=True)
        write_json(monitor / "preflight.json", usage)
        started = time.monotonic()
        model = None
        try:
            with gpu_trace(monitor, detailed=True):
                set_seed(5417)
                model, tokenizer = load_model(model_info["local_dir"])
                if name in {"M2", "M5"}:
                    model = PeftModel.from_pretrained(model, project_path(records[name]["checkpoint"]), local_files_only=True, is_trainable=False)
                model.eval()
                metrics = predict_rows(EvaluationRequests(experiment, root.name), model, tokenizer, selected_rows, folder,
                    stage="evaluation", identity=root.name + "-" + role + "-" + name, resume=True)
        finally:
            del model
            gc.collect()
            torch.cuda.empty_cache()
        write_json(folder / "runtime.json", {"seconds": time.monotonic() - started,
                   "prompt_version": "m1-format-p2" if name == "M1-P2" else "original", "system_prompt": M1_P2 if name == "M1-P2" else SYSTEM})
    files = {str(p.relative_to(ROOT)): sha256(p) for p in folder.rglob("*") if p.is_file()}
    bound_json(folder / "completed.json", {"metrics": metrics, "files": files})
    return metrics


def run(manifest_path, resume=None):
    with batch_lock(CACHE / "model-execution.lock"):
        spec = verify_spec(manifest_path)
        experiment = Experiment(spec["experiment_run_id"])
        pointer = CACHE / "evaluation-v1.json"
        if resume:
            folder = run_path(resume)
            state = read_json(folder / "manifest.json")
            if (not pointer.exists() or read_json(pointer)["run_id"] != resume
                    or state.get("kind") != "frozen_diagnosis_evaluation"
                    or state.get("specification_sha256") != sha256(manifest_path)):
                raise ValueError("Evaluation resume identity/policy mismatch")
            for key, value in read_json(experiment.manifest)["operations"].items():
                if key.startswith(folder.name + "-master-") and value["status"] == "reserved":
                    experiment.finish(key, "unknown", error="Previous evaluation worker ended; explicit resume")
        else:
            if pointer.exists():
                raise ValueError("Evaluation already exists; inspect and use --resume " + read_json(pointer)["run_id"])
            gpu_ready()
            experiment.check("evaluation", timeout=300)
            folder = new_run("evaluation")
            state = {"kind": "frozen_diagnosis_evaluation", "run_id": folder.name, "created_at": now(),
                     "specification_sha256": sha256(manifest_path), "models": {}, "validation": {}}
            write_json(folder / "manifest.json", state)
            write_json(pointer, {"run_id": folder.name})
        if state.get("status") == "evaluation_finished":
            finished = [v for k, v in read_json(experiment.manifest)["operations"].items()
                        if k.startswith(folder.name + "-master-") and v["status"] == "finished"]
            if not finished or finished[-1]["result"]["manifest_sha256"] != sha256(folder / "manifest.json"):
                raise ValueError("Completed evaluation manifest changed")
            for relative, expected in state["phase_commitments"].items():
                path = project_path(relative)
                if sha256(path) != expected:
                    raise ValueError("Completed evaluation commitment changed")
                cached_phase(path.parent)
            return state
        shared_test_lock = experiment.folder / "final-config-lock.json"
        if shared_test_lock.exists() and read_json(shared_test_lock).get("evaluation_run_id") != folder.name:
            raise ValueError("Final test already locked by another evaluation; never run a second trial")
        operations = read_json(experiment.manifest)["operations"]
        operation = folder.name + "-master-" + str(sum(k.startswith(folder.name + "-master-") for k in operations))
        experiment.reserve(operation, "evaluation", timeout=300)
        experiment.attach(operation, run_id=folder.name, artifact=str(folder.relative_to(ROOT)))
        state.update(status="running", current_operation=operation)
        state.pop("error", None)
        write_json(folder / "manifest.json", state)
        print("Evaluation run:", folder.name, flush=True)
        try:
            from transformers import AutoTokenizer
            model_info = read_json(experiment.folder / "diagnoser-model.json")
            verify_checkpoint(model_info, read_json(experiment.folder / "diagnoser-file-sha256.json"))
            tokenizer = AutoTokenizer.from_pretrained(model_info["local_dir"], local_files_only=True, trust_remote_code=False)
            validation = frozen_rows(spec, tokenizer, "validation")
            state["validation"]["M1-P2"] = model_phase(experiment, spec, folder, "validation", "M1-P2", validation, model_info)
            write_json(folder / "manifest.json", state)
            test = frozen_rows(spec, tokenizer, "test")
            if not (folder / "final-test-lock.json").exists():
                write_json(folder / "final-test-preflight.json", gpu_ready())
            test_lock = {"evaluation_protocol": "evaluation-v1", "evaluation_run_id": folder.name,
                         "specification_sha256": sha256(manifest_path), "source_training_lock": spec["trained_model_lock"],
                         "m1_p2_binding": {"base_source_run": spec["run_ids"][1], "weights": "base_no_adapter",
                                           "system_prompt": M1_P2, "prompt_version": "m1-format-p2"},
                         "prompts": {"M1-P2": M1_P2, "M2": SYSTEM, "M5": SYSTEM}, "parser": "strict-json-v1",
                         "m1_validation_sha256": sha256(folder / "validation-M1-P2/completed.json"),
                         "test_samples": [{"sample_id": r["sample_id"], "input_sha256": r["input_sha256"],
                                           "user_message_sha256": r["user_message_sha256"],
                                           "original_prompt_sha256": r["prepared"]["prompt_sha256"],
                                           "m1_p2_prompt_sha256": r["prepared_p2"]["prompt_sha256"]} for r in test]}
            bound_json(folder / "final-test-lock.json", test_lock)
            bound_json(shared_test_lock, test_lock)
            print("Final test locked:", sha256(folder / "final-test-lock.json"), flush=True)
            for name in ("M0", "M1-P2", "M2", "M5"):
                state["models"][name] = model_phase(experiment, spec, folder, "test", name, test, model_info)
                write_json(folder / "manifest.json", state)
                print(name, json.dumps(state["models"][name], ensure_ascii=False), flush=True)
            state["phase_commitments"] = {str(p.relative_to(ROOT)): sha256(p) for p in folder.glob("*/completed.json")}
            state.update(status="evaluation_finished", finished_at=now())
            write_json(folder / "manifest.json", state)
            experiment.finish(operation, "finished", result={"run_id": folder.name, "manifest_sha256": sha256(folder / "manifest.json")})
            return state
        except (Exception, KeyboardInterrupt) as exc:
            state.update(status="evaluation_interrupted" if isinstance(exc, KeyboardInterrupt) else "evaluation_failed", error=repr(exc), finished_at=now())
            write_json(folder / "manifest.json", state)
            experiment.finish(operation, "failed", result={"run_id": folder.name}, error=repr(exc))
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--resume", metavar="EVALUATION_RUN_ID")
    args = parser.parse_args()
    print(json.dumps(run(args.manifest, args.resume), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
