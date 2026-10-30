"""Build the first development registry from saved pinned metadata (no source execution).

Raw inputs are downloaded separately into .cache/expansion. This command is
idempotent for the exact snapshot files and never downloads models or runs tests.
"""
from pathlib import Path
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ci_demo.common import read_json, sha256, write_json
from ci_demo.multicase import patch_paths, is_test, validate_case
from ci_demo.batch import select_cases

RAW = ROOT / ".cache" / "expansion"
DEST = ROOT / "data-manifests"
CASE_DEST = ROOT / "cases"
AIDEV_REV = "b8dc67df93e7c11f6f20c84129db7232eb1ec253"
SWE_REV = "b0dde1093fe417d83b7184254edf8199c1f0dff5"


def focus_line(patch):
    found = re.search(r"@@[^\n]*\+(\d+)", patch)
    return int(found.group(1)) if found else 1


def main():
    records = []
    for row in read_json(RAW / "aidev-screen-input.json"):
        repo, number = row["html_url"].removeprefix("https://github.com/").split("/pull/")
        case_id = repo.replace("/", "__") + "-" + number
        folder = RAW / "records" / case_id
        write_json(folder / "source-record.json", row)
        entry = {"case_id": case_id, "source_kind": "aidev", "repo_url": "https://github.com/" + repo,
                 "instance_id": str(row["id"]), "dataset": "hao-li/AIDev", "dataset_revision": AIDEV_REV,
                 "row_idx": row["row_idx"], "source_record_sha256": sha256(folder / "source-record.json"),
                 "eligible": False, "environment_cost": 2, "split": "development", "reasons": []}
        pr = read_json(folder / "pr.json"); files = read_json(folder / "files.json")
        entry["changed_file_count"] = len(files)
        product = [x for x in files if x["filename"].endswith(".py") and not is_test(x["filename"])]
        tests = [x["filename"] for x in files if x["filename"].endswith(".py") and is_test(x["filename"])]
        license_id = read_json(folder / "license.json").get("license", {}).get("spdx_id") if (folder / "license.json").exists() else None
        if case_id == "esaul314__chunkify-340": license_id = "MIT"  # pinned pyproject declaration
        if case_id.startswith("neuron7x__"):
            entry["reasons"].append("source_SPDX_proprietary_conflicts_with_repository_MIT")
        if case_id.startswith("cailleanC1C__"):
            entry["reasons"].append("changed_package_declares_proprietary_license")
        if not license_id or license_id == "NOASSERTION":
            entry["reasons"].append("pinned_source_license_unresolved")
        if license_id and case_id != "esaul314__chunkify-340" and not (folder / "LICENSE").exists():
            entry["reasons"].append("license_not_verified_at_head_revision")
        if len(product) != 1 or not tests: entry["reasons"].append("requires_one_production_file_and_explicit_upstream_test")
        entry["license"] = license_id
        if not entry["reasons"]:
            targets = tests[:]
            if case_id == "PyLabRobot__pylabrobot-527":
                targets = [tests[0] + "::test_serialize_deserialize_special_floats", tests[0] + "::test_serialize_deserialize_closure"]
                deps = ["typing_extensions==4.12.2"]; cost = 0
            elif case_id == "tyighter__tcm-364":
                deps = ["imagesize==1.4.1", "tqdm==4.67.1"]; cost = 0
            elif case_id == "mfat__sshpilot-716":
                deps = ["paramiko==3.5.1", "cryptography==44.0.2", "keyring==25.6.0", "psutil==6.1.1"]; cost = 1
            else:
                deps = ["haystack-ai==2.15.1", "ftfy==6.3.1", "PyYAML==6.0.3", "pydantic==2.10.6", "structlog==24.4.0"]; cost = 1
            frozen = tests[:]
            for name in ("conftest.py", "tests/conftest.py"):
                if (folder / name.replace("/", "__")).exists(): frozen.append(name)
            case = {**{k: entry[k] for k in ("case_id", "source_kind", "repo_url", "dataset", "dataset_revision", "license", "split")},
                    "runner_kind": "python-source-v2", "revision": "v5", "table": "all_pull_request", "record_id": row["id"],
                    "base": pr["base"]["sha"], "head": pr["head"]["sha"], "allowed_file": product[0]["filename"],
                    "test_targets": targets, "frozen_test_files": frozen, "dependencies": deps, "install_project": False,
                    "python_paths": [".", "src"], "focus_line": focus_line(product[0].get("patch", "")),
                    "resources": {"memory_mb": 1024, "cpus": 1}, "build_timeout": 1200, "test_timeout": 300,
                    "source_record_sha256": entry["source_record_sha256"], "pr_metadata_sha256": sha256(folder / "pr.json"),
                    "historical_hypothesis": "Frozen upstream regression tests fail at base and pass at PR head; local reconstruction only"}
            if case_id == "tyighter__tcm-364": case["writable_dirs"] = ["logs"]
            entry.update(eligible=True, environment_cost=cost)
            validate_case(case); write_json(CASE_DEST / case_id / "case.json", case)
        records.append(entry)
    for folder in sorted((RAW / "records").iterdir()):
        if not (folder / "record.json").exists(): continue
        row = read_json(folder / "record.json"); repo = row["repo"]
        product = [p for p in patch_paths(row["patch"]) if p.endswith(".py") and not is_test(p)]
        license_file = next((folder / x for x in ("LICENSE", "LICENSE.txt", "LICENSE.md") if (folder / x).exists()), None)
        entry = {"case_id": row["instance_id"], "instance_id": row["instance_id"], "source_kind": "swebench",
                 "repo_url": "https://github.com/" + repo, "dataset": "SWE-bench/SWE-bench_Lite", "dataset_revision": SWE_REV,
                 "source_split": "dev", "split": "development", "source_record_sha256": sha256(folder / "record.json"),
                 "license": "MIT" if license_file else None, "license_evidence_sha256": sha256(license_file) if license_file else None,
                 "eligible": bool(license_file and product and row["FAIL_TO_PASS"]), "changed_file_count": len(patch_paths(row["patch"])),
                 "environment_cost": int(repo.startswith("sqlfluff/")), "reasons": []}
        if not entry["eligible"]: entry["reasons"].append("missing_license_or_target_evidence")
        if entry["eligible"]:
            f2p = row["FAIL_TO_PASS"]; p2p = row["PASS_TO_PASS"]
            if isinstance(f2p, str): f2p = json.loads(f2p)
            if isinstance(p2p, str): p2p = json.loads(p2p)
            paths = sorted(set(t.split("::")[0] for t in f2p + p2p))
            dependencies = ["pytz==2025.2", "python-dateutil==2.9.0.post0", "simplejson==3.20.1"] if repo.startswith("marshmallow") else ["numpy==1.23.5"]
            if repo.startswith("sqlfluff/"):
                dependencies = ["Jinja2==3.0.3", "click==8.0.4", "diff-cover==6.5.0", "pathspec==0.9.0", "hypothesis==6.54.6"]
            case = {**{k: entry[k] for k in ("case_id", "source_kind", "repo_url", "dataset", "dataset_revision", "license", "split")},
                    "runner_kind": "python-source-v2", "revision": SWE_REV, "table": "dev", "record_id": row["instance_id"],
                    "base": row["base_commit"], "head": "base+repair:" + sha256(folder / "repair.patch"), "allowed_file": product[0],
                    "repair_patch": (folder / "repair.patch").relative_to(ROOT).as_posix(), "repair_patch_sha256": sha256(folder / "repair.patch"),
                    "test_patch": (folder / "test.patch").relative_to(ROOT).as_posix(), "test_patch_sha256": sha256(folder / "test.patch"),
                    "fail_to_pass": f2p, "pass_to_pass": p2p, "test_targets": paths,
                    "frozen_test_files": patch_paths(row["test_patch"]), "focus_line": focus_line(row["patch"]),
                    "python_image": "python:3.9-slim-bookworm", "dependencies": dependencies, "python_paths": [".", "src"],
                    "resources": {"memory_mb": 2048, "cpus": 1}, "build_timeout": 1200, "test_timeout": 300,
                    "historical_hypothesis": "Source FAIL_TO_PASS fail on base and pass with reference repair; PASS_TO_PASS remain passing"}
            validate_case(case); write_json(CASE_DEST / case["case_id"] / "case.json", case)
        records.append(entry)
    for entry in records:
        entry["group_id"] = "repo:" + entry["repo_url"].lower().removeprefix("https://github.com/")
        entry["duplicate_family"] = "instance:" + entry["case_id"]
        entry["near_duplicate_status"] = "pending_content_review_before_future_splits"
    plan = {"schema_version": 2, "split": "development", "screening": records,
            "discovery_seconds": read_json(RAW / "discovery-time.json")["active_seconds"],
            "selection_rule": "environment_cost, changed_file_count, instance ID; alternate sources, <=5/source, <=4/repo",
            "selected": select_cases(records), "candidate_scope": "ten targeted AIDev records from pinned first row group; ten selected SWE Lite dev records; purposive, not representative"}
    assert len(records) == 20
    write_json(DEST / "expansion-01.json", plan)
    print(json.dumps({"screened": len(records), "selected": plan["selected"], "rejected": {r['case_id']: r['reasons'] for r in records if not r['eligible']}}, indent=2))


if __name__ == "__main__": main()
