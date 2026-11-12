"""Locked-data baselines and independent QLoRA runs; all target code remains text."""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import nullcontext
import gc
import hashlib
import json
import math
from pathlib import Path
import time

from .batch import batch_lock
from .common import CACHE, ROOT, new_run, now, read_json, run_path, sha256, write_json
from .diagnosis import evaluate
from .experiment import active_experiment, manual_learning_experiment
from .learning import fit_classifier, load_locked_dataset, select_checkpoint, training_example, update_budget
from .ml import SYSTEM, infer, load_model, verify_checkpoint
from .synthetic_experiment import gpu_trace


def predict_rows(experiment, model, tokenizer, rows, folder, *, stage, identity, resume=False):
    folder.mkdir(parents=True, exist_ok=True)
    phase = {"identity": identity, "stage": stage, "samples": [{"sample_id": r["sample_id"], "input_sha256": r["input_sha256"],
             "prompt_sha256": r["prepared"]["prompt_sha256"]} for r in rows]}
    if (folder / "phase.json").exists():
        if read_json(folder / "phase.json") != phase:
            raise ValueError("Cannot resume a prediction phase with different inputs")
    elif any(folder.iterdir()):
        raise ValueError("Existing prediction artifacts lack their phase checkpoint")
    else:
        write_json(folder / "phase.json", phase)
    predictions = {}
    try:
        for row in rows:
            key = hashlib.sha256(row["sample_id"].encode()).hexdigest()[:20]
            operation = identity + "-" + key
            if resume:
                prior = read_json(experiment.manifest).get("operations", {}).get(operation)
                if prior and prior["status"] != "finished":
                    # An uncertain request is never called again, even if its response file exists.
                    note = folder / (key + "-unreturned.json")
                    if not note.exists():
                        write_json(note, {"recorded_at": now(),
                        "sample_id": row["sample_id"], "operation": operation, "prior_status": prior["status"],
                        "qualification": "Unreturned/uncertain prior request counts as an error; not reissued"})
                    if prior["status"] == "reserved":
                        experiment.finish(operation, "unknown", error="Unreturned prediction at explicit resume; not reissued")
                    continue
            reservation = experiment.reserve(operation, stage, request_role="diagnoser_3b_inference", timeout=180)
            if reservation["status"] == "finished":
                saved = ROOT / reservation["result"]["artifact"]
                if sha256(saved) != reservation["result"]["sha256"]:
                    raise ValueError("Saved model response changed before resume")
                previous = read_json(saved)
                predictions[row["sample_id"]] = previous["parsed"]
                continue
            item = folder / key
            item.mkdir()
            experiment.attach(operation, sample_id=row["sample_id"], artifact=str(item.relative_to(ROOT)))
            write_json(item / "request.json", {"recorded_at": now(), "sample_id": row["sample_id"],
                "input_sha256": row["input_sha256"], "prepared": row["prepared"],
                "do_sample": False, "max_new_tokens": 384, "max_time_seconds": 180})
            try:
                result = infer(model, tokenizer, row["prepared"])
                write_json(item / "result.json", result)
                predictions[row["sample_id"]] = result["parsed"]
                experiment.finish(operation, "finished", result={"artifact": str((item / "result.json").relative_to(ROOT)),
                                  "sha256": sha256(item / "result.json")})
            except (Exception, KeyboardInterrupt) as exc:
                write_json(item / "error.json", {"recorded_at": now(), "error": repr(exc)})
                experiment.finish(operation, "failed", error=repr(exc))
                raise
    finally:
        metrics = evaluate([r["reference"] for r in rows], predictions)
        write_json(folder / "predictions.json", predictions)
        write_json(folder / "metrics.json", {**metrics, "requested": len(rows), "returned": len(predictions)})
    return metrics


def bound_json(path, value):
    if path.exists():
        if read_json(path) != value:
            raise ValueError("Resume configuration/input changed: " + path.name)
    else:
        write_json(path, value)


