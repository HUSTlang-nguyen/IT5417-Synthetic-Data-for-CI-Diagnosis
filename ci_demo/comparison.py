"""Summarize saved pilot evidence, including failed and unexecuted attempts."""
from __future__ import annotations
from collections import Counter
from .common import new_run, now, read_json, run_path, sha256, write_json
from .ollama import MODELS, OPTIONS


def _model_summary(model, run_id=None):
    summary = {"model": model, "requested": 3, "run_id": run_id,
               "status": "not_started", "recorded_attempts": 0, "unexecuted": 3,
               "execution_verified": 0, "status_counts": {},
               "generation_seconds": None, "measured_generation_attempts": 0}
    if run_id is None:
        return summary, None
    folder = run_path(run_id)
    manifest = read_json(folder / "manifest.json")
    if manifest.get("kind") != "synthetic_generation" or manifest.get("model") != model:
        raise ValueError("Comparison requires synthetic runs from the documented models.")
    attempts = manifest.get("attempts", [])
    indices = [item["index"] for item in attempts]
    if (manifest.get("attempt_count") != 3 or len(attempts) > 3
            or len(set(indices)) != len(indices) or any(i not in (1, 2, 3) for i in indices)):
        raise ValueError("Comparison requires three requested attempts with unique indices 1–3.")
    measured = [a["generation_seconds"] for a in attempts if a.get("generation_seconds") is not None]
    summary.update(status=manifest["status"], recorded_attempts=len(attempts),
                   unexecuted=3 - len(attempts),
                   execution_verified=sum(a["status"] == "execution_verified" for a in attempts),
                   status_counts=dict(Counter(a["status"] for a in attempts)),
                   generation_seconds=round(sum(measured), 3) if measured else None,
                   measured_generation_attempts=len(measured), error=manifest.get("error"),
                   model_digest=manifest.get("model_info", {}).get("tag", {}).get("digest"),
                   runtime_version=manifest.get("runtime_version"))
    gate = manifest.get("passing_seed", {})
    protocol = {"source": manifest.get("source"), "options": manifest.get("options"),
                "source_commit": gate.get("source_commit"), "source_hash": gate.get("source_hash"),
                "test_hash": gate.get("test_hash"), "image_id": gate.get("image_id")}
    for name in ("prompt.txt", "original.py", "tests.py"):
        path = folder / name
        protocol[name] = sha256(path) if path.is_file() else None
    summary["protocol"] = protocol
    return summary, manifest


def save_comparison(run_ids=(), *, folder=None, doctor_run=None, error=None, finished=True):
    """Checkpoint a comparison without editing any source run or its raw evidence."""
    selected = {}
    for run_id in run_ids:
        manifest = read_json(run_path(run_id) / "manifest.json")
        model = manifest.get("model")
        if model not in MODELS or model in selected or manifest.get("kind") != "synthetic_generation":
            raise ValueError("Use at most one synthetic run per documented model.")
        selected[model] = run_id
    models, manifests = [], []
    for model in MODELS:
        summary, manifest = _model_summary(model, selected.get(model))
        models.append(summary)
        if manifest is not None:
            manifests.append(manifest)
    issues = []
    present = [m for m in models if m["run_id"]]
    if len(present) != 2:
        issues.append("missing_model_run")
    for model in present:
        protocol = model["protocol"]
        if any(value is None for value in protocol.values()):
            issues.append(model["model"] + ":incomplete_protocol_evidence")
        if protocol["options"] != OPTIONS:
            issues.append(model["model"] + ":nonstandard_options")
        if protocol["original.py"] != protocol["source_hash"] or protocol["tests.py"] != protocol["test_hash"]:
            issues.append(model["model"] + ":snapshot_hash_mismatch")
    if len(present) == 2:
        for key in present[0]["protocol"]:
            if present[0]["protocol"][key] != present[1]["protocol"][key]:
                issues.append("protocol_mismatch:" + key)
    complete = (not issues and len(manifests) == 2
                and all(m["status"] == "verification_finished" and len(m["attempts"]) == 3 for m in manifests))
    folder = folder or new_run("comparison")
    existing = read_json(folder / "manifest.json") if (folder / "manifest.json").is_file() else {}
    summary = {"schema_version": 1, "kind": "pilot_comparison", "run_id": folder.name,
               "created_at": existing.get("created_at", now()), "updated_at": now(),
               "status": ("comparison_finished" if complete and not error else "comparison_incomplete") if finished else "running",
               "models": models, "protocol_compatible": not issues, "comparison_issues": issues,
               "doctor_run": doctor_run, "human_review": "pending", "not_training_evaluation": True}
    if error:
        summary["error"] = error
    write_json(folder / "manifest.json", summary)
    from .report import report_run
    report_run(folder.name)
    return summary


def compare_runs(run_ids):
    if len(run_ids) != 2:
        raise ValueError("Supply exactly two run IDs, one per model.")
    return save_comparison(run_ids)
