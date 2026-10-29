"""Paths, evidence and bounded subprocess execution."""
from __future__ import annotations
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import time
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache"
RUNS = ROOT / "runs"
BANGKOK = timezone(timedelta(hours=7))

def now():
    return datetime.now(BANGKOK).isoformat(timespec="seconds")

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def case_config(case="properr-6"):
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,120}", case):
        raise ValueError("Invalid case ID")
    if case == "properr-6":
        return read_json(ROOT / "cases" / case / "case.json")
    from .multicase import validate_case
    value = read_json(ROOT / "data-manifests" / "cases" / (case + ".json"))
    validate_case(value)
    if value["case_id"] != case:
        raise ValueError("Case ID mismatch")
    return value

def new_run(kind):
    RUNS.mkdir(parents=True, exist_ok=True)
    run_id = kind + "-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    folder = RUNS / run_id
    folder.mkdir()
    return folder

def run_path(run_id):
    if not run_id or Path(run_id).name != run_id or run_id in {".", ".."}:
        raise ValueError("Run must be an existing run ID, not a path.")
    folder = RUNS / run_id
    if not (folder / "manifest.json").is_file():
        raise ValueError("Run manifest not found: " + run_id)
    return folder

def command(args, folder, name, timeout=300, cwd=None):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    timed_out = False
    try:
        result = subprocess.run(
            [str(a) for a in args], cwd=cwd, capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=timeout,
            shell=False,
        )
        code, stdout, stderr = result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        code = None
        stdout = exc.stdout or b""
        stderr = exc.stderr or b""
        if isinstance(stdout, bytes): stdout = stdout.decode("utf-8", "replace")
        if isinstance(stderr, bytes): stderr = stderr.decode("utf-8", "replace")
    except OSError as exc:
        code, stdout, stderr = None, "", str(exc)
    (folder / (name + ".stdout.txt")).write_text(stdout, encoding="utf-8")
    (folder / (name + ".stderr.txt")).write_text(stderr, encoding="utf-8")
    evidence = {
        "command": [str(a) for a in args], "exit_code": code,
        "timed_out": timed_out, "duration_seconds": round(time.monotonic() - start, 3),
        "recorded_at": now(), "stdout": name + ".stdout.txt", "stderr": name + ".stderr.txt",
    }
    write_json(folder / (name + ".json"), evidence)
    return evidence

def successful(result):
    return result["exit_code"] == 0 and not result["timed_out"]

def require_success(result, context):
    if not successful(result):
        raise RuntimeError(context + ": see " + result["stderr"])