CHECKPOINT_FILES = ("adapter_model.safetensors", "adapter_config.json", "trainer_state.json",
                    "optimizer.pt", "scheduler.pt", "rng_state.pth", "experiment-config.json", "exposures.json")


def seal_checkpoint(path):
    if any(not (path / name).is_file() for name in CHECKPOINT_FILES):
        raise ValueError("Training checkpoint lacks optimizer/RNG/adapter evidence")
    write_json(path / "checkpoint-evidence.json", {"created_at": now(),
        "files": {name: sha256(path / name) for name in CHECKPOINT_FILES}})


def resume_checkpoint(folder, config):
    complete = []
    for evidence in (folder / "checkpoints").rglob("checkpoint-evidence.json"):
        path = evidence.parent.resolve()
        if not path.is_relative_to((folder / "checkpoints").resolve()):
            raise ValueError("Resume checkpoint escaped its run")
        saved = read_json(evidence)
        if set(saved["files"]) != set(CHECKPOINT_FILES) or any(sha256(path / k) != v for k, v in saved["files"].items()):
            raise ValueError("Saved training checkpoint changed")
        if read_json(path / "experiment-config.json") != config:
            raise ValueError("Resume checkpoint configuration changed")
        step = read_json(path / "trainer_state.json")["global_step"]
        if not isinstance(step, int) or not 0 < step <= config["max_steps"]:
            raise ValueError("Invalid saved training step")
        complete.append((step, saved["created_at"], path))
    if not complete:
        raise ValueError("No complete checkpoint to resume; interrupted artifacts are preserved")
    return max(complete, key=lambda item: (item[0], item[1]))[2]


def collate_examples(examples, pad_token_id):
    import torch
    length = math.ceil(max(len(x["input_ids"]) for x in examples) / 8) * 8
    batch = {}
    for name, pad in (("input_ids", pad_token_id), ("attention_mask", 0), ("labels", -100)):
        batch[name] = torch.tensor([x[name] + [pad] * (length - len(x[name])) for x in examples], dtype=torch.long)
    batch["sample_ids"] = [x["sample_id"] for x in examples]
    return batch


def run_learning(dataset_path, name, *, context=2048, resume=None, experiment=None, smoke=False):
    with batch_lock(CACHE / "model-execution.lock"):
        return _run_learning(dataset_path, name, context=context, resume=resume, experiment=experiment, smoke=smoke)


