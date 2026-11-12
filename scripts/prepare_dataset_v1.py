"""Freeze purposive repo roles and pinned real-case recipes, before execution/model results."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ci_demo.common import read_json, sha256, write_json
from ci_demo.multicase import is_test, patch_paths, validate_case, SITE_PROTOCOL

ROLES = {"sympy/sympy": "train", "pydicom/pydicom": "train", "pvlib/pvlib-python": "train",
         "pylint-dev/astroid": "train", "marshmallow-code/marshmallow": "train",
         "sphinx-doc/sphinx": "validation", "pylint-dev/pylint": "test"}
LICENSES = {"sympy/sympy": "BSD-3-Clause", "pydicom/pydicom": "MIT", "pvlib/pvlib-python": "BSD-3-Clause",
            "pylint-dev/astroid": "LGPL-2.1-or-later", "marshmallow-code/marshmallow": "MIT",
            "sphinx-doc/sphinx": "BSD-2-Clause", "pylint-dev/pylint": "GPL-2.0-or-later"}


def recipe(repo, version):
    paths = [".", "src"]
    plugins = []
    if repo == "sympy/sympy":
        deps = ["mpmath==1.2.1"]
    elif repo == "pydicom/pydicom":
        deps = ["numpy==1.23.5"]
    elif repo == "pvlib/pvlib-python":
        deps = ["numpy==1.23.5", "pandas==1.5.3", "scipy==1.10.1", "h5py==3.8.0", "requests==2.31.0", "pytz==2025.2"]
    elif repo == "marshmallow-code/marshmallow":
        deps = ["pytz==2025.2", "python-dateutil==2.9.0.post0", "simplejson==3.20.1"]
    elif repo == "pylint-dev/astroid":
        deps = ["wrapt==1.15.0", "lazy-object-proxy==1.9.0", "typing_extensions==4.12.2"]
    elif repo == "sphinx-doc/sphinx":
        major = int(version.split(".")[0])
        docutils = "0.16" if major < 4 else ("0.17.1" if major < 6 else "0.18.1")
        deps = ["docutils==" + docutils, "Jinja2==3.0.3", "Pygments==2.15.1", "babel==2.12.1", "alabaster==0.7.13",
                "snowballstemmer==2.2.0", "imagesize==1.4.1", "packaging==23.2", "requests==2.31.0",
                "sphinxcontrib-applehelp==1.0.4", "sphinxcontrib-devhelp==1.0.2", "sphinxcontrib-jsmath==1.0.1",
                "sphinxcontrib-htmlhelp==2.0.1", "sphinxcontrib-serializinghtml==1.1.5", "sphinxcontrib-qthelp==1.0.3"]
        plugins = ["sphinx.testing.fixtures"]
    else:
        parts = tuple(int(x) for x in version.split(".")[:2])
        astroid = ("3.0.3" if parts >= (3, 0) else "2.15.8" if parts >= (2, 17) else "2.14.2" if parts >= (2, 16)
                   else "2.12.13" if parts >= (2, 15) else "2.11.7" if parts >= (2, 13) else "2.8.6" if parts >= (2, 11) else "2.7.3")
        deps = ["astroid==" + astroid, "isort==5.10.1", "mccabe==0.7.0", "toml==0.10.2", "tomli==2.0.1",
                "dill==0.3.6", "platformdirs==2.6.2", "typing_extensions==4.12.2"]
    return {"dependencies": deps, "python_paths": paths, "pytest_plugins": plugins, "install_project": False,
            "python_image": "python:3.9-slim-bookworm", "resources": {"memory_mb": 2048, "cpus": 1}}


def prepare():
    source = ROOT / ".cache/dataset-v1-source"
    revision = read_json(source / "dataset-info.json")["sha"]
    destination = ROOT / "data-manifests/dataset-v1-plan.json"
    if destination.exists():
        raise ValueError("Plan already frozen; inspect/resume instead of overwriting")
    rows = read_json(source / "records.json") + read_json(source / "test-records.json")
    exposed = {url.rstrip("/").lower() for g in read_json(ROOT / "data-manifests/development-groups-v1.json")["groups"] for url in g["repo_urls"]}
    for repo, role in ROLES.items():
        if role != "train" and ("https://github.com/" + repo).lower() in exposed:
            raise ValueError("Evaluation repo was exposed during development")
    used = {read_json(p).get("record_id", read_json(p).get("case_id")) for p in (ROOT / "cases").glob("*/case.json")}
    candidates = []
    rejected = {}
    for row in rows:
        repo = row["repo"]
        if repo not in ROLES:
            rejected["outside_declared_repo_scope"] = rejected.get("outside_declared_repo_scope", 0) + 1
            continue
        reason = None
        try:
            product = [p for p in patch_paths(row["patch"]) if not is_test(p)]
            tests = patch_paths(row["test_patch"])
            f2p, p2p = json.loads(row["FAIL_TO_PASS"]), json.loads(row["PASS_TO_PASS"])
            if not product or len(product) > 2 or not all(p.endswith(".py") for p in product):
                reason = "requires_small_python_production_patch"
            elif not tests or not all(is_test(p) or Path(p).name == "conftest.py" for p in tests):
                reason = "test_patch_changes_non_test_source"
            elif not f2p:
                reason = "no_source_FAIL_TO_PASS"
            elif row["instance_id"] in used:
                reason = "prior_case_do_not_rerun"
            elif repo != "sympy/sympy" and not all(".py::" in t for t in f2p + p2p):
                reason = "unsupported_source_test_identity"
        except (ValueError, KeyError):
            reason = "missing_or_unsupported_patch_test_metadata"
        if reason:
            rejected[reason] = rejected.get(reason, 0) + 1
            continue
        candidates.append((len(product), len(row["patch"]), row["instance_id"], row, product, tests, f2p, p2p))
    candidates.sort(key=lambda c: (c[0], c[1], c[2]))
    selected = []
    counts = {"train": 0, "validation": 0, "test": 0}
    maximum = {"train": 300, "validation": 100, "test": 80}
    for _, _, identity, row, product, tests, f2p, p2p in candidates:
        repo = row["repo"]
        role = ROLES[repo]
        if counts[role] >= maximum[role]:
            continue
        case_id = identity + "-ds1"
        raw = ROOT / ".cache/dataset-v1-source/cases" / case_id
        raw.mkdir(parents=True, exist_ok=False)
        write_json(raw / "source-record.json", row)
        for name, content in [("repair.patch", row["patch"]), ("test.patch", row["test_patch"])]:
            (raw / name).write_text(content, encoding="utf-8", newline="\n")
        targets = tests if repo == "sympy/sympy" else sorted({t.split("::")[0] for t in f2p + p2p})
        case = {"case_id": case_id, "source_case_id": identity, "source_kind": "swebench", "dataset": "princeton-nlp/SWE-bench",
                "dataset_revision": revision, "revision": revision, "table": row["original_split"], "record_id": identity,
                "repo_url": "https://github.com/" + repo, "base": row["base_commit"], "head": "base+repair:" + sha256(raw / "repair.patch"),
                "allowed_file": product[0], "license": LICENSES[repo], "verify_pinned_license": True,
                "split": "development", "experiment_role": role, "runner_kind": "python-source-v2",
                "repair_patch": (raw / "repair.patch").relative_to(ROOT).as_posix(), "repair_patch_sha256": sha256(raw / "repair.patch"),
                "test_patch": (raw / "test.patch").relative_to(ROOT).as_posix(), "test_patch_sha256": sha256(raw / "test.patch"),
                "source_record_sha256": sha256(raw / "source-record.json"),
                "fail_to_pass": f2p, "pass_to_pass": p2p, "test_targets": targets, "frozen_test_files": tests,
                "source_id_matching": "exact_unique_function_name" if repo == "sympy/sympy" else "exact_or_unique_truncated_param",
                "generation_protocol": SITE_PROTOCOL, "focus_line": 1, "build_timeout": 1200, "test_timeout": 300,
                "historical_hypothesis": "Source tests fail on base, pass with frozen reference repair; local reconstruction only",
                **recipe(repo, row["version"])}
        # License family is checked again against actual pinned source before Docker build.
        validate_case(case)
        write_json(ROOT / "cases" / case_id / "case.json", case)
        selected.append({"case_id": case_id, "source_case_id": identity, "repo": repo, "role": role,
                         "product_files": product, "source_version": row["version"]})
        counts[role] += 1
    plan = {"schema_version": 1, "source_revision": revision, "repo_roles": ROLES, "selected": selected,
            "selected_counts": counts, "metadata_rows_screened": len(rows), "rejection_counts": rejected,
            "selection_order": "production_file_count, production_patch_bytes, instance_id; independent of test/model outcomes",
            "qualification": "Purposive real reconstruction candidates, not verified samples or official benchmark scores",
            "targets": {"real": 250, "train": 175, "validation": 37, "test": 38},
            "prior_exposed_repos_sha256": sha256(ROOT / "data-manifests/development-groups-v1.json")}
    assert not {r["repo"] for r in selected if r["role"] == "train"} & {r["repo"] for r in selected if r["role"] != "train"}
    write_json(destination, plan)
    print(json.dumps({k: plan[k] for k in ("selected_counts", "metadata_rows_screened", "rejection_counts")}, ensure_ascii=False))


if __name__ == "__main__":
    prepare()
