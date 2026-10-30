"""Construct development cohort 02 from cached pinned records; never overwrite cases."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ci_demo.common import read_json, write_json, sha256
from ci_demo.multicase import patch_paths, is_test, validate_case, SITE_PROTOCOL
from ci_demo.batch import select_cases

RAW = ROOT / ".cache/expansion-02"


def focal_line(patch, allowed):
    current = None; line_number = 1; fallback = 1
    for line in patch.splitlines():
        if line.startswith("+++ b/"): current = line[6:]
        elif line.startswith("@@"):
            match = re.search(r"\+(\d+)", line)
            if match: line_number = int(match.group(1)); fallback = line_number if current == allowed else fallback
        elif current == allowed and line.startswith("+") and not line.startswith("+++"):
            value = line[1:].strip()
            if value and not value.startswith(("#", "from ", "import ", "def ", "class ", '"""', "'''")):
                return line_number
            line_number += 1
        elif current == allowed and line.startswith(" "): line_number += 1
    return fallback


def save_case(case):
    validate_case(case)
    path = ROOT / "cases" / case["case_id"] / "case.json"
    if path.exists():
        if read_json(path) != case: raise ValueError("Refuse to rewrite an existing case: " + case["case_id"])
    else: write_json(path, case)


def main():
    records = []
    for row in read_json(RAW / "aidev-screen-input.json"):
        repo, number = row["html_url"].removeprefix("https://github.com/").split("/pull/")
        case_id = repo.replace("/", "__") + "-" + number; folder = RAW / "records" / case_id
        write_json(folder / "source-record.json", row)
        entry = {"case_id": case_id, "source_kind": "aidev", "repo_url": "https://github.com/" + repo,
                 "instance_id": str(row["id"]), "dataset": "hao-li/AIDev", "dataset_revision": "b8dc67df93e7c11f6f20c84129db7232eb1ec253",
                 "eligible": False, "environment_cost": 2, "changed_file_count": 0, "reasons": [], "split": "development",
                 "source_record_sha256": sha256(folder / "source-record.json"), "row_idx": row["row_idx"]}
        if (folder / "pr.json").exists():
            pr = read_json(folder / "pr.json"); base, head = pr["base"]["sha"], pr["head"]["sha"]
            entry["identity_source"] = "saved_GitHub_PR_API"
        elif (folder / "git-identity.json").exists():
            pr = read_json(folder / "git-identity.json"); base, head = pr["base"], pr["head"]
            entry["identity_source"] = pr["base_identity_source"] + "+" + pr["head_identity_source"]
        else:
            entry["reasons"].append("commit_metadata_unavailable_or_public_patch_ref_mismatch")
        if not (folder / "series.patch").exists(): entry["reasons"].append("public_patch_unavailable")
        if entry["reasons"]: records.append(entry); continue
        patch = (folder / "series.patch").read_text(encoding="utf-8")
        paths = patch_paths(patch); entry["changed_file_count"] = len(paths)
        product = [p for p in paths if p.endswith(".py") and not is_test(p)]
        tests = [p for p in paths if p.endswith(".py") and is_test(p)]
        if len(product) != 1: entry["reasons"].append("requires_one_production_Python_file")
        license_file = next((folder / n for n in ("LICENSE", "LICENSE.txt", "LICENSE.md") if (folder / n).exists()), None)
        if not license_file: entry["reasons"].append("license_not_verified_at_pinned_source")
        else:
            license_text = license_file.read_text(encoding="utf-8")
            license_id = "MIT" if "Permission is hereby granted" in license_text else "GPL-3.0" if "GNU GENERAL PUBLIC LICENSE" in license_text else None
            if not license_id: entry["reasons"].append("license_requires_manual_mapping")
            entry["license"] = license_id; entry["license_evidence_sha256"] = sha256(license_file)
        if case_id == "PyLabRobot__pylabrobot-528":
            tests = ["pylabrobot/resources/resource_tests.py"]
        if not tests: entry["reasons"].append("no_identified_upstream_test_target")
        if not entry["reasons"]:
            if repo == "PyLabRobot/pylabrobot":
                dependencies = ["typing_extensions==4.12.2", "requests==2.32.3", "numpy==1.26.4", "websockets==12.0", "pyserial==3.5"]
                writable = ["logs", "test_logs"]; cost = 0
            elif repo == "shillis13/python":
                dependencies = ["PyYAML==6.0.3", "colorama==0.4.6", "rich==13.9.4"]; writable = []; cost = 0
            elif repo == "fastapi/fastapi":
                dependencies = ["starlette==0.48.0", "pydantic==2.10.6", "httpx==0.28.1", "typing_extensions==4.14.1",
                                "typing-inspection==0.4.2", "annotated-doc==0.0.4", "inline-snapshot==0.23.2"]
                writable = []; cost = 1
            else:
                entry["reasons"].append("bounded_environment_recipe_not_available"); records.append(entry); continue
            frozen = tests[:]
            for p in ("conftest.py", "tests/conftest.py", "pylabrobot/conftest.py"):
                if (folder / p.replace("/", "__")).is_file(): frozen.append(p)
            nodes = []
            for test in tests:
                source = folder / test.replace("/", "__")
                if source.exists():
                    funcs = re.findall(r"^def (test_\w+)\(", source.read_text(encoding="utf-8"), re.M)
                    nodes.extend(test + "::" + f for f in funcs[:3])
            case = {**{k: entry[k] for k in ("case_id", "source_kind", "repo_url", "dataset", "dataset_revision", "split", "license")},
                    "runner_kind": "python-source-v2", "revision": "v5", "table": "all_pull_request", "record_id": row["id"],
                    "base": base, "head": head, "allowed_file": product[0], "frozen_test_files": frozen,
                    "test_targets": tests, "prompt_test_nodes": nodes or tests, "dependencies": dependencies, "install_project": False,
                    "python_paths": [".", "src"], "writable_dirs": writable, "generation_protocol": SITE_PROTOCOL,
                    "focus_line": focal_line(patch, product[0]), "resources": {"memory_mb": 2048, "cpus": 1},
                    "identity_source": entry["identity_source"], "source_record_sha256": entry["source_record_sha256"],
                    "historical_hypothesis": "Frozen upstream tests on pinned base/head; support requires an observed regression, not PR text"}
            save_case(case); entry.update(eligible=True, environment_cost=cost)
        records.append(entry)
    for folder in sorted((RAW / "records").iterdir()):
        if not (folder / "record.json").exists(): continue
        row = read_json(folder / "record.json"); repo = row["repo"]
        product = [p for p in patch_paths(row["patch"]) if p.endswith(".py") and not is_test(p)]
        is_astroid = repo.endswith("/astroid")
        license_file = folder / "LICENSE"; text = license_file.read_text(encoding="utf-8") if license_file.exists() else ""
        license_id = "LGPL-2.1-or-later" if "GNU LESSER GENERAL PUBLIC LICENSE" in text else "BSD-3-Clause" if "BSD 3-Clause" in text else None
        entry = {"case_id": row["instance_id"], "source_kind": "swebench", "instance_id": row["instance_id"],
                 "repo_url": "https://github.com/" + repo, "dataset": "SWE-bench/SWE-bench_Lite", "dataset_revision": "b0dde1093fe417d83b7184254edf8199c1f0dff5",
                 "split": "development", "source_split": "dev", "eligible": bool(license_id and product and row["FAIL_TO_PASS"]),
                 "license": license_id, "environment_cost": 1 if is_astroid else 2, "changed_file_count": len(patch_paths(row["patch"])),
                 "reasons": [], "source_record_sha256": sha256(folder / "record.json"), "license_evidence_sha256": sha256(license_file)}
        if not entry["eligible"]: entry["reasons"].append("source_license_or_test_evidence_unresolved"); records.append(entry); continue
        f2p = json.loads(row["FAIL_TO_PASS"]) if isinstance(row["FAIL_TO_PASS"], str) else row["FAIL_TO_PASS"]
        p2p = json.loads(row["PASS_TO_PASS"]) if isinstance(row["PASS_TO_PASS"], str) else row["PASS_TO_PASS"]
        targets = sorted(set(t.split("::")[0] for t in f2p + p2p))
        deps = (["lazy-object-proxy==1.9.0", "wrapt==1.13.3", "typing_extensions==4.12.2", "six==1.16.0", "nose==1.3.7", "attrs==22.2.0"] if is_astroid else
                ["numpy==1.23.5", "pandas==1.5.3", "scipy==1.10.1", "pytz==2025.2", "requests==2.32.3", "matplotlib==3.7.5", "h5py==3.10.0"])
        case = {**{k: entry[k] for k in ("case_id", "source_kind", "repo_url", "dataset", "dataset_revision", "split", "license")},
                "runner_kind": "python-source-v2", "revision": entry["dataset_revision"], "table": "dev", "record_id": row["instance_id"],
                "base": row["base_commit"], "head": "base+repair:" + sha256(folder / "repair.patch"), "allowed_file": product[0],
                "repair_patch": (folder / "repair.patch").relative_to(ROOT).as_posix(), "repair_patch_sha256": sha256(folder / "repair.patch"),
                "test_patch": (folder / "test.patch").relative_to(ROOT).as_posix(), "test_patch_sha256": sha256(folder / "test.patch"),
                "fail_to_pass": f2p, "pass_to_pass": p2p, "test_targets": targets, "prompt_test_nodes": f2p,
                "frozen_test_files": patch_paths(row["test_patch"]), "focus_line": focal_line(row["patch"], product[0]),
                "generation_protocol": SITE_PROTOCOL, "source_id_matching": "exact_or_unique_truncated_param",
                "python_image": "python:3.9-slim-bookworm", "dependencies": deps, "python_paths": [".", "src"],
                "resources": {"memory_mb": 2048, "cpus": 1}, "build_timeout": 1200, "test_timeout": 300,
                "historical_hypothesis": "Source FAIL_TO_PASS fail on base/fixed-pass, PASS_TO_PASS stay pass; unique truncated parameter mapping recorded"}
        save_case(case); records.append(entry)
    for entry in records:
        entry["group_id"] = "repo:" + entry["repo_url"].lower().removeprefix("https://github.com/")
        entry["duplicate_family"] = "instance:" + entry["case_id"]
        entry["near_duplicate_status"] = "pending_content_review_before_future_splits"
    assert len(records) == 20, len(records)
    plan = {"schema_version": 2, "split": "development", "screening": records, "selected": select_cases(records),
            "discovery_seconds": read_json(RAW / "discovery-time.json")["active_seconds"], "generation_protocol": SITE_PROTOCOL,
            "candidate_scope": "20 additional purposive AIDev/SWE Lite dev records; metadata failures retained, no independent benchmark claim"}
    path = ROOT / "data-manifests/expansion-02.json"
    if path.exists() and read_json(path) != plan: raise ValueError("Refuse to overwrite a different saved cohort")
    write_json(path, plan)
    print(json.dumps({"selected": plan["selected"], "rejected": {r['case_id']:r['reasons'] for r in records if not r['eligible']}},indent=2))


if __name__ == "__main__": main()