def _run_learning(dataset_path, name, *, context, resume, experiment, smoke):
    if name not in {"M0", "M1", "M2", "M5"} or context not in {1024, 2048}:
        raise ValueError("Unsupported learning protocol")
    if smoke and (name != "M2" or resume):
        raise ValueError("Runtime smoke uses a fresh M2 adapter only, never a research/resume result")
    experiment = experiment or active_experiment()
    experiment.configure_learning_stages()
    dataset_path = Path(dataset_path).resolve()
    # Reject a draft before importing torch, reserving a model call, or creating a training run.
    if read_json(dataset_path).get("status") != "locked":
        raise ValueError("Dataset not locked; do not train an undersized substitute")
    dataset_hash = sha256(dataset_path)
    logical = ("smoke-" if smoke else "fit-") + name + "-" + dataset_hash[:16] + "-ctx" + str(context)
    stage = "training_" + name if name in {"M2", "M5"} else "evaluation"
    model_info = read_json(experiment.folder / "diagnoser-model.json")
    config = {"model": name, "purpose": "runtime_smoke" if smoke else "research", "base_model": model_info["repo_id"], "base_revision": model_info["revision"],
              "dataset_sha256": dataset_hash, "context": context, "output_budget": 384, "seed": 5417,
              "system_prompt": SYSTEM, "implementation_sha256": sha256(__file__),
              "checkpoint_inventory_sha256": sha256(experiment.folder / "diagnoser-file-sha256.json")}
    state = read_json(experiment.manifest)
    previous = [(key, value) for key, value in state.get("operations", {}).items()
                if key == logical or key.startswith(logical + "-resume-")]
    finished = [value for _, value in previous if value["status"] == "finished"]
    if finished:
        saved = finished[-1]["result"]
        if "manifest_sha256" in saved and sha256(run_path(saved["run_id"]) / "manifest.json") != saved["manifest_sha256"]:
            raise ValueError("Completed learning manifest changed")
        return finished[-1]["result"]
    if resume:
        folder = run_path(resume)
        manifest = read_json(folder / "manifest.json")
        if (manifest.get("kind") != "diagnosis_learning" or manifest.get("config") != config
                or manifest.get("experiment_run_id") != experiment.folder.name
                or manifest.get("logical_operation") != logical):
            raise ValueError("Resume run/model/dataset/config/study identity mismatch")
        if name == "M0":
            raise ValueError("Interrupted M0 fitting is not silently repeated; inspect its classifier artifacts")
        if name in {"M2", "M5"}:
            resume_checkpoint(folder, read_json(folder / "training-config.json"))
        for key, value in previous:
            if value["status"] == "reserved":
                experiment.finish(key, "unknown", error="Explicit resume after prior worker ended; no model replay")
        operation = logical + "-resume-" + str(len(previous))
    else:
        if previous:
            raise ValueError("Prior run exists; use --resume RUN_ID after inspecting its artifacts")
        operation = logical
        folder = None
    experiment.reserve(operation, stage, timeout=300)
    if folder is None:
        folder = new_run("learning-" + ("smoke-" if smoke else "") + name.lower())
        manifest = {"kind": "diagnosis_learning", "run_id": folder.name, "created_at": now(),
                    "config": config, "experiment_run_id": experiment.folder.name, "logical_operation": logical}
    manifest.update(status="running", current_operation=operation)
    write_json(folder / "manifest.json", manifest)
    print("Run:", folder.name, "Model:", name, "Artifacts:", folder, flush=True)
    experiment.attach(operation, run_id=folder.name, artifact=str(folder.relative_to(ROOT)))
    try:
        monitor = folder / "gpu-monitor" / operation
        if name != "M0":
            monitor.mkdir(parents=True, exist_ok=False)
            write_json(monitor / "columns.json", {"columns": ["timestamp", "gpu_util_percent", "temperature_c", "power_w", "memory_used_mib"], "interval_ms": 250})
        with gpu_trace(monitor, detailed=True) if name != "M0" else nullcontext():
            verify_checkpoint(model_info, read_json(experiment.folder / "diagnoser-file-sha256.json"))
            from transformers import AutoTokenizer, set_seed
            set_seed(5417)
            tokenizer = AutoTokenizer.from_pretrained(model_info["local_dir"], local_files_only=True, trust_remote_code=False)
            rows, gate = load_locked_dataset(dataset_path, tokenizer, context=context, model=name)
            bound_json(folder / "data-gates.json", gate)
            bound_json(folder / "prepared-inputs.json", [{"sample_id": r["sample_id"], "role": r["role"], "origin": r["origin"],
                         "prepared": r["prepared"]} for r in rows])
            train = [r for r in rows if r["role"] == "train" and (name == "M5" or r["origin"] == "real_local_reconstruction")]
            validation = [r for r in rows if r["role"] == "validation"]
            if name == "M0":
                import joblib
                started = time.monotonic()
                classifier = fit_classifier(train)
                predictions = classifier.predict([r["model_text"] for r in validation])
                parsed = {r["sample_id"]: {"cause_type": str(p), "locations": [], "explanation": ""}
                          for r, p in zip(validation, predictions)}
                all_metrics = evaluate([r["reference"] for r in validation], parsed)
                metrics = {k: all_metrics[k] for k in ("macro_f1", "classification_accuracy", "per_class", "confusion", "reference_quality")}
                metrics["localization"] = "not_applicable_classifier_only"
                write_json(folder / "validation-predictions.json", parsed)
                write_json(folder / "validation-metrics.json", metrics)
                joblib.dump(classifier, folder / "classifier.joblib")
                manifest.update(status="validation_finished", seconds=time.monotonic()-started,
                                classifier_sha256=sha256(folder / "classifier.joblib"))
            elif name == "M1":
                started = time.monotonic()
                model, tokenizer = load_model(model_info["local_dir"])
                manifest["model_load_seconds"] = time.monotonic()-started
                metrics = predict_rows(experiment, model, tokenizer, validation, folder / "validation", stage=stage,
                                       identity=folder.name + "-validation", resume=bool(resume))
                manifest.update(status="validation_finished", validation_metrics=metrics)
            else:
                manifest.update(train_sft(experiment, model_info, tokenizer, rows, train, validation, folder, stage, config, resume=bool(resume), invocation=operation, smoke=smoke))
        manifest["finished_at"] = now()
        write_json(folder / "manifest.json", manifest)
        experiment.finish(operation, "finished", result={"run_id": folder.name, "artifact": str(folder.relative_to(ROOT)),
            "status": manifest["status"], "manifest_sha256": sha256(folder / "manifest.json")})
        return manifest
    except (Exception, KeyboardInterrupt) as exc:
        for child, record in read_json(experiment.manifest).get("operations", {}).items():
            if (child.startswith(folder.name + "-") and record.get("request_role") == "diagnoser_3b_inference"
                    and record["status"] == "reserved"):
                experiment.finish(child, "unknown", error="Learning worker interrupted before a returned response; not reissued")
        manifest.update(status="interrupted" if isinstance(exc, KeyboardInterrupt) else "failed", error=repr(exc), finished_at=now())
        write_json(folder / "manifest.json", manifest)
        experiment.finish(operation, "failed", result={"run_id": folder.name}, error=repr(exc))
        raise


