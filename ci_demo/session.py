"""Checkpoint a single-generator demo without modifying the linked raw runs."""
from __future__ import annotations
from collections import Counter
from .common import now, read_json, run_path, write_json
from .ollama import DIAGNOSTIC_MODEL, GENERATOR_MODEL

TERMINAL_ATTEMPTS = {"generation_error", "invalid_output", "verification_failed", "execution_verified"}


def generation_summary(run_id=None):
    result = {"model": GENERATOR_MODEL, "role": "generator", "run_id": run_id,
              "status": "not_started", "requested": 3, "recorded_attempts": 0,
              "unexecuted": 3, "execution_verified": 0, "status_counts": {},
              "generation_seconds": None, "measured_generation_attempts": 0}
    if run_id is None:
        return result, False
    manifest = read_json(run_path(run_id) / "manifest.json")
    if manifest.get("kind") != "synthetic_generation" or manifest.get("model") != GENERATOR_MODEL:
        raise ValueError("Demo sessions require a 7B synthetic generation run.")
    attempts = manifest.get("attempts", [])
    indices = [a["index"] for a in attempts]
    if (manifest.get("attempt_count") != 3 or len(attempts) > 3
            or len(set(indices)) != len(indices) or any(i not in (1, 2, 3) for i in indices)):
        raise ValueError("The demo requires three requested attempts with unique indices 1–3.")
    measured = [a["generation_seconds"] for a in attempts if a.get("generation_seconds") is not None]
    result.update(status=manifest["status"], recorded_attempts=len(attempts), unexecuted=3 - len(attempts),
                  execution_verified=sum(a["status"] == "execution_verified" for a in attempts),
                  status_counts=dict(Counter(a["status"] for a in attempts)),
                  generation_seconds=round(sum(measured), 3) if measured else None,
                  measured_generation_attempts=len(measured), error=manifest.get("error"),
                  model_digest=manifest.get("model_info", {}).get("tag", {}).get("digest"),
                  runtime_version=manifest.get("runtime_version"))
    complete = (manifest["status"] == "verification_finished" and len(attempts) == 3
                and all(a["status"] in TERMINAL_ATTEMPTS for a in attempts) and not result["error"])
    return result, complete


def save_session(folder, *, generation_run=None, doctor_run=None, reproduction_run=None,
                 error=None, finished=False):
    existing = read_json(folder / "manifest.json") if (folder / "manifest.json").is_file() else {}
    if existing and existing.get("kind") != "generation_demo":
        raise ValueError("Refusing to overwrite a different artifact kind.")
    if existing.get("finished_at"):
        raise ValueError("Demo already finished; create a new session instead of overwriting evidence.")
    generation_run = generation_run or existing.get("generator", {}).get("run_id")
    generator, complete = generation_summary(generation_run)
    error = error or existing.get("error")
    manifest = {"schema_version": 1, "kind": "generation_demo", "run_id": folder.name,
                "created_at": existing.get("created_at", now()), "updated_at": now(),
                "status": ("demo_finished" if complete and not error else "demo_incomplete") if finished else "running",
                "generator": generator,
                "diagnoser": {"model": DIAGNOSTIC_MODEL, "role": "diagnoser", "status": "not_implemented"},
                "doctor_run": doctor_run or existing.get("doctor_run"),
                "reproduction_run": reproduction_run or existing.get("reproduction_run"),
                "human_review": "pending", "not_training_evaluation": True}
    if error:
        manifest["error"] = error
    if finished:
        manifest["finished_at"] = now()
    write_json(folder / "manifest.json", manifest)
    from .report import report_run
    report_run(folder.name)
    return manifest
