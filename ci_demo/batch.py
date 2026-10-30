"""Bounded serial experiment scheduler; checkpoint before every side effect."""
from __future__ import annotations
from collections import Counter
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
import hashlib
import json
import os
import math
import shutil
import time
from . import multicase
from .common import CACHE, ROOT, case_config, new_run, now, read_json, run_path, sha256, write_json


class BudgetStop(RuntimeError):
    pass


def initial_budget_charge(plan):
    value = plan.get("initial_budget_charge_seconds", plan.get("discovery_seconds", 0))
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 21600:
        raise ValueError("Initial budget charge must be finite and within the fixed six-hour limit")
    return value


@contextmanager
def batch_lock(path):
    """An OS lock releases on process death; never clear a live owner's lock."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+b")
    if path.stat().st_size == 0: handle.write(b"0"); handle.flush()
    handle.seek(0)
    try:
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as exc:
        handle.close()
        raise RuntimeError("Batch is already running in another process") from exc
    try:
        yield
    finally:
        handle.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_UN)
        handle.close()


def select_cases(records):
    """Source-balanced deterministic selection; rejected rows remain in registry."""
    pools = {s: sorted((r for r in records if r["source_kind"] == s and r.get("eligible")),
                       key=lambda r: (r["environment_cost"], r["changed_file_count"], r["case_id"]))
             for s in ("aidev", "swebench")}
    counts = Counter(); selected = []
    for _ in range(5):
        for source in ("aidev", "swebench"):
            candidate = next((x for x in pools[source] if counts[x["repo_url"]] < 4), None)
            if candidate:
                pools[source].remove(candidate); counts[candidate["repo_url"]] += 1; selected.append(candidate["case_id"])
    return selected


def summarize(manifest):
    output = {"screened": len(manifest["screening"]), "selected": len(manifest["cases"]),
              "requested_generation_attempts": 3 * len(manifest["cases"]), "generation_capacity": 30,
              "reproduction_attempted": 0, "historical_supported": 0, "passing_seeds": 0,
              "generation_attempted": 0, "execution_verified": 0, "by_source": {}, "by_repo": {}}
    output["generation_unknown"] = 0
    for item in manifest["cases"]:
        metrics = {k: 0 for k in ("selected", "reproduction_attempted", "historical_supported", "passing_seeds", "generation_attempted", "execution_verified")}
        metrics["selected"] = 1
        for name in ("reproduce", "generate", "verify"):
            record = item["stages"].get(name)
            if not record: continue
            if name == "reproduce": metrics["reproduction_attempted"] = 1
            path = run_path(record["run_id"]) / "manifest.json"
            raw = read_json(path)
            if name == "reproduce":
                metrics["historical_supported"] = int(raw.get("historical_supported", False))
                metrics["passing_seeds"] = int(raw.get("head_passed", False))
            elif name == "generate":
                metrics["generation_attempted"] = len(raw.get("attempts", []))
                output["generation_unknown"] += sum(a["status"] == "generation_in_progress" for a in raw.get("attempts", []))
            elif name == "verify": metrics["execution_verified"] = sum(x["status"] == "execution_verified" for x in raw.get("attempts", []))
        for key, value in metrics.items():
            if key != "selected": output[key] += value
        for field, group in (("by_source", item["source_kind"]), ("by_repo", item["repo_url"])):
            totals = output[field].setdefault(group, {k: 0 for k in metrics})
            for k, v in metrics.items(): totals[k] += v
    output["generation_unexecuted"] = output["requested_generation_attempts"] - output["generation_attempted"]
    return output


def run_batch(manifest_path=None, resume=None, endpoint="http://127.0.0.1:11434"):
    if bool(manifest_path) == bool(resume): raise ValueError("Choose a manifest or a resume ID")
    key = resume if resume else hashlib.sha256(str(Path(manifest_path).resolve()).encode()).hexdigest()
    if resume: run_path(resume)  # validate identifier before constructing lock path
    with batch_lock(CACHE / "batch-locks" / (key + ".lock")):
        return _run_batch(manifest_path, resume, endpoint)


def _run_batch(manifest_path=None, resume=None, endpoint="http://127.0.0.1:11434"):
    if bool(manifest_path) == bool(resume): raise ValueError("Choose a manifest or a resume ID")
    if resume:
        folder = run_path(resume); manifest = read_json(folder / "manifest.json")
        if manifest["kind"] != "development_batch": raise ValueError("Not a batch run")
        if manifest["status"] == "batch_finished": return manifest
    else:
        plan = read_json(Path(manifest_path))
        records = plan["screening"]
        if len(records) != 20 or Counter(x["source_kind"] for x in records) != {"aidev": 10, "swebench": 10}:
            raise ValueError("Batch requires exactly ten screened records per source")
        if plan.get("split") != "development": raise ValueError("Batch may use development records only")
        cases = [case_config(x) for x in select_cases(records)]
        folder = new_run("batch")
        manifest = {"schema_version": 2, "kind": "development_batch", "run_id": folder.name,
                    "created_at": now(), "status": "running", "plan_sha256": sha256(Path(manifest_path)),
                    "screening": records, "budget_seconds": 21600,
                    "active_seconds": initial_budget_charge(plan),
                    "inherited_budget_seconds": plan.get("initial_budget_charge_seconds", 0),
                    "cohort_kind": plan.get("cohort_kind", "new_source_cases"), "parent_batch": plan.get("parent_batch"),
                    "unaccounted_time_bound_seconds": 0,
                    "minimum_free_bytes": 20 * 2**30, "human_review": "pending", "split": "development",
                    "cases": [{"case_id": c["case_id"], "source_case_id": c.get("source_case_id", c["case_id"]),
                               "source_kind": c["source_kind"], "repo_url": c["repo_url"],
                               "config_sha256": hashlib.sha256(json.dumps(c, sort_keys=True).encode()).hexdigest(),
                               "stages": {}, "status": "pending"} for c in cases]}
        write_json(folder / "plan.json", plan)
    # Never reissue an operation whose result is unknown after interruption.
    for item in manifest["cases"]:
        for name, stage in item["stages"].items():
            if stage["status"] != "running": continue
            path = run_path(stage["run_id"]) / "manifest.json"
            saved = read_json(path)
            if saved.get("finished_at"):
                stage["status"] = "done"
            else:
                stage["status"] = "interrupted_unknown"; item["status"] = "interrupted_unknown"
                event_id = "interruption-" + __import__("uuid").uuid4().hex
                event = {"event_id": event_id, "recorded_at": now(), "case_id": item["case_id"],
                         "previous_run": stage["run_id"], "stage": name, "status": "interrupted_unknown",
                         "action": "preserved_previous_artifacts_no_retry"}
                write_json(folder / "resume-events" / (event_id + ".json"), event)
                stage["interruption_event"] = "resume-events/" + event_id + ".json"
                # Bound missing time, explicitly separate it from measured runtime.
                manifest["unaccounted_time_bound_seconds"] += stage.get("max_unaccounted_seconds", 1200)
    base_seconds = manifest["active_seconds"]; start = time.monotonic()

    def checkpoint():
        manifest["active_seconds"] = round(base_seconds + time.monotonic() - start, 3)
        manifest["updated_at"] = now()
        write_json(folder / "manifest.json", manifest)

    current_stage = None

    def guard(operation):
        checkpoint()
        if manifest["active_seconds"] + manifest["unaccounted_time_bound_seconds"] >= manifest["budget_seconds"]:
            raise BudgetStop("six_hour_budget_exhausted")
        if shutil.disk_usage(folder).free < manifest["minimum_free_bytes"]:
            raise BudgetStop("artifact_volume_below_20_GiB")
        if current_stage is not None:
            current_stage.update(operation=operation, operation_started_at=now(),
                                 max_unaccounted_seconds=1200 if operation == "docker-build" else 300)
        checkpoint()

    manifest["status"] = "running"; checkpoint()
    try:
        for item in manifest["cases"]:
            if item["status"] in ("finished", "failed", "interrupted_unknown"): continue
            case = case_config(item["case_id"])
            actual = hashlib.sha256(json.dumps(case, sort_keys=True).encode()).hexdigest()
            if actual != item["config_sha256"]: raise ValueError("Case changed since batch creation")
            for name in ("reproduce", "generate", "verify"):
                if name in item["stages"]: continue
                guard("start-" + name)
                stage_folder = new_run(name)
                current_stage = {"run_id": stage_folder.name, "status": "running", "started_at": now()}
                item["stages"][name] = current_stage
                # A manifest exists before any source/network/model side effect.
                write_json(stage_folder / "manifest.json", {"run_id": stage_folder.name, "kind": "reserved_stage",
                           "status": "reserved", "created_at": now(), "source": case})
                checkpoint(); print("batch", item["case_id"], name, stage_folder.name, flush=True)
                if name == "reproduce": result = multicase.reproduce_case(case, stage_folder, guard)
                elif name == "generate": result = multicase.generate_case(case, endpoint, stage_folder, item["stages"]["reproduce"]["run_id"], guard)
                else: result = multicase.verify_case(item["stages"]["generate"]["run_id"], stage_folder, guard)
                from .report import report_run
                report_run(stage_folder.name)
                current_stage["status"] = "done"; current_stage["finished_at"] = now(); current_stage = None
                if result.get("error"):
                    item.update(status="failed", error=result["error"]); checkpoint(); break
                if name == "reproduce" and not result.get("head_passed"):
                    item.update(status="failed", error="fixed_tests_do_not_pass"); checkpoint(); break
                checkpoint()
            else: item["status"] = "finished"
            checkpoint()
        manifest["status"] = "batch_finished"
    except BudgetStop as exc:
        manifest.update(status="batch_stopped", stop_reason=str(exc))
    except (OSError, ValueError, RuntimeError, KeyError) as exc:
        manifest.update(status="batch_incomplete", error=str(exc))
    manifest["summary"] = summarize(manifest)
    manifest["finished_at"] = now(); checkpoint()
    from .report import report_run
    report_run(folder.name)
    return manifest