def train_sft(experiment, model_info, tokenizer, rows, train, validation, folder, stage, config, *, resume=False, invocation="initial", smoke=False):
    import torch
    from transformers import Trainer, TrainerCallback, TrainingArguments
    from peft import LoraConfig, PeftModel, get_peft_model, get_peft_model_state_dict, prepare_model_for_kbit_training, set_peft_model_state_dict
    from safetensors.torch import load_file
    examples = [training_example(row, tokenizer) for row in train]
    updates = 3 if smoke else update_budget(rows)
    midpoint = math.ceil(updates / 2)
    configuration = {**config, "max_steps": updates, "real_train": sum(r["origin"] == "real_local_reconstruction" for r in train),
        "synthetic_train": sum(r["origin"] == "controlled_synthetic" for r in train), "lora_rank": 16, "lora_alpha": 32,
        "lora_dropout": .05, "target_modules": "all-linear", "learning_rate": 1e-4, "batch_size": 1,
        "gradient_accumulation_steps": 8, "loss": "response_only", "validation_steps": [] if smoke else [midpoint, updates]}
    bound_json(folder / "training-config.json", configuration)
    bound_json(folder / "training-sample-ids.json", [r["sample_id"] for r in train])
    tracking = {"examples": 0, "input_tokens": 0, "target_tokens": 0, "exposures": Counter(),
                "peak_allocated_bytes": 0, "peak_reserved_bytes": 0}
    choices = []
    checkpoint = resume_checkpoint(folder, configuration) if resume else None
    resume_step = 0
    if checkpoint:
        tracking = read_json(checkpoint / "exposures.json")
        tracking["exposures"] = Counter(tracking["exposures"])
        resume_step = read_json(checkpoint / "trainer_state.json")["global_step"]
        if (folder / "checkpoint-selection.json").exists():
            choices = read_json(folder / "checkpoint-selection.json")["candidates"]
            for choice in choices:
                metrics_path = ROOT / choice["metrics_path"]
                if sha256(metrics_path) != choice["metrics_sha256"]:
                    raise ValueError("Saved checkpoint validation metrics changed")
    start = time.monotonic()
    model, _ = load_model(model_info["local_dir"])
    load_seconds = time.monotonic()-start
    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model, gradient_checkpointing_kwargs={"use_reentrant": False})
    model = get_peft_model(model, LoraConfig(r=16, lora_alpha=32, lora_dropout=.05, target_modules="all-linear", task_type="CAUSAL_LM", bias="none"))
    if checkpoint:
        set_peft_model_state_dict(model, load_file(str(checkpoint / "adapter_model.safetensors")))
    torch.cuda.reset_peak_memory_stats()

    def capture_memory():
        tracking["peak_allocated_bytes"] = max(tracking["peak_allocated_bytes"], torch.cuda.max_memory_allocated())
        tracking["peak_reserved_bytes"] = max(tracking["peak_reserved_bytes"], torch.cuda.max_memory_reserved())

    def validate(step, saved_checkpoint):
        if any(c["step"] == step for c in choices):
            return
        model.eval()
        phase = folder / ("validation-step-" + str(step))
        try:
            metrics = predict_rows(experiment, model, tokenizer, validation, phase,
                stage=stage, identity=folder.name + "-val" + str(step), resume=resume)
        finally:
            capture_memory()
            model.train()
        choices.append({"step": step, "joint_top1": metrics["joint_top1"],
                        "checkpoint": str(saved_checkpoint.relative_to(ROOT)), "metrics": metrics,
                        "metrics_path": str((phase / "metrics.json").relative_to(ROOT)),
                        "metrics_sha256": sha256(phase / "metrics.json")})
        write_json(folder / "checkpoint-selection.json", {"candidates": choices, "selected": select_checkpoint(choices),
                   "rule": "validation_joint_class_function_top1_then_earliest_step"})

    if checkpoint and resume_step in {midpoint, updates}:
        validate(resume_step, checkpoint)

    class TrackingTrainer(Trainer):
        def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):
            ids = inputs.pop("sample_ids")
            tracking["exposures"].update(ids)
            tracking["examples"] += len(ids)
            tracking["target_tokens"] += int((inputs["labels"] != -100).sum().item())
            tracking["input_tokens"] += int((inputs["attention_mask"].bool() & (inputs["labels"] == -100)).sum().item())
            result = super().compute_loss(model, inputs, return_outputs=return_outputs, num_items_in_batch=num_items_in_batch)
            loss = result[0] if return_outputs else result
            if not torch.isfinite(loss).item():
                raise FloatingPointError("Nonfinite training loss")
            return result

    class EvidenceCallback(TrainerCallback):
        def on_step_begin(self, args, state, control, **kwargs):
            experiment.check(stage, timeout=60)
            self.step_started = time.monotonic()

        def on_train_begin(self, args, state, control, **kwargs):
            self.started = time.monotonic()

        def on_log(self, args, state, control, logs=None, **kwargs):
            capture_memory()
            with (folder / "training-events.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps({"recorded_at": now(), "step": state.global_step, "epoch": state.epoch,
                                         "invocation": invocation, "elapsed_seconds": time.monotonic()-self.started,
                                         "last_update_seconds": getattr(self, "step_seconds", None),
                                         "logs": logs, "tracking": tracking}, default=str) + "\n")
            print(f"{folder.name} step {state.global_step}/{updates} {logs}", flush=True)

        def on_step_end(self, args, state, control, **kwargs):
            capture_memory()
            self.step_seconds = time.monotonic()-self.step_started
            if state.global_step in {midpoint, updates}:
                control.should_save = True
            return control

        def on_save(self, args, state, control, **kwargs):
            checkpoint = Path(args.output_dir) / ("checkpoint-" + str(state.global_step))
            write_json(checkpoint / "experiment-config.json", configuration)
            write_json(checkpoint / "exposures.json", tracking)
            seal_checkpoint(checkpoint)
            if smoke or state.global_step not in {midpoint, updates}:
                return
            validate(state.global_step, checkpoint)

    checkpoint_root = folder / "checkpoints"
    if resume:
        checkpoint_root = checkpoint_root / ("resume-" + str(time.time_ns()))
    args = TrainingArguments(output_dir=str(checkpoint_root), max_steps=updates, learning_rate=1e-4,
        per_device_train_batch_size=1, gradient_accumulation_steps=8, seed=5417, data_seed=5417,
        bf16=True, fp16=False, optim="adamw_torch", lr_scheduler_type="linear", warmup_ratio=0,
        logging_strategy="steps", logging_steps=1, logging_nan_inf_filter=False,
        save_strategy="steps", save_steps=min(20, midpoint), eval_strategy="no", report_to=[],
        gradient_checkpointing=True, gradient_checkpointing_kwargs={"use_reentrant": False},
        remove_unused_columns=False, dataloader_num_workers=0)
    write_json(folder / ("trainer-arguments-" + invocation + ".json"), args.to_dict())
    trainer = TrackingTrainer(model=model, args=args, train_dataset=examples,
        data_collator=lambda batch: collate_examples(batch, tokenizer.eos_token_id), callbacks=[EvidenceCallback()])
    train_started = time.monotonic()
    result = trainer.train(resume_from_checkpoint=str(checkpoint) if checkpoint else None) if resume_step < updates else None
    capture_memory()
    train_seconds = time.monotonic()-train_started
    if result is not None:
        trainer.save_state()
    selected = ({"step": updates, "checkpoint": str((checkpoint_root / ("checkpoint-" + str(updates))).relative_to(ROOT))}
                if smoke else select_checkpoint(choices))
    with (folder / "training-invocations.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"recorded_at": now(), "invocation": invocation, "resumed_checkpoint": str(checkpoint) if checkpoint else None,
            "committed_resume_step": resume_step, "load_seconds": load_seconds, "invocation_train_seconds": train_seconds,
            "qualification": "Checkpoint exposures count committed updates; discarded post-checkpoint work remains in prior event logs and is not erased"}) + "\n")
    write_json(folder / "training-summary.json", {"tracking": tracking, "trainer_metrics": result.metrics if result else {"completed_from_final_checkpoint": True},
               "load_seconds": load_seconds, "train_including_validation_seconds": train_seconds, "selected": selected})
    del trainer, model
    gc.collect()
    torch.cuda.empty_cache()
    experiment.check(stage, timeout=120)
    base, _ = load_model(model_info["local_dir"])
    selected_path = ROOT / selected["checkpoint"]
    reloaded = PeftModel.from_pretrained(base, selected_path, local_files_only=True, is_trainable=False)
    expected = load_file(str(selected_path / "adapter_model.safetensors"))
    actual = get_peft_model_state_dict(reloaded)
    if set(actual) != set(expected) or any(not torch.equal(actual[k].detach().cpu(), expected[k]) for k in expected):
        raise ValueError("Selected adapter reload does not match saved checkpoint tensors")
    write_json(folder / "reload-verification.json", {"recorded_at": now(), "all_adapter_tensors_match": True,
               "tensor_count": len(actual), "adapter_sha256": sha256(selected_path / "adapter_model.safetensors")})
    return {"status": "calibration_finished" if smoke else "training_finished", "selected_checkpoint": selected["checkpoint"], "training": tracking,
            "updates": updates, "model_load_seconds": load_seconds, "train_including_validation_seconds": train_seconds,
            "reload_verified": True}


