"""Locked-data baselines and independent QLoRA runs; all target code remains text."""
from __future__ import annotations

import argparse
from collections import Counter
import gc
import hashlib
import json
import math
from pathlib import Path
import time

from .batch import batch_lock
from .common import CACHE, ROOT, new_run, now, read_json, run_path, sha256, write_json
from .diagnosis import evaluate
from .experiment import active_experiment
from .learning import fit_classifier, load_locked_dataset, select_checkpoint, training_example, update_budget
from .ml import SYSTEM, infer, load_model, verify_checkpoint


def predict_rows(experiment, model, tokenizer, rows, folder, *, stage, identity):
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
            except Exception as exc:
                write_json(item / "error.json", {"recorded_at": now(), "error": repr(exc)})
                experiment.finish(operation, "failed", error=repr(exc))
                raise
    finally:
        metrics = evaluate([r["reference"] for r in rows], predictions)
        write_json(folder / "predictions.json", predictions)
        write_json(folder / "metrics.json", {**metrics, "requested": len(rows), "returned": len(predictions)})
    return metrics


def collate_examples(examples, pad_token_id):
    import torch
    length = math.ceil(max(len(x["input_ids"]) for x in examples) / 8) * 8
    batch = {}
    for name, pad in (("input_ids", pad_token_id), ("attention_mask", 0), ("labels", -100)):
        batch[name] = torch.tensor([x[name] + [pad] * (length - len(x[name])) for x in examples], dtype=torch.long)
    batch["sample_ids"] = [x["sample_id"] for x in examples]
    return batch


