"""Locked wall-clock/request reservations for the bounded dataset/SFT experiment."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
import math
import shutil

from .batch import batch_lock, BudgetStop
from .common import CACHE, ROOT, new_run, now, read_json, run_path, sha256, write_json


class Experiment:
    def __init__(self, run_id):
        self.folder = run_path(run_id)
        self.manifest = self.folder / "manifest.json"
        if read_json(self.manifest).get("kind") != "dataset_sft_experiment":
            raise ValueError("Expected dataset/SFT experiment")
        self.lock = CACHE / "experiment-locks" / (run_id + ".lock")

    def _check(self, state, stage, timeout):
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout < 0:
            raise ValueError("Invalid timeout")
        if stage not in state["stage_limits_seconds"]:
            raise ValueError("Unknown experiment stage")
        timestamp = datetime.fromisoformat(now())
        fallback = state.get("stages", {}).get(stage, {}).get("started_at", timestamp.isoformat())
        started = min(datetime.fromisoformat(fallback), datetime.fromisoformat(state.get("stage_budget_started", {}).get(stage, fallback)))
        used = (timestamp - started).total_seconds()
        if state.get("stage_budget_modes", {}).get(stage) == "operation_union":
            intervals = sorted((datetime.fromisoformat(r["reserved_at"]), datetime.fromisoformat(r.get("finished_at", timestamp.isoformat())))
                               for r in state.get("operations", {}).values() if r.get("stage") == stage)
            used = 0
            end = None
            for left, right in intervals:
                left = max(left, end) if end is not None else left
                used += max(0, (right - left).total_seconds())
                end = max(end, right) if end is not None else right
        if state.get("deadline") is None:
            if state.get("mode") != "manual_learning_v1.1":
                raise ValueError("Only an explicit manual learning study may omit a calendar deadline")
            wall_remaining = float("inf")
        else:
            wall_remaining = (datetime.fromisoformat(state["deadline"]) - timestamp).total_seconds()
        remaining = min(wall_remaining, state["stage_limits_seconds"][stage] - used)
        if state["status"] != "running" or remaining <= timeout or shutil.disk_usage(self.folder).free < 20 * 1024 ** 3:
            raise BudgetStop("Insufficient wall/stage budget or storage before " + stage)
        return timestamp, remaining

    def configure_learning_stages(self):
        """Each independent SFT has its own cap; evaluation counts actual operation time."""
        with batch_lock(self.lock, wait_seconds=30):
            state = read_json(self.manifest)
            limits = state["stage_limits_seconds"]
            for name in ("training_M2", "training_M5"):
                if name in limits and limits[name] != limits["training_each"]:
                    raise ValueError("Independent SFT budget changed")
                limits[name] = limits["training_each"]
            state.setdefault("stage_budget_modes", {})["evaluation"] = "operation_union"
            write_json(self.manifest, state)

    def configure_execution_accounting(self):
        """Charge recorded work, including in-flight operations, without resetting any cap."""
        with batch_lock(self.lock, wait_seconds=30):
            state = read_json(self.manifest)
            if datetime.fromisoformat(now()) >= datetime.fromisoformat(state["deadline"]):
                raise BudgetStop("Experiment deadline already reached")
            modes = state.setdefault("stage_budget_modes", {})
            changed = [stage for stage in ("real_reproduction", "synthetic") if modes.get(stage) != "operation_union"]
            if changed:
                state.setdefault("budget_policy_events", []).append({"recorded_at": now(), "stages": changed,
                    "policy": "Union of existing reserved/finished operation intervals; in-flight time is charged",
                    "reason": "Resume across usage-limit idle time; original deadline, operation timestamps and stage caps remain unchanged"})
                for stage in changed:
                    modes[stage] = "operation_union"
                write_json(self.manifest, state)

    def check(self, stage, *, timeout=0):
        with batch_lock(self.lock, wait_seconds=30):
            return self._check(read_json(self.manifest), stage, timeout)[1]

    def attach(self, operation, **artifacts):
        with batch_lock(self.lock, wait_seconds=30):
            state = read_json(self.manifest)
            record = state["operations"][operation]
            if record["status"] != "reserved":
                raise ValueError("Cannot attach to terminal operation")
            record.setdefault("artifacts", {}).update(artifacts)
            write_json(self.manifest, state)

    def reserve(self, operation, stage, *, request_role=None, timeout=0):
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,160}", operation):
            raise ValueError("Invalid operation identity")
        with batch_lock(self.lock, wait_seconds=30):
            state = read_json(self.manifest)
            operations = state.setdefault("operations", {})
            if operation in operations:
                previous = operations[operation]
                if previous["status"] == "finished":
                    return previous
                raise RuntimeError("Operation already reserved; inspect prior artifacts before any new trial: " + operation)
            timestamp, remaining = self._check(state, stage, timeout)
            stage_state = state.setdefault("stage_budget_started", {})
            if request_role is not None:
                request_limits = state["request_limits"]
                if request_role not in request_limits:
                    raise ValueError("Unknown model request role")
                used = sum(r.get("request_role") == request_role for r in operations.values())
                if used >= request_limits[request_role]:
                    raise BudgetStop("Request limit reached: " + request_role)
            stage_state.setdefault(stage, state.get("stages", {}).get(stage, {}).get("started_at", timestamp.isoformat()))
            record = {"operation": operation, "stage": stage, "status": "reserved", "reserved_at": timestamp.isoformat(),
                      "request_role": request_role, "timeout_seconds": timeout,
                      "remaining_seconds_at_reservation": remaining}
            operations[operation] = record
            write_json(self.manifest, state)
            return record

    def finish(self, operation, status, *, result=None, error=None):
        if status not in {"finished", "failed", "unknown"}:
            raise ValueError("Invalid terminal operation state")
        with batch_lock(self.lock, wait_seconds=30):
            state = read_json(self.manifest)
            record = state["operations"][operation]
            if record["status"] != "reserved":
                raise ValueError("Refuse to overwrite terminal operation")
            record.update(status=status, finished_at=now(), result=result, error=error)
            write_json(self.manifest, state)
            return record


def active_experiment():
    return Experiment(read_json(CACHE / "active-experiment.json")["run_id"])


def manual_learning_experiment(dataset_path):
    """Start once, on the user's model command; never reset the collection experiment."""
    specification_path = ROOT / "data-manifests" / "training-v1.1.json"
    spec = read_json(specification_path)
    dataset_path = Path(dataset_path).resolve()
    if (spec.get("protocol") != "v1.1" or read_json(dataset_path).get("protocol") != "v1.1"
            or sha256(dataset_path) != spec["dataset_sha256"]):
        raise ValueError("Manual learning dataset differs from the prepared v1.1 lock")
    pointer = CACHE / "manual-learning-v1.1.json"
    with batch_lock(CACHE / "manual-learning-init.lock", wait_seconds=30):
        if pointer.exists():
            experiment = Experiment(read_json(pointer)["run_id"])
            state = read_json(experiment.manifest)
            if state.get("mode") != "manual_learning_v1.1" or state.get("specification_sha256") != sha256(specification_path):
                raise ValueError("Existing manual study has a different policy; do not reset it")
            return experiment
        original = run_path(spec["source_experiment_run_id"])
        if set(spec["model_metadata_sha256"]) != {"diagnoser-model.json", "diagnoser-file-sha256.json"}:
            raise ValueError("Prepared model provenance inventory incomplete")
        for name, expected in spec["model_metadata_sha256"].items():
            if name not in {"diagnoser-model.json", "diagnoser-file-sha256.json"} or sha256(original / name) != expected:
                raise ValueError("Prepared model provenance changed")
        folder = new_run("manual-study")
        limits = {"training_each": 7200, "training_M2": 7200, "training_M5": 7200, "evaluation": 7200}
        write_json(folder / "manifest.json", {"kind": "dataset_sft_experiment", "run_id": folder.name,
            "created_at": now(), "status": "running", "mode": "manual_learning_v1.1", "deadline": None,
            "specification_sha256": sha256(specification_path), "dataset_sha256": sha256(dataset_path),
            "stage_limits_seconds": limits, "stage_budget_modes": {k: "operation_union" for k in limits},
            "request_limits": {"generator_7b": 0, "diagnoser_3b_inference": 1500}, "operations": {},
            "qualification": "User starts models manually; no calendar cutoff, cumulative per-stage/request/storage caps retained. Original 24h collection experiment unchanged."})
        for name in ("diagnoser-model.json", "diagnoser-file-sha256.json"):
            (folder / name).write_bytes((original / name).read_bytes())
        write_json(pointer, {"run_id": folder.name})
        return Experiment(folder.name)
