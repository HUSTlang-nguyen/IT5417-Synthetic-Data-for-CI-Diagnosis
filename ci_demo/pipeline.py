"""Evidence-preserving stages. Failures stay visible and do not become labels."""
from __future__ import annotations
import difflib
import json
from pathlib import Path
import platform
import shutil
import urllib.error
from . import ollama, runner, sources
from .common import (CACHE, ROOT, case_config, command, new_run, now, read_json,
                     require_success, run_path, sha256, successful, write_json)

PROMPT = """You are generating a controlled synthetic CI regression on a real repository.
Return exactly the specified JSON object. Change ONLY properr/__init__.py.
Return the COMPLETE replacement content, not a diff or markdown.
Introduce ONE plausible Python wrapper/export regression affecting nominal or stddev behavior.
Keep imports and the public API present. Prefer a small behavior change over removing a symbol.
Do not change tests, Rust, dependencies, CI or any other file.
Do not insert explanations/comments identifying the bug into source code.
proposed_label and explanation are proposals only; execution and a human review decide validity.
The source is a passing seed, not evidence that this synthetic error occurred in historical CI.

ORIGINAL PYTHON FILE:
{source}

IMMUTABLE EXISTING TESTS:
{tests}
"""

def image_identity(case, evidence):
    result = runner.inspect_image(case, evidence)
    require_success(result, "Docker image unavailable")
    info = read_json(evidence / result["stdout"])[0]
    labels = info.get("Config", {}).get("Labels") or {}
    for name in ("base", "head"):
        if labels.get("it5417." + name) != case[name]:
            raise RuntimeError("Image source label mismatch")
    return {"id": info["Id"], "labels": labels,
            "repo_digests": info.get("RepoDigests", [])}

def doctor(endpoint, target_gpu="RTX 4070 SUPER"):
    folder = new_run("doctor")
    checks = {}
    checks["python"] = {"version": platform.python_version(), "platform": platform.platform()}
    for key, args in {
        "docker": ["docker", "version", "--format", "{{json .}}"],
        "git": ["git", "--version"],
        "gpu": ["nvidia-smi", "--query-gpu=name,memory.total,memory.free,driver_version", "--format=csv,noheader"],
    }.items():
        checks[key] = command(args, folder, key, timeout=30)
    gpu_text = (folder / checks["gpu"]["stdout"]).read_text(encoding="utf-8")
    target_matches = target_gpu.casefold() in gpu_text.casefold()
    try:
        docker_info = read_json(folder / checks["docker"]["stdout"])
        checks["docker"]["server_os"] = docker_info.get("Server", {}).get("Os")
    except (ValueError, AttributeError):
        checks["docker"]["server_os"] = None
    try:
        checks["ollama"] = {
            "ok": True, "version": json.loads(ollama.request(endpoint, "/api/version", timeout=5)),
            "models": json.loads(ollama.request(endpoint, "/api/tags", timeout=5)),
        }
    except (OSError, ValueError) as exc:
        checks["ollama"] = {"ok": False, "error": str(exc)}
    manifest = {"schema_version": 1, "kind": "doctor", "run_id": folder.name,
                "created_at": now(), "status": "doctor_finished", "target_gpu": target_gpu,
                "target_gpu_matches": target_matches, "checks": checks}
    write_json(folder / "manifest.json", manifest)
    return manifest

def reproduce(case_id="properr-6"):
    case = case_config(case_id)
    if case.get("runner_kind") == "python-source-v2":
        from .multicase import reproduce_case
        return reproduce_case(case)
    folder = new_run("reproduce")
    manifest = {"schema_version": 1, "kind": "historical_reproduction",
                "run_id": folder.name, "created_at": now(), "source": case,
                "status": "running",
                "qualification": "Local reconstruction, not the original historical GitHub CI logs."}
    write_json(folder / "manifest.json", manifest)
    try:
        locations, context = sources.prepare(case, folder)
        manifest["build"] = runner.build_image(case, context, folder)
        require_success(manifest["build"], "Docker build failed")
        manifest["image"] = image_identity(case, folder)
        manifest["base"] = runner.execute(case, folder, "historical-base", role="base")
        manifest["head"] = runner.execute(case, folder, "historical-head", role="head")
        stderr = (folder / manifest["base"]["stderr"]).read_text(encoding="utf-8")
        missing_pytest = (manifest["base"]["exit_code"] == 1
                          and not manifest["base"]["timed_out"]
                          and "No module named pytest" in stderr)
        confirmed = missing_pytest and successful(manifest["head"])
        manifest["status"] = "hypothesis_supported_locally" if confirmed else "hypothesis_not_confirmed"
        manifest["head_passed"] = successful(manifest["head"])
        if manifest["head_passed"]:
            allowed = locations["head"] / case["allowed_file"]
            tests = locations["head"] / case["test_file"]
            gate = {"case_id": case_id, "source_commit": case["head"],
                    "source_hash": sha256(allowed), "test_hash": sha256(tests),
                    "image_id": manifest["image"]["id"], "reproduction_run": folder.name,
                    "head_passed": True, "created_at": now()}
            write_json(CACHE / "passing-seed.json", gate)
    except (OSError, RuntimeError, ValueError) as exc:
        manifest["status"], manifest["error"] = "environment_error", str(exc)
    finally:
        manifest["finished_at"] = now()
        write_json(folder / "manifest.json", manifest)
    return manifest

