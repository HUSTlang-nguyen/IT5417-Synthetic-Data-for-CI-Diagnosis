"""Bounded 7B generation/verification from current train seeds; no model-call replay."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import os
from pathlib import Path
import subprocess

from . import multicase, ollama
from .batch import BudgetStop, batch_lock
from .common import CACHE, ROOT, case_config, new_run, now, read_json, run_path, sha256, write_json
from .dataset_experiment import freeze_plan
from .experiment import active_experiment


@contextmanager
def gpu_trace(folder):
    output = folder / "whole-gpu-memory.csv"
    process = None
    with output.open("w", encoding="utf-8") as stream, (folder / "gpu-monitor.stderr.txt").open("w", encoding="utf-8") as errors:
        try:
            process = subprocess.Popen(["nvidia-smi", "--query-gpu=timestamp,memory.used", "--format=csv,noheader,nounits", "--loop-ms=250"],
                stdout=stream, stderr=errors, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        except OSError as exc:
            errors.write(str(exc))
        try:
            yield
        finally:
            if process is not None and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)


def request_count(experiment):
    return sum(r.get("request_role") == "generator_7b" for r in read_json(experiment.manifest).get("operations", {}).values())


def generate_one(experiment, case, endpoint, batch):
    identity = case["source_case_id"]
    operation = "synthetic-generate-" + identity
    previous = read_json(experiment.manifest).get("operations", {}).get(operation)
    if previous:
        if previous["status"] != "finished":
            return {"source_case_id": identity, "status": "prior_generation_not_reissued", "operation": operation}
        generated = run_path(previous["result"]["run_id"])
        if sha256(generated / "manifest.json") != previous["result"]["manifest_sha256"]:
            raise ValueError("Saved generation manifest changed")
    else:
        if read_json(experiment.manifest)["request_limits"]["generator_7b"] - request_count(experiment) < 3:
            raise BudgetStop("Insufficient request budget for a fresh three-attempt seed")
        experiment.reserve(operation, "synthetic", timeout=300)
        generated = new_run("generate")
        experiment.attach(operation, run_id=generated.name, case_id=case["case_id"], source_case_id=identity, batch=batch.name)
        active = None
        uncertain = None

        def close_request():
            nonlocal active, uncertain
            if active is None:
                return
            name, directory = active
            response = directory / "response.raw.json"
            if response.is_file():
                experiment.finish(name, "finished", result={"artifact": str(response.relative_to(ROOT)), "sha256": sha256(response)})
            else:
                uncertain = "Model call lacks a saved response; inspect before further generation: " + name
                experiment.finish(name, "unknown", result={"artifact": str(directory.relative_to(ROOT))}, error=uncertain)
            active = None
            if uncertain:
                raise RuntimeError(uncertain)

        def guard(name):
            nonlocal active
            if name.startswith("model-attempt-"):
                close_request()
                index = int(name.rsplit("-", 1)[-1])
                request = "generator-" + generated.name + "-" + str(index)
                experiment.reserve(request, "synthetic", request_role="generator_7b", timeout=180)
                directory = generated / ("attempt-" + str(index).zfill(2))
                experiment.attach(request, artifact=str(directory.relative_to(ROOT)), source_case_id=identity)
                active = request, directory
            else:
                experiment.check("synthetic", timeout=300)

        seed = read_json(CACHE / "passing-seeds" / (case["case_id"] + ".json"))
        raw = multicase.generate_case(case, endpoint, folder=generated, reproduction_run=seed["reproduction_run"], guard=guard)
        try:
            close_request()
        except RuntimeError:
            pass
        successful = raw["status"] == "generation_finished" and uncertain is None
        experiment.finish(operation, "finished" if successful else "failed", result={"run_id": generated.name,
            "manifest_sha256": sha256(generated / "manifest.json"), "status": raw["status"]}, error=uncertain or raw.get("error"))
        if uncertain:
            raise RuntimeError(uncertain)
        if not successful:
            return {"source_case_id": identity, "generation_run": generated.name, "status": raw["status"], "error": raw.get("error")}
    operation = "synthetic-verify-" + identity
    previous = read_json(experiment.manifest).get("operations", {}).get(operation)
    if previous:
        if previous["status"] != "finished":
            return {"source_case_id": identity, "generation_run": generated.name, "status": "prior_verification_not_reissued"}
        verified = run_path(previous["result"]["run_id"])
        if sha256(verified / "manifest.json") != previous["result"]["manifest_sha256"]:
            raise ValueError("Saved verification manifest changed")
        result = read_json(verified / "manifest.json")
    else:
        experiment.reserve(operation, "synthetic", timeout=300)
        verified = new_run("verify")
        experiment.attach(operation, run_id=verified.name, generation_run=generated.name, source_case_id=identity, batch=batch.name)
        result = multicase.verify_case(generated.name, folder=verified, guard=lambda name: experiment.check("synthetic", timeout=300))
        experiment.finish(operation, "finished" if result["status"] == "verification_finished" else "failed",
            result={"run_id": verified.name, "manifest_sha256": sha256(verified / "manifest.json"), "status": result["status"]}, error=result.get("error"))
    return {"source_case_id": identity, "generation_run": generated.name, "verification_run": verified.name,
            "status": result["status"], "attempt_count": 3,
            "execution_verified": sum(a["status"] == "execution_verified" for a in result.get("attempts", []))}


def run_batch(plan_path, *, limit, endpoint="http://127.0.0.1:11434"):
    if limit < 1:
        raise ValueError("Limit must be positive")
    endpoint = ollama.endpoint_url(endpoint)
    experiment = active_experiment()
    with batch_lock(experiment.folder / "reproduction-worker.lock"), batch_lock(CACHE / "model-execution.lock"):
        with batch_lock(experiment.lock, wait_seconds=30):
            plan = freeze_plan(experiment, Path(plan_path))
        state = read_json(experiment.manifest)
        if any(r["stage"] == "synthetic" and r["status"] in {"reserved", "unknown"} for r in state.get("operations", {}).values()):
            raise RuntimeError("Uncertain prior synthetic operation; inspect its artifacts before any new model call")
        eligible = []
        for row in plan["selected"]:
            if row["role"] != "train":
                continue
            case = case_config(row["case_id"])
            if (CACHE / "passing-seeds" / (case["case_id"] + ".json")).is_file():
                eligible.append(case)
        batch = new_run("synthetic-batch")
        manifest = {"kind": "synthetic_collection", "run_id": batch.name, "created_at": now(), "status": "running",
            "source_plan_sha256": sha256(plan_path), "eligible_train_seeds": len(eligible), "new_case_limit": limit,
            "model": ollama.GENERATOR_MODEL, "prompt_revision": multicase.SITE_PROMPT_REVISION,
            "request_caps": state["request_limits"], "deadline": state["deadline"],
            "cases": [], "attempts_per_seed": 3, "calls_before": request_count(experiment), "review": "pending_silver_curation_not_gold"}
        write_json(batch / "manifest.json", manifest)
        count = 0
        try:
            manifest["model_info"] = ollama.model_info(endpoint, ollama.GENERATOR_MODEL)
            with gpu_trace(batch):
                for case in eligible:
                    prior = read_json(experiment.manifest).get("operations", {}).get("synthetic-verify-" + case["source_case_id"])
                    if prior is not None:
                        continue
                    if count >= limit:
                        break
                    experiment.check("synthetic", timeout=300)
                    manifest["current_source_case_id"] = case["source_case_id"]
                    entry = {"source_case_id": case["source_case_id"], "case_id": case["case_id"], "status": "running", "attempt_count": 3}
                    manifest["cases"].append(entry)
                    write_json(batch / "manifest.json", manifest)
                    result = generate_one(experiment, case, endpoint, batch)
                    entry.update(result)
                    count += 1
                    manifest["calls_after"] = request_count(experiment)
                    write_json(batch / "manifest.json", manifest)
                    print(case["source_case_id"], result["status"], result.get("execution_verified", 0), flush=True)
            manifest["status"] = "collection_finished"
        except (OSError, RuntimeError, ValueError, KeyError) as exc:
            manifest.update(status="collection_stopped", error=str(exc))
            for entry in manifest["cases"]:
                if entry["status"] == "running":
                    entry.update(status="stage_stopped", error=str(exc))
        values = []
        gpu_csv = batch / "whole-gpu-memory.csv"
        for line in gpu_csv.read_text(encoding="utf-8").splitlines() if gpu_csv.exists() else []:
            try:
                values.append(int(line.rsplit(",", 1)[-1].strip()))
            except ValueError:
                pass
        write_json(batch / "gpu-memory-summary.json", {"samples": len(values), "peak_whole_gpu_mib": max(values) if values else None,
            "qualification": "Sampled entire GPU including background allocations; not model-exclusive CUDA memory"})
        manifest.update(finished_at=now(), calls_after=request_count(experiment))
        manifest["new_model_calls"] = manifest["calls_after"] - manifest["calls_before"]
        write_json(batch / "manifest.json", manifest)
        return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", default="data-manifests/dataset-v1-plan-env-ready.json")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    print(run_batch(ROOT / args.plan, limit=args.limit), flush=True)


if __name__ == "__main__":
    main()