def run_learning(dataset_path, name, *, context=2048):
    if name not in {"M0", "M1", "M2", "M5"} or context not in {1024, 2048}:
        raise ValueError("Unsupported learning protocol")
    experiment = active_experiment()
    experiment.configure_learning_stages()
    dataset_path = Path(dataset_path).resolve()
    # Reject a draft before importing torch, reserving a model call, or creating a training run.
    if read_json(dataset_path).get("status") != "locked":
        raise ValueError("Dataset not locked; do not train an undersized substitute")
    dataset_hash = sha256(dataset_path)
    operation = "fit-" + name + "-" + dataset_hash[:16] + "-ctx" + str(context)
    stage = "training_" + name if name in {"M2", "M5"} else "evaluation"
    reservation = experiment.reserve(operation, stage, timeout=300)
    if reservation["status"] == "finished":
        return reservation["result"]
    folder = new_run("learning-" + name.lower())
    model_info = read_json(experiment.folder / "diagnoser-model.json")
    config = {"model": name, "base_model": model_info["repo_id"], "base_revision": model_info["revision"],
              "dataset_sha256": dataset_hash, "context": context, "output_budget": 384, "seed": 5417,
              "system_prompt": SYSTEM, "implementation_sha256": sha256(__file__),
              "checkpoint_inventory_sha256": sha256(experiment.folder / "diagnoser-file-sha256.json")}
    manifest = {"kind": "diagnosis_learning", "run_id": folder.name, "created_at": now(), "status": "running", "config": config}
    write_json(folder / "manifest.json", manifest)
    experiment.attach(operation, run_id=folder.name, artifact=str(folder.relative_to(ROOT)))
    try:
        with batch_lock(CACHE / "model-execution.lock"):
            verify_checkpoint(model_info, read_json(experiment.folder / "diagnoser-file-sha256.json"))
            from transformers import AutoTokenizer, set_seed
            set_seed(5417)
            tokenizer = AutoTokenizer.from_pretrained(model_info["local_dir"], local_files_only=True, trust_remote_code=False)
            rows, gate = load_locked_dataset(dataset_path, tokenizer, context=context)
            write_json(folder / "data-gates.json", gate)
            write_json(folder / "prepared-inputs.json", [{"sample_id": r["sample_id"], "role": r["role"], "origin": r["origin"],
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
                                       identity=folder.name + "-validation")
                manifest.update(status="validation_finished", validation_metrics=metrics)
            else:
                manifest.update(train_sft(experiment, model_info, tokenizer, rows, train, validation, folder, stage, config))
        manifest["finished_at"] = now()
        write_json(folder / "manifest.json", manifest)
        experiment.finish(operation, "finished", result={"run_id": folder.name, "artifact": str(folder.relative_to(ROOT)), "status": manifest["status"]})
        return manifest
    except Exception as exc:
        manifest.update(status="failed", error=repr(exc), finished_at=now())
        write_json(folder / "manifest.json", manifest)
        experiment.finish(operation, "failed", result={"run_id": folder.name}, error=repr(exc))
        raise


def train_sft(experiment, model_info, tokenizer, rows, train, validation, folder, stage, config):
    import torch
    from transformers import Trainer, TrainerCallback, TrainingArguments
    from peft import LoraConfig, PeftModel, get_peft_model, get_peft_model_state_dict, prepare_model_for_kbit_training
    from safetensors.torch import load_file
    examples = [training_example(row, tokenizer) for row in train]
    updates = update_budget(rows)
    midpoint = math.ceil(updates / 2)
    configuration = {**config, "max_steps": updates, "real_train": sum(r["origin"] == "real_local_reconstruction" for r in train),
        "synthetic_train": sum(r["origin"] == "controlled_synthetic" for r in train), "lora_rank": 16, "lora_alpha": 32,
        "lora_dropout": .05, "target_modules": "all-linear", "learning_rate": 1e-4, "batch_size": 1,
        "gradient_accumulation_steps": 8, "loss": "response_only", "validation_steps": [midpoint, updates]}
    write_json(folder / "training-config.json", configuration)
    write_json(folder / "training-sample-ids.json", [r["sample_id"] for r in train])
    tracking = {"examples": 0, "input_tokens": 0, "target_tokens": 0, "exposures": Counter(),
                "peak_allocated_bytes": 0, "peak_reserved_bytes": 0}
    choices = []
    start = time.monotonic()
    model, _ = load_model(model_info["local_dir"])
    load_seconds = time.monotonic()-start
    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model, gradient_checkpointing_kwargs={"use_reentrant": False})
    model = get_peft_model(model, LoraConfig(r=16, lora_alpha=32, lora_dropout=.05, target_modules="all-linear", task_type="CAUSAL_LM", bias="none"))
    torch.cuda.reset_peak_memory_stats()

    def capture_memory():
        tracking["peak_allocated_bytes"] = max(tracking["peak_allocated_bytes"], torch.cuda.max_memory_allocated())
        tracking["peak_reserved_bytes"] = max(tracking["peak_reserved_bytes"], torch.cuda.max_memory_reserved())

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

        def on_log(self, args, state, control, logs=None, **kwargs):
            capture_memory()
            with (folder / "training-events.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps({"recorded_at": now(), "step": state.global_step, "epoch": state.epoch,
                                         "logs": logs, "tracking": tracking}, default=str) + "\n")

        def on_step_end(self, args, state, control, **kwargs):
            capture_memory()
            if state.global_step in {midpoint, updates}:
                control.should_save = True
            return control

        def on_save(self, args, state, control, **kwargs):
            checkpoint = folder / "checkpoints" / ("checkpoint-" + str(state.global_step))
            write_json(checkpoint / "experiment-config.json", configuration)
            write_json(checkpoint / "exposures.json", tracking)
            if state.global_step not in {midpoint, updates}:
                return
            capture_memory()
            model.eval()
            try:
                metrics = predict_rows(experiment, model, tokenizer, validation, folder / ("validation-step-" + str(state.global_step)),
                    stage=stage, identity=folder.name + "-val" + str(state.global_step))
            finally:
                capture_memory()
                model.train()
            choices.append({"step": state.global_step, "joint_top1": metrics["joint_top1"],
                            "checkpoint": str(checkpoint.relative_to(ROOT)), "metrics": metrics})
            write_json(folder / "checkpoint-selection.json", {"candidates": choices, "selected": select_checkpoint(choices),
                       "rule": "validation_joint_class_function_top1_then_earliest_step"})

    args = TrainingArguments(output_dir=str(folder / "checkpoints"), max_steps=updates, learning_rate=1e-4,
        per_device_train_batch_size=1, gradient_accumulation_steps=8, seed=5417, data_seed=5417,
        bf16=True, fp16=False, optim="adamw_torch", lr_scheduler_type="linear", warmup_ratio=0,
        logging_strategy="steps", logging_steps=1, logging_nan_inf_filter=False,
        save_strategy="steps", save_steps=midpoint, eval_strategy="no", report_to=[],
        gradient_checkpointing=True, gradient_checkpointing_kwargs={"use_reentrant": False},
        remove_unused_columns=False, dataloader_num_workers=0)
    (folder / "trainer-arguments.json").write_text(args.to_json_string(), encoding="utf-8")
    trainer = TrackingTrainer(model=model, args=args, train_dataset=examples,
        data_collator=lambda batch: collate_examples(batch, tokenizer.eos_token_id), callbacks=[EvidenceCallback()])
    train_started = time.monotonic()
    result = trainer.train()
    capture_memory()
    train_seconds = time.monotonic()-train_started
    trainer.save_state()
    selected = select_checkpoint(choices)
    write_json(folder / "training-summary.json", {"tracking": tracking, "trainer_metrics": result.metrics,
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
    return {"status": "training_finished", "selected_checkpoint": selected["checkpoint"], "training": tracking,
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


def evaluate_final_test(dataset_path, run_ids):
    experiment = active_experiment()
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
    parser.add_argument("--dataset", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--model", choices=["M0", "M1", "M2", "M5"])
    mode.add_argument("--test-runs", nargs=4, metavar="RUN_ID")
    parser.add_argument("--context", type=int, choices=[1024, 2048], default=2048)
    args = parser.parse_args()
    result = evaluate_final_test(args.dataset, args.test_runs) if args.test_runs else run_learning(args.dataset, args.model, context=args.context)
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