def final_model_lock(dataset_path, run_ids):
    if len(run_ids) != 4 or len(set(run_ids)) != 4:
        raise ValueError("Final evaluation requires four distinct M0/M1/M2/M5 runs")
    models = {}
    dataset_hash = sha256(dataset_path)
    for run_id in run_ids:
        folder = run_path(run_id)
        raw = read_json(folder / "manifest.json")
        config = raw.get("config", {})
        name = config.get("model")
        expected = "training_finished" if name in {"M2", "M5"} else "validation_finished"
        if raw.get("kind") != "diagnosis_learning" or raw.get("status") != expected or name in models:
            raise ValueError("Incomplete or repeated final model")
        if config.get("dataset_sha256") != dataset_hash or config.get("system_prompt") != SYSTEM:
            raise ValueError("Final dataset/prompt differs from the completed model run")
        models[name] = {"run_id": run_id, "manifest_sha256": sha256(folder / "manifest.json"), "config": config}
    if set(models) != {"M0", "M1", "M2", "M5"}:
        raise ValueError("A required experimental model is absent")
    keys = ("base_model", "base_revision", "context", "checkpoint_inventory_sha256")
    if any(any(models[name]["config"][key] != models["M1"]["config"][key] for key in keys) for name in models):
        raise ValueError("Final models do not share the same base/context")
    training = {}
    for name, record in models.items():
        folder = run_path(record["run_id"])
        raw = read_json(folder / "manifest.json")
        if name == "M0":
            if sha256(folder / "classifier.joblib") != raw["classifier_sha256"]:
                raise ValueError("M0 classifier changed")
            record["classifier_sha256"] = raw["classifier_sha256"]
        elif name in {"M2", "M5"}:
            if raw.get("reload_verified") is not True:
                raise ValueError("Selected adapter was not reload-verified")
            checkpoint = (ROOT / raw["selected_checkpoint"]).resolve()
            if not checkpoint.is_relative_to((folder / "checkpoints").resolve()):
                raise ValueError("Selected adapter is outside its training run")
            selected = read_json(folder / "checkpoint-selection.json")["selected"]
            if selected["checkpoint"] != raw["selected_checkpoint"]:
                raise ValueError("Selected checkpoint changed")
            training[name] = read_json(folder / "training-config.json")
            record.update(checkpoint=raw["selected_checkpoint"], selected_step=selected["step"],
                adapter_sha256=sha256(checkpoint / "adapter_model.safetensors"),
                selection_sha256=sha256(folder / "checkpoint-selection.json"),
                training_config_sha256=sha256(folder / "training-config.json"),
                selected_exposures_sha256=sha256(checkpoint / "exposures.json"))
    shared = ("max_steps", "learning_rate", "lora_rank", "lora_alpha", "lora_dropout", "target_modules", "batch_size", "gradient_accumulation_steps", "seed", "context")
    if any(training["M2"][key] != training["M5"][key] for key in shared):
        raise ValueError("SFT training conditions differ")
    return {"dataset_sha256": dataset_hash, "models": models, "test_policy": "one_final_test_after_all_configs_and_checkpoints_locked"}


