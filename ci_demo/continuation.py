"""Pinned, read-only parent lineage and the v1.2 continuation schedule."""
from __future__ import annotations

import math
from collections import Counter
from datetime import datetime
from pathlib import Path
import shutil

from .common import ROOT, read_json, sha256, write_json, now


def training_plan(name):
    if name not in {"M2", "M5"}:
        raise ValueError("Continuation v1.2 only supports M2/M5")
    count = 175 if name == "M2" else 276
    per_epoch = math.ceil(count / 8)
    return {"target_epochs": 10, "train_examples": count, "steps_per_epoch": per_epoch,
            "max_steps": 10 * per_epoch, "parent_step": 104,
            "remaining_updates": 10 * per_epoch - 104,
            "learning_rate": 2e-5, "validation_steps": [n * per_epoch for n in (6, 8, 10)]}


def expected_exposures(sample_ids, step, plan):
    import torch
    epochs, updates = divmod(step, plan["steps_per_epoch"])
    counts = Counter({sid: epochs for sid in sample_ids})
    order = torch.randperm(len(sample_ids), generator=torch.Generator().manual_seed(5417 + epochs)).tolist()
    counts.update(sample_ids[i] for i in order[:updates * 8])
    return counts


def project_file(relative):
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT.resolve()):
        raise ValueError("Continuation lineage escaped project")
    return path


def checked_checkpoint(path):
    from .sft import CHECKPOINT_FILES
    evidence = read_json(path / "checkpoint-evidence.json")
    if set(evidence["files"]) != set(CHECKPOINT_FILES):
        raise ValueError("Incomplete continuation parent checkpoint")
    if any(sha256(path / name) != expected for name, expected in evidence["files"].items()):
        raise ValueError("Continuation checkpoint changed")
    return evidence


def load_spec(dataset_path):
    spec_path = ROOT / "data-manifests/training-v1.2.json"
    spec = read_json(spec_path)
    if (spec["protocol"] != "v1.2" or sha256(dataset_path) != spec["dataset_sha256"]
            or spec["plans"] != {name: training_plan(name) for name in ("M2", "M5")}
            or spec["stage_limits_seconds"] != {"training_each": 10800, "training_M2": 10800, "training_M5": 10800, "evaluation": 7200}):
        raise ValueError("Continuation policy/dataset differs from approved plan")
    for name, parent in spec["parents"].items():
        folder = project_file("runs/" + parent["run_id"])
        for relative, expected in parent["files"].items():
            path = project_file(relative)
            if not path.is_relative_to(folder) or sha256(path) != expected:
                raise ValueError("Pinned parent artifact changed")
        manifest = read_json(folder / "manifest.json")
        if manifest["config"]["model"] != name or manifest["config"]["dataset_sha256"] != spec["dataset_sha256"]:
            raise ValueError("Wrong continuation parent model/data")
        expected_status = "training_finished" if name in {"M2", "M5"} else "validation_finished"
        if manifest["status"] != expected_status:
            raise ValueError("Parent run incomplete")
        if name in {"M2", "M5"}:
            if not manifest.get("reload_verified"):
                raise ValueError("Parent adapter not reload verified")
            for step in (52, 104):
                checkpoint = folder / "checkpoints" / ("checkpoint-" + str(step))
                checked_checkpoint(checkpoint)
                if read_json(checkpoint / "trainer_state.json")["global_step"] != step:
                    raise ValueError("Parent training step mismatch")
                if read_json(checkpoint / "experiment-config.json") != read_json(folder / "training-config.json"):
                    raise ValueError("Parent training configuration mismatch")
            selection = read_json(folder / "checkpoint-selection.json")
            sample_ids = read_json(folder / "training-sample-ids.json")
            actual = read_json(folder / "checkpoints/checkpoint-104/exposures.json")["exposures"]
            if Counter(actual) != expected_exposures(sample_ids, 104, training_plan(name)):
                raise ValueError("Parent data order differs from seedable epoch sampler")
            if [c["step"] for c in selection["candidates"]] != [52, 104]:
                raise ValueError("Parent validation history incomplete")
            for candidate in selection["candidates"]:
                if (project_file(candidate["checkpoint"]) != folder / "checkpoints" / ("checkpoint-" + str(candidate["step"]))
                        or sha256(project_file(candidate["metrics_path"])) != candidate["metrics_sha256"]):
                    raise ValueError("Parent validation lineage changed")
    if set(spec["parents"]) != {"M0", "M1", "M2", "M5"}:
        raise ValueError("Continuation requires four pinned parent runs")
    return spec