def passing_seed(case):
    gate_file = CACHE / "passing-seed.json"
    if not gate_file.is_file():
        raise RuntimeError("No passing seed. Run reproduce successfully first.")
    gate = read_json(gate_file)
    if not gate.get("head_passed") or gate.get("source_commit") != case["head"]:
        raise RuntimeError("Seed provenance does not match the case")
    source_dir = CACHE / "exports" / case["head"]
    if sha256(source_dir / case["allowed_file"]) != gate["source_hash"]:
        raise RuntimeError("Passing source was modified")
    if sha256(source_dir / case["test_file"]) != gate["test_hash"]:
        raise RuntimeError("Immutable test was modified")
    return gate, source_dir

def validate_proposal(proposal, original, allowed="properr/__init__.py"):
    if not isinstance(proposal, dict) or set(proposal) != set(ollama.SCHEMA["required"]):
        raise ValueError("Unexpected or missing response fields")
    if proposal["path"] != allowed:
        raise ValueError("File outside allowlist")
    if not all(isinstance(proposal[key], str) for key in ollama.SCHEMA["required"]):
        raise ValueError("All response fields must be strings")
    if proposal["proposed_label"] not in {"logic", "import", "syntax", "other"}:
        raise ValueError("Unknown proposed label")
    content = proposal["content"]
    if not content.strip() or len(content.encode("utf-8")) > 32_768:
        raise ValueError("Empty or excessive replacement content")
    if content == original:
        raise ValueError("Unchanged source")
    if "\x00" in content or content.lstrip().startswith("```"):
        raise ValueError("Invalid source envelope")
    return content

def generate_run(model, attempts, endpoint, case_id="properr-6"):
    if model != ollama.GENERATOR_MODEL:
        raise ValueError("Generation requires the configured 7B generator.")
    if attempts != 3:
        raise ValueError("The generator protocol fixes three attempts.")
    case = case_config(case_id)
    if case.get("runner_kind") == "python-source-v2":
        from .multicase import generate_case
        return generate_case(case, endpoint)
    gate, source_dir = passing_seed(case)
    folder = new_run("generate")
    source = (source_dir / case["allowed_file"]).read_text(encoding="utf-8")
    tests = (source_dir / case["test_file"]).read_text(encoding="utf-8")
    prompt = PROMPT.format(source=source, tests=tests)
    (folder / "prompt.txt").write_text(prompt, encoding="utf-8")
    shutil.copy2(source_dir / case["allowed_file"], folder / "original.py")
    shutil.copy2(source_dir / case["test_file"], folder / "tests.py")
    manifest = {
        "schema_version": 1, "kind": "synthetic_generation", "run_id": folder.name,
        "created_at": now(), "source": case, "passing_seed": gate, "model": model,
        "endpoint": ollama.endpoint_url(endpoint), "options": ollama.OPTIONS,
        "attempt_count": attempts, "attempts": [], "status": "running",
        "human_review": "pending", "origin": "controlled_synthetic_not_historical",
    }
    write_json(folder / "manifest.json", manifest)
    try:
        manifest["image"] = image_identity(case, folder)
        if manifest["image"]["id"] != gate["image_id"]:
            raise RuntimeError("Image changed since passing-seed verification; reproduce again.")
        manifest["preflight"] = runner.execute(case, folder, "generation-preflight")
        require_success(manifest["preflight"], "Seed no longer passes")
        manifest["model_info"] = ollama.model_info(endpoint, model)
        manifest["runtime_version"] = json.loads(ollama.request(endpoint, "/api/version", timeout=10))
        for index in range(attempts):
            attempt_dir = folder / ("attempt-" + str(index + 1).zfill(2))
            attempt_dir.mkdir()
            item = {"index": index + 1, "directory": attempt_dir.name,
                    "status": "generation_error", "human_review": "pending"}
            payload = {"model": model, "options": {**ollama.OPTIONS, "seed": ollama.OPTIONS["seed"] + index},
                       "format": ollama.SCHEMA, "messages": [{"role": "user", "content": prompt}],
                       "stream": False, "keep_alive": 0}
            write_json(attempt_dir / "request.json", payload)
            try:
                _, raw, elapsed = ollama.generate(endpoint, model, prompt, index)
                item["generation_seconds"] = elapsed
                (attempt_dir / "response.raw.json").write_text(raw, encoding="utf-8")
                response = json.loads(raw)
                write_json(attempt_dir / "response.json", response)
                if not isinstance(response, dict):
                    raise ValueError("Ollama response must be a JSON object")
                item["runtime_metrics"] = {key: response.get(key) for key in (
                    "total_duration", "load_duration", "prompt_eval_count", "eval_count", "eval_duration")}
                if not response.get("done") or response.get("done_reason") == "length":
                    raise ValueError("Incomplete or truncated model output")
                proposal = json.loads(response["message"]["content"])
                content = validate_proposal(proposal, source, case["allowed_file"])
                write_json(attempt_dir / "proposal.json", proposal)
                (attempt_dir / "candidate.py").write_text(content, encoding="utf-8", newline="\n")
                patch = "".join(difflib.unified_diff(
                    source.splitlines(keepends=True), content.splitlines(keepends=True),
                    fromfile="a/" + case["allowed_file"], tofile="b/" + case["allowed_file"]))
                (attempt_dir / "change.diff").write_text(patch, encoding="utf-8")
                item.update(status="awaiting_verification", candidate_sha256=sha256(attempt_dir / "candidate.py"),
                            proposed_label=proposal["proposed_label"])
            except (OSError, ValueError, KeyError, TypeError) as exc:
                item["error"] = str(exc)
                if isinstance(exc, (ValueError, KeyError, TypeError)):
                    item["status"] = "invalid_output"
            manifest["attempts"].append(item)
            write_json(folder / "manifest.json", manifest)
            print("attempt", index + 1, item["status"], flush=True)
        manifest["status"] = "generation_finished"
    except (OSError, RuntimeError, ValueError) as exc:
        manifest["status"], manifest["error"] = "environment_error", str(exc)
    finally:
        manifest["finished_at"] = now()
        write_json(folder / "manifest.json", manifest)
    return manifest