def evaluate_final_test(dataset_path, run_ids, *, experiment=None):
    experiment = experiment or active_experiment()
    experiment.configure_learning_stages()
    specification = final_model_lock(dataset_path, run_ids)
    lock = experiment.folder / "final-config-lock.json"
    with batch_lock(experiment.lock, wait_seconds=30):
        if lock.exists() and read_json(lock) != specification:
            raise ValueError("Test was already locked to a different configuration")
        if not lock.exists():
            write_json(lock, specification)
    operation = "final-test-" + sha256(lock)[:20]
    reservation = experiment.reserve(operation, "evaluation", timeout=300)
    if reservation["status"] == "finished":
        return reservation["result"]
    folder = new_run("diagnosis-test")
    manifest = {"kind": "diagnosis_final_test", "run_id": folder.name, "status": "running", "created_at": now(),
                "config_lock_sha256": sha256(lock), "models": {}}
    write_json(folder / "manifest.json", manifest)
    experiment.attach(operation, run_id=folder.name)
    try:
        with batch_lock(CACHE / "model-execution.lock"):
            from transformers import AutoTokenizer
            import joblib
            import torch
            from peft import PeftModel
            model_info = read_json(experiment.folder / "diagnoser-model.json")
            verify_checkpoint(model_info, read_json(experiment.folder / "diagnoser-file-sha256.json"))
            tokenizer = AutoTokenizer.from_pretrained(model_info["local_dir"], local_files_only=True, trust_remote_code=False)
            rows, _ = load_locked_dataset(dataset_path, tokenizer, context=specification["models"]["M1"]["config"]["context"])
            test = [r for r in rows if r["role"] == "test"]
            for name in ("M0", "M1", "M2", "M5"):
                experiment.check("evaluation", timeout=180)
                record = specification["models"][name]
                if name == "M0":
                    classifier = joblib.load(run_path(record["run_id"]) / "classifier.joblib")
                    values = classifier.predict([r["model_text"] for r in test])
                    parsed = {r["sample_id"]: {"cause_type": str(p), "locations": [], "explanation": ""} for r, p in zip(test, values)}
                    metrics = evaluate([r["reference"] for r in test], parsed)
                    metrics = {key: metrics[key] for key in ("macro_f1", "classification_accuracy", "per_class", "confusion", "reference_quality")}
                    metrics["localization"] = "not_applicable_classifier_only"
                    write_json(folder / "M0-predictions.json", parsed)
                else:
                    model, tokenizer = load_model(model_info["local_dir"])
                    if name != "M1":
                        model = PeftModel.from_pretrained(model, ROOT / record["checkpoint"], local_files_only=True, is_trainable=False)
                    model.eval()
                    metrics = predict_rows(experiment, model, tokenizer, test, folder / name, stage="evaluation", identity=record["run_id"] + "-test")
                    del model
                    gc.collect()
                    torch.cuda.empty_cache()
                manifest["models"][name] = metrics
                write_json(folder / "manifest.json", manifest)
        manifest.update(status="evaluation_finished", finished_at=now())
        write_json(folder / "manifest.json", manifest)
        experiment.finish(operation, "finished", result={"run_id": folder.name})
        return manifest
    except Exception as exc:
        manifest.update(status="evaluation_failed", error=repr(exc), finished_at=now())
        write_json(folder / "manifest.json", manifest)
        experiment.finish(operation, "failed", result={"run_id": folder.name}, error=repr(exc))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default=str(CACHE / "dataset-v1" / "locked-v1.1.json"))
    parser.add_argument("--manual", action="store_true", help="User-started v1.1 study; collection run stays unchanged")
    parser.add_argument("--resume", metavar="LEARNING_RUN_ID")
    parser.add_argument("--smoke", action="store_true", help="Three train updates and adapter reload on real train, no validation/test")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--model", choices=["M0", "M1", "M2", "M5"])
    mode.add_argument("--test-runs", nargs=4, metavar="RUN_ID")
    mode.add_argument("--check", action="store_true", help="Read readiness only; no study/model operation")
    parser.add_argument("--context", type=int, choices=[1024, 2048], default=2048)
    args = parser.parse_args()
    if args.resume and not args.model:
        parser.error("--resume requires --model")
    if args.smoke and (args.model != "M2" or args.resume):
        parser.error("--smoke requires fresh --model M2")
    if args.check:
        from .learning import check_prepared_pilot
        print(json.dumps(check_prepared_pilot(args.dataset), ensure_ascii=False), flush=True)
        return
    experiment = manual_learning_experiment(args.dataset) if args.manual else None
    result = evaluate_final_test(args.dataset, args.test_runs, experiment=experiment) if args.test_runs else run_learning(
        args.dataset, args.model, context=args.context, resume=args.resume, experiment=experiment, smoke=args.smoke)
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