def check_ready(dataset_path):
    from .learning import check_prepared_pilot
    data = check_prepared_pilot(dataset_path)
    data.pop("optimizer_updates_per_sft")
    data["qualification"] = "Dataset bytes/gates checked; no model executed by this command"
    spec = load_spec(dataset_path)
    free = shutil.disk_usage(ROOT).free / 1024 ** 3
    if free < 20:
        raise ValueError("Continuation requires at least 20 GiB free")
    return {"status": "ready_continuation_no_model_run", "training_protocol": "v1.2",
            "dataset": data, "plans": spec["plans"], "free_storage_gib": free,
            "stage_limits_seconds": spec["stage_limits_seconds"]}


def make_scheduler(optimizer, total_steps):
    from torch.optim.lr_scheduler import LambdaLR
    remaining = total_steps - 104
    if remaining not in {116, 246}:
        raise ValueError("Unexpected continuation step budget")
    for group in optimizer.param_groups:
        group["lr"] = group["initial_lr"] = 2e-5
    return LambdaLR(optimizer, lambda k: max(0.0, 1 - k / remaining))


class ContinuationTrainerMixin:
    """Only bootstrap replaces the exhausted schedule; child resume restores it."""
    continuation_plan = None
    continuation_bootstrap = False
    continuation_folder = None

    def _get_train_sampler(self, train_dataset=None):
        if self.continuation_plan is None:
            return super()._get_train_sampler(train_dataset)
        import torch
        from torch.utils.data import Sampler
        trainer = self
        dataset = self.train_dataset if train_dataset is None else train_dataset

        class ResumeSampler(Sampler):
            def __len__(self):
                return len(dataset)
            def __iter__(self):
                # Accelerate's skip wrapper resets its iteration; derive epoch from committed updates instead.
                epoch = trainer.state.global_step // trainer.continuation_plan["steps_per_epoch"]
                return iter(torch.randperm(len(dataset), generator=torch.Generator().manual_seed(5417 + epoch)).tolist())

        return ResumeSampler()

    def create_scheduler(self, num_training_steps, optimizer=None):
        if self.continuation_plan is None:
            return super().create_scheduler(num_training_steps, optimizer)
        if self.lr_scheduler is None:
            self.lr_scheduler = make_scheduler(optimizer if optimizer is not None else self.optimizer, num_training_steps)
            self._created_lr_scheduler = True
        return self.lr_scheduler

    def _load_optimizer_and_scheduler(self, checkpoint):
        super()._load_optimizer_and_scheduler(checkpoint)
        if self.continuation_plan and self.continuation_bootstrap:
            old_lrs = [g["lr"] for g in self.optimizer.param_groups]
            self.lr_scheduler = make_scheduler(self.optimizer, self.continuation_plan["max_steps"])
            write_json(self.continuation_folder / "scheduler-transition.json", {
                "recorded_at": now(), "parent_checkpoint": str(checkpoint), "parent_step": 104,
                "previous_lrs": old_lrs, "new_lrs": [g["lr"] for g in self.optimizer.param_groups],
                "remaining_updates": self.continuation_plan["remaining_updates"],
                "qualification": "Optimizer moments restored; only LR/scheduler restarted. Later child resume does not restart schedule."})


def inherited_choices(config):
    parent = project_file("runs/" + config["parent_run_id"])
    return read_json(parent / "checkpoint-selection.json")["candidates"]


def verify_selected_parent(checkpoint, name, dataset_path):
    spec = load_spec(dataset_path)
    parent = project_file("runs/" + spec["parents"][name]["run_id"])
    if checkpoint not in {parent / "checkpoints/checkpoint-52", parent / "checkpoints/checkpoint-104"}:
        raise ValueError("Selected checkpoint outside pinned parent lineage")
    checked_checkpoint(checkpoint)


def cost_record(config, experiment, stage):
    parent = read_json(project_file("runs/" + config["parent_run_id"] + "/manifest.json"))
    intervals = sorted((datetime.fromisoformat(r["reserved_at"]), datetime.fromisoformat(r.get("finished_at", now())))
                       for r in read_json(experiment.manifest)["operations"].values() if r["stage"] == stage)
    used, end = 0.0, None
    for left, right in intervals:
        used += max(0, (right - (max(left, end) if end else left)).total_seconds())
        end = max(end, right) if end else right
    parent_seconds = (datetime.fromisoformat(parent["finished_at"]) - datetime.fromisoformat(parent["created_at"])).total_seconds()
    return {"parent_run_id": parent["run_id"], "parent_wall_seconds": parent_seconds,
            "continuation_stage_charged_seconds": used, "parent_plus_continuation_seconds": parent_seconds + used,
            "qualification": "Child union includes all prior invocations and nested validation once; idle between closed operations excluded. Current operation measured just before finish."}