def verify_run(run_id):
    folder = run_path(run_id)
    manifest = read_json(folder / "manifest.json")
    if manifest.get("source", {}).get("runner_kind") == "python-source-v2":
        from .multicase import verify_case
        return verify_case(run_id)
    if manifest["kind"] != "synthetic_generation":
        raise ValueError("verify requires a synthetic generation run.")
    if manifest.get("model") != ollama.GENERATOR_MODEL:
        raise ValueError("verify requires a run from the configured 7B generator.")
    if manifest.get("verified_at"):
        raise ValueError("Run already verified; create a new run instead of overwriting evidence.")
    case = manifest["source"]
    try:
        image = image_identity(case, folder)
        if image["id"] != manifest["passing_seed"]["image_id"]:
            raise RuntimeError("Image changed; refusing verification.")
        if sha256(folder / "original.py") != manifest["passing_seed"]["source_hash"]:
            raise RuntimeError("Original source snapshot changed")
        if sha256(folder / "tests.py") != manifest["passing_seed"]["test_hash"]:
            raise RuntimeError("Original test snapshot changed")
        for item in manifest["attempts"]:
            if item["status"] != "awaiting_verification": continue
            evidence = folder / item["directory"]
            candidate = evidence / "candidate.py"
            if sha256(candidate) != item["candidate_sha256"]:
                item.update(status="invalid_output", error="Candidate modified after generation")
                continue
            item["baseline"] = runner.execute(case, evidence, "baseline")
            item["repetitions"] = []
            if successful(item["baseline"]):
                item["repetitions"] = [runner.execute(case, evidence, "candidate-" + str(i+1), candidate=candidate)
                                       for i in range(3)]
            item["restored"] = runner.execute(case, evidence, "restored")
            is_accepted = runner.accepted(item["baseline"], item["repetitions"], item["restored"], evidence)
            item["status"] = "execution_verified" if is_accepted else "verification_failed"
            if not is_accepted:
                item["rejection_reason"] = runner.rejection_reason(item["baseline"], item["repetitions"], item["restored"], evidence)
            item["label_status"] = "pending_human_review"
            write_json(evidence / "review.json", {
                "status": "pending", "reviewer": None, "evidence": [],
                "confirmed_label": None, "confirmed_locations": [],
                "note": "Execution acceptance is not gold-label confirmation or training approval.",
            })
            write_json(folder / "manifest.json", manifest)
            print("attempt", item["index"], item["status"], flush=True)
        manifest["status"], manifest["verified_at"] = "verification_finished", now()
    except (OSError, RuntimeError, ValueError) as exc:
        manifest["status"], manifest["error"] = "environment_error", str(exc)
    write_json(folder / "manifest.json", manifest)
    return manifest
