"""Run immutable repo tests in fresh constrained containers."""
from __future__ import annotations
import uuid
import tempfile
import shutil
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from .common import command, successful, write_json

def build_image(case, context, evidence):
    args = [
        "docker", "build", "--label", "it5417.base=" + case["base"],
        "--label", "it5417.head=" + case["head"],
        "--label", "it5417.runner=v1", "-t", case["image"], context,
    ]
    return command(args, evidence, "docker-build", timeout=1200)

def inspect_image(case, evidence):
    return command(["docker", "image", "inspect", case["image"]],
                   evidence, "image-inspect", timeout=30)

def execute(case, evidence, name, role="head", candidate=None, timeout=90):
    container = "it5417-" + uuid.uuid4().hex[:16]
    args = [
        "docker", "run", "--name", container, "--network=none",
        "--read-only", "--user", "65534:65534", "--cap-drop=ALL",
        "--security-opt=no-new-privileges", "--pids-limit=128",
        "--memory=512m", "--cpus=1", "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
    ]
    if candidate is not None:
        path = str(candidate.resolve())
        if "," in path: raise ValueError("Candidate mount path cannot contain commas")
        args += ["--mount", "type=bind,src=" + path +
                 ",dst=/opt/head/lib/python3.11/site-packages/properr/__init__.py,readonly"]
    if role not in {"base", "head"}: raise ValueError("Unknown role")
    evidence.mkdir(parents=True, exist_ok=True)
    # A stopped container loses tmpfs contents. Mount only a fresh output directory,
    # never the run directory containing manifests, tests or other evidence.
    with tempfile.TemporaryDirectory(prefix="junit-", dir=evidence) as temporary:
        output = Path(temporary).resolve()
        if "," in str(output): raise ValueError("Evidence mount path cannot contain commas")
        output.chmod(0o777)
        args += ["--mount", "type=bind,src=" + str(output) + ",dst=/results",
                 case["image"], "/opt/" + role + "/bin/python", "-m", "pytest",
                 "-v", "-p", "no:cacheprovider", "/source/" + role + "/tests",
                 "--junitxml=/results/results.xml"]
        try:
            result = command(args, evidence, name, timeout=timeout)
        finally:
            # docker CLI timeout does not itself stop the daemon-side container.
            cleanup = command(["docker", "rm", "-f", container], evidence, name + "-cleanup", timeout=20)
        junit = output / "results.xml"
        if (successful(cleanup) and not result["timed_out"] and not junit.is_symlink()
                and junit.is_file() and junit.stat().st_size <= 2_000_000):
            destination = evidence / (name + ".junit.xml")
            shutil.copyfile(junit, destination)
            result["junit"] = destination.name
        result["container_removed"] = successful(cleanup)
    result["container"] = container
    result["role"] = role
    write_json(evidence / (name + ".json"), result)
    return result

def evidence_failure(result, evidence):
    return bool(failure_signature(result, evidence))

def failure_signature(result, evidence):
    if result["timed_out"] or result["exit_code"] not in (1, 2) or "junit" not in result:
        return []
    try:
        root = ET.parse(evidence / result["junit"]).getroot()
        failures = []
        for test in root.iter("testcase"):
            for node in list(test):
                if node.tag in {"failure", "error"}:
                    # Pytest reprs include fresh object addresses in every process.
                    # Normalize addresses only; retain assertion values and test identity.
                    message = re.sub(r" at 0x[0-9a-fA-F]+", " at <address>", node.get("message", ""))
                    failures.append((test.get("classname"), test.get("name"), node.tag, node.get("type"), message))
        return sorted(failures, key=str)
    except (OSError, ET.ParseError):
        return []

def accepted(baseline, repetitions, restored, evidence):
    signatures = [failure_signature(r, evidence) for r in repetitions]
    return (successful(baseline) and len(repetitions) == 3
            and all(signatures) and all(s == signatures[0] for s in signatures)
            and successful(restored))


def rejection_reason(baseline, repetitions, restored, evidence):
    if not successful(baseline): return "baseline_failed"
    if any(r["timed_out"] for r in repetitions): return "timeout"
    if any(r["exit_code"] not in (0, 1, 2) for r in repetitions): return "execution_error"
    if not successful(restored): return "restoration_failed"
    if len(repetitions) != 3: return "incomplete_verification"
    if any(successful(r) for r in repetitions): return "does_not_fail_consistently"
    signatures = [failure_signature(r, evidence) for r in repetitions]
    if not all(signatures): return "missing_test_failure_evidence"
    return "unstable_failure"
