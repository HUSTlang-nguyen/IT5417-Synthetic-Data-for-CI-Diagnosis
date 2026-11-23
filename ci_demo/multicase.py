"""Versioned multi-repository development experiments; never execute candidates on host."""
from __future__ import annotations
import copy
import ast
import difflib
import hashlib
import io
import json
import posixpath
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tarfile
import tempfile
import time
import xml.etree.ElementTree as ET
from . import ollama, runner
from .common import CACHE, ROOT, command, new_run, now, read_json, require_success, run_path, sha256, successful, write_json

PROTOCOL = "single-file-exact-edit-v2"
SITE_PROTOCOL = "single-line-site-v3"
SITE_PROMPT_REVISION = "single-line-site-v3-quality-r3"
SITE_SCHEMA = {"type": "object", "additionalProperties": False,
               "properties": {k: {"type": "string"} for k in ("path", "site_id", "replacement", "explanation")},
               "required": ["path", "site_id", "replacement", "explanation"]}
EDIT_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {k: {"type": "string"} for k in ("path", "before", "after", "proposed_label", "explanation")},
    "required": ["path", "before", "after", "proposed_label", "explanation"],
}
EDIT_SCHEMA["properties"]["proposed_label"]["enum"] = ["logic", "import", "syntax", "other"]


def safe_relative(value):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value or "\x00" in value:
        raise ValueError("Invalid repository-relative path")
    p = PurePosixPath(value)
    if p.is_absolute() or any(x in ("..", ".git") for x in p.parts) or value.startswith("-"):
        raise ValueError("Unsafe repository-relative path")
    reserved = {"CON", "PRN", "AUX", "NUL", *["COM" + str(i) for i in range(1, 10)], *["LPT" + str(i) for i in range(1, 10)]}
    if any(part.rstrip(" .") != part or part.split(".")[0].upper() in reserved for part in p.parts):
        raise ValueError("Repository path cannot be exported safely on Windows")
    return value


def validate_case(case):
    if case.get("runner_kind") != "python-source-v2" or case.get("split") != "development":
        raise ValueError("Only registered development cases are supported")
    if "experiment_role" in case and case["experiment_role"] not in {"train", "validation", "test"}:
        raise ValueError("Unknown frozen experiment role")
    if case.get("test_workdir", "source") not in ("source", "work"):
        raise ValueError("Test working directory must be source or isolated work tmpfs")
    if case.get("system_tools", []) not in ([], ["git"]):
        raise ValueError("Only the declared git build/runtime tool is supported")
    if 'git_test_fixture' in case and (case['git_test_fixture'] is not True
            or case['repo_url'] != 'https://github.com/gitpython-developers/GitPython'
            or case.get('system_tools') != ['git']):
        raise ValueError('Pinned Git fixture requires its declared GitPython recipe/tool')
    if case.get("source_kind") not in {"aidev", "swebench"}: raise ValueError("Unknown source adapter")
    if case.get("test_reference_policy") is not None:
        from .upstream_tests import provenance
        provenance(case)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,120}", case["case_id"]):
        raise ValueError("Invalid case ID")
    if not re.fullmatch(r"https://github.com/[\w.-]+/[\w.-]+", case["repo_url"]):
        raise ValueError("Expected an explicit GitHub repository URL")
    if any(part in {".", ".."} for part in case["repo_url"].removeprefix("https://github.com/").split("/")):
        raise ValueError("Repository identity cannot contain dot components")
    safe_relative(case["repo_url"].removeprefix("https://github.com/"))
    if not re.fullmatch(r"[0-9a-f]{40}", case["base"]):
        raise ValueError("Base must be an immutable commit")
    if case["source_kind"] == "aidev" and not re.fullmatch(r"[0-9a-f]{40}", case["head"]):
        raise ValueError("Head must be an immutable commit")
    if not case.get("license") or case["license"] in ("NOASSERTION", "unknown"):
        raise ValueError("Unresolved source license")
    safe_relative(case["allowed_file"])
    if not case["allowed_file"].endswith(".py") or is_test(case["allowed_file"]):
        raise ValueError("Generator can edit only a production Python file")
    if not case.get("test_targets") or len(case["test_targets"]) > 600:
        raise ValueError("Explicit bounded test targets required")
    for target in case["test_targets"]:
        safe_relative(target.split("::")[0])
    for path in case.get("python_paths", ["."]):
        if path != ".": safe_relative(path)
    if any(p not in {"logs", "test_logs"} for p in case.get("writable_dirs", [])):
        raise ValueError("Only isolated declared runtime log directories may be writable under source")
    for directory in case.get("writable_dirs", []):
        if any(p == directory or p.startswith(directory + "/") for p in [case["allowed_file"], *case["frozen_test_files"]]):
            raise ValueError("Runtime tmpfs must not cover source/tests")
    if case.get("generation_protocol", PROTOCOL) not in {PROTOCOL, SITE_PROTOCOL}:
        raise ValueError("Unknown generator protocol")
    if case.get("source_id_matching", "exact") not in {"exact", "exact_or_unique_truncated_param", "exact_unique_function_name", "swebench_pytest_options"}:
        raise ValueError("Unknown source test identity matching policy")
    if case.get('source_id_matching') == 'swebench_pytest_options' and (case.get('source_kind') != 'swebench' or case['repo_url'] not in {
            'https://github.com/psf/requests','https://github.com/pydicom/pydicom','https://github.com/pylint-dev/pylint'}):
        raise ValueError('SWE pytest option normalization requires its declared source parser')
    if case.get("source_id_matching") == "exact_unique_function_name" and case["repo_url"] != "https://github.com/sympy/sympy":
        raise ValueError("Function-name source identifiers are specific to SymPy")
    if case.get("pytest_version", "7.4.4") not in {"6.2.5", "7.4.4", "8.3.5"}:
        raise ValueError("Unsupported pinned pytest version")
    for plugin in case.get("pytest_plugins", []):
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*", plugin): raise ValueError("Invalid explicit pytest plugin")
    limits = case["resources"]
    if not (128 <= limits["memory_mb"] <= 8192 and 0 < limits["cpus"] <= 4):
        raise ValueError("Invalid resource bounds")
    if case.get("python_image", "python:3.11-slim-bookworm") not in {
            "python:3.9-slim-bookworm", "python:3.10-slim-bookworm", "python:3.11-slim-bookworm"}:
        raise ValueError("Unsupported Python build image")
    if case.get("test_timeout", 300) > 300 or case.get("build_timeout", 1200) > 1200:
        raise ValueError("Stage timeout exceeds batch protocol")
    for package in case.get("dependencies", []):
        if not re.fullmatch(r"[A-Za-z0-9_.\[\],<>=!~-]+", package) or package.startswith("-"):
            raise ValueError("Dependencies must be package requirements, not commands or URLs")
    if case.get("scm_build_version") is not None:
        if (not isinstance(case["scm_build_version"], str)
                or not re.fullmatch(r"[0-9][A-Za-z0-9.+!-]{0,100}", case["scm_build_version"])
                or not case.get("install_project", True)):
            raise ValueError("SCM build version requires a safe recorded version and project installation")
    for key in ("repair_patch", "test_patch"):
        if case.get(key):
            path = (ROOT / safe_relative(case[key])).resolve()
            if not path.is_relative_to(CACHE.resolve()):
                raise ValueError("Raw patches must be in ignored cache")
            if sha256(path) != case[key + "_sha256"]:
                raise ValueError("Patch hash mismatch")


def is_test(path):
    p = PurePosixPath(path)
    return p.parts[:1] == ("testing",) or any(x in ("test", "tests") for x in p.parts) or p.name.startswith("test_") or p.name.endswith(("_test.py", "_tests.py"))


def patch_paths(text):
    paths = []
    for line in text.splitlines():
        if line.startswith(("--- ", "+++ ")):
            path = line[4:].split("\t")[0]
            if path == "/dev/null": continue
            if not path.startswith(("a/", "b/")): raise ValueError("Unsupported patch path")
            paths.append(safe_relative(path[2:]))
    if not paths: raise ValueError("Patch has no file headers")
    return sorted(set(paths))


def checked(args, evidence, name, timeout=180, cwd=None, guard=None):
    if guard: guard(name)
    result = command(args, evidence, name, timeout=timeout, cwd=cwd)
    require_success(result, name + " failed")
    return result


def archive_links(archive):
    """Retain safe source symlinks as data; materialize only inside the Linux image."""
    members = {m.name.rstrip("/"): m for m in archive.getmembers()}
    links = {}
    for path, member in members.items():
        safe_relative(path)
        if member.isfile() or member.isdir():
            continue
        if not member.issym() or not member.linkname or "\\" in member.linkname or ":" in member.linkname or "\x00" in member.linkname or member.linkname.startswith("/"):
            raise ValueError("Unsafe/nonregular source archive entry: " + path)
        links[path] = member.linkname
    if any(path != p and path.startswith(p + "/") for path in members for p in links):
        raise ValueError("Archive file nested under a symlink")
    for path, target in links.items():
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(path), target))
        for _ in range(len(links) + 1):
            safe_relative(resolved)
            prefix = next((p for p in links if resolved == p or resolved.startswith(p + "/")), None)
            if prefix is None:
                break
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(prefix), links[prefix], resolved[len(prefix):].lstrip("/")))
        else:
            raise ValueError("Cyclic source symlink: " + path)
        if resolved not in members or any(path != p and path.startswith(p + "/") for p in links):
            raise ValueError("Missing target or nested symlink source entry: " + path)
    return links


def export_commit(repo, revision, destination, evidence, name, guard):
    if guard: guard(name + "-commit")
    cached = command(["git", "-C", repo, "cat-file", "-e", revision + "^{commit}"], evidence, name + "-commit")
    if not successful(cached):
        checked(["git", "-C", repo, "fetch", "--depth=1", "origin", revision], evidence, name + "-fetch", guard=guard)
    actual = subprocess.check_output(["git", "-C", str(repo), "rev-parse", revision + "^{commit}"], text=True).strip()
    if actual != revision: raise ValueError("Fetched commit identity mismatch")
    raw = subprocess.check_output(["git", "-c", "core.autocrlf=false", "-c", "core.eol=lf", "-C", str(repo), "archive", revision], timeout=90)
    destination.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        links = archive_links(archive)
        for member in archive.getmembers():
            safe_relative(member.name)
            if member.isdir() or member.issym(): continue
            target = destination / member.name
            if not target.resolve().is_relative_to(destination.resolve()): raise ValueError("Source export escaped context")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.extractfile(member).read())
    write_json(evidence / (name + "-source-links.json"), links)
    return links


def inventory(folder):
    return {p.relative_to(folder).as_posix(): sha256(p) for p in sorted(folder.rglob("*")) if p.is_file()}


def ensure_frozen_tests(inventories):
    base, head = inventories["base"], inventories["head"]
    for path in set(base) | set(head):
        if is_test(path) or PurePosixPath(path).name == "conftest.py":
            if base.get(path) != head.get(path):
                raise ValueError("Undeclared test/harness difference between base and fixed: " + path)


def source_function_targets(case, tree):
    """SymPy source IDs omit paths: resolve exact names once against frozen test ASTs."""
    names = list(dict.fromkeys(case["fail_to_pass"] + case["pass_to_pass"]))
    found = {name: [] for name in names}
    for relative in case["frozen_test_files"]:
        path = tree / relative
        if path.suffix != ".py":
            continue
        module = ast.parse(path.read_text(encoding="utf-8"))
        for node in module.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in found:
                found[node.name].append(relative + "::" + node.name)
    if any(not re.fullmatch(r"test_\w+", name) or len(matches) != 1 for name, matches in found.items()):
        raise ValueError("Source function identifiers missing or ambiguous in frozen tests")
    return [found[name][0] for name in names]


def apply_patch_file(tree, path, evidence, name, guard):
    text = path.read_text(encoding="utf-8")
    patch_paths(text)
    # An exported tree is nested under our repository. Explicit Git/work-tree
    # roots prevent git apply from interpreting paths against the outer checkout.
    metadata = tree.parent / ".patch-git"
    if not metadata.exists():
        checked(["git", "init", "--bare", metadata], evidence, "patch-repository-init", guard=guard)
    prefix = ["git", "-c", "core.autocrlf=false", "-c", "core.eol=lf", "--git-dir=" + str(metadata.resolve()), "--work-tree=" + str(tree.resolve()), "apply"]
    checked([*prefix, "--check", str(path.resolve())], evidence, name + "-check", cwd=tree, guard=guard)
    checked([*prefix, str(path.resolve())], evidence, name, cwd=tree, guard=guard)


def pinned_license(base, declared):
    candidates = [base / name for name in ("LICENSE", "LICENSE.txt", "LICENSE.rst", "LICENSE.md", "COPYING", "COPYING.txt")]
    license_file = next((p for p in candidates if p.is_file()), None)
    if license_file is None:
        raise ValueError("Pinned source license missing")
    text = license_file.read_text(encoding="utf-8", errors="replace")
    markers = {"BSD-3-Clause": "Redistribution and use", "BSD-2-Clause": "Redistribution and use",
               "MIT": "Permission is hereby granted", "GPL-2.0-or-later": "GNU GENERAL PUBLIC LICENSE",
               "LGPL-2.1-or-later": "GNU LESSER GENERAL PUBLIC LICENSE", "Apache-2.0": "Apache License",
               "Unlicense": "This is free and unencumbered software released into the public domain"}
    if markers.get(declared, "<unrecognized>").lower() not in text.lower():
        raise ValueError("Pinned license does not match declared family; manual review required")
    return {"path": license_file.relative_to(base).as_posix(), "sha256": sha256(license_file),
            "declared_license": declared,
            "qualification": "Pinned full license retained; family marker check, not legal review"}


def prepare_git_fixture(case, repo, work, evidence, guard=None):
    """GitPython's TestBase needs a real repo even for its pure utility tests."""
    fixture = work / 'fixture.git'
    checked(['git', '-c', 'core.longpaths=true', '-c', 'init.templateDir=', 'init', '--bare', 'fixture.git'], evidence, 'fixture-init', cwd=work, guard=guard)
    prefix = ['git', '-c', 'core.longpaths=true', '--git-dir=fixture.git']
    checked([*prefix, 'fetch', '--depth=1', str(repo.resolve()), case['base']], evidence, 'fixture-fetch', cwd=work, guard=guard)
    checked([*prefix, 'update-ref', 'refs/heads/pinned-source', case['base']], evidence, 'fixture-ref', cwd=work, guard=guard)
    checked([*prefix, 'symbolic-ref', 'HEAD', 'refs/heads/pinned-source'], evidence, 'fixture-head', cwd=work, guard=guard)
    actual = subprocess.check_output([*prefix, 'rev-parse', 'HEAD'], cwd=work, text=True, timeout=30).strip()
    if actual != case['base'] or (fixture / 'objects/info/alternates').exists():
        raise ValueError('Git fixture must contain the pinned commit without host alternates')
    metadata = {'commit': actual, 'inventory': inventory(fixture), 'runtime_path': '/fixtures/source.git'}
    write_json(evidence / 'git-test-fixture.json', metadata)
    return metadata


def prepare_case(case, evidence, guard=None):
    validate_case(case)
    identity = hashlib.sha256(json.dumps(case, sort_keys=True).encode()).hexdigest()[:16]
    work = CACHE / "case-contexts" / case["case_id"] / identity / evidence.name
    work.mkdir(parents=True)
    repo = CACHE / "sources-v2" / case["repo_url"].removeprefix("https://github.com/")
    if not (repo / ".git").is_dir():
        repo.mkdir(parents=True, exist_ok=True)
        checked(["git", "init", str(repo)], evidence, "source-init", guard=guard)
        checked(["git", "-C", repo, "remote", "add", "origin", case["repo_url"] + ".git"], evidence, "source-origin", guard=guard)
    source_links = {"base": export_commit(repo, case["base"], work / "base", evidence, "base", guard) or {}}
    if case["source_kind"] == "swebench":
        shutil.copytree(work / "base", work / "head")
        source_links["head"] = dict(source_links["base"])
        for role in ("base", "head"):
            apply_patch_file(work / role, ROOT / case["test_patch"], evidence, role + "-test-patch", guard)
        apply_patch_file(work / "head", ROOT / case["repair_patch"], evidence, "gold-repair", guard)
        if case.get("test_reference_policy") is not None:
            from .upstream_tests import verify_products
            verify_products(case, work / "head")
    else:
        source_links["head"] = export_commit(repo, case["head"], work / "head", evidence, "head", guard) or {}
        # Freeze declared head tests onto the base as a reconstruction harness.
        # These are upstream tests, never generated candidate tests.
        for path in case["frozen_test_files"]:
            safe_relative(path)
            if not is_test(path) and PurePosixPath(path).name != "conftest.py":
                raise ValueError("Frozen harness must consist of tests")
            target = work / "base" / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(work / "head" / path, target)
    inventories = {role: inventory(work / role) for role in ("base", "head")}
    for role in inventories: write_json(evidence / (role + "-source.json"), inventories[role])
    ensure_frozen_tests(inventories)
    for path in case["frozen_test_files"]:
        if inventories["base"].get(path) != inventories["head"].get(path):
            raise ValueError("Test bytes differ between base and fixed")
    source = work / "head" / case["allowed_file"]
    if not source.is_file(): raise ValueError("Allowlisted source file missing")
    resolved_targets = source_function_targets(case, work / "head") if case.get("source_id_matching") == "exact_unique_function_name" else case["test_targets"]
    if case.get("verify_pinned_license"):
        write_json(evidence / "license-evidence.json", pinned_license(work / "base", case["license"]))
    fixture = prepare_git_fixture(case, repo, work, evidence, guard) if case.get('git_test_fixture') else None
    dependencies = ["setuptools==75.6.0", "wheel==0.45.1", "pytest==" + case.get("pytest_version", "7.4.4"), *case.get("dependencies", [])]
    install = ["/opt/venv/bin/pip", "install", "--disable-pip-version-check", *dependencies]
    dockerfile = ("FROM " + case.get("python_image", "python:3.11-slim-bookworm") + "\n"
                  "ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1\n")
    if case.get("system_tools"):
        dockerfile += "RUN apt-get update && apt-get install -y --no-install-recommends git && dpkg-query -W git\n"
    dockerfile += (
                  "RUN python -m venv /opt/venv\n"
                  "RUN " + json.dumps(install) + "\n"
                  "COPY base /source/base\nCOPY head /source/head\n")
    if fixture:
        dockerfile += ('COPY fixture.git /fixtures/source.git\n'
                       'RUN git config --system --add safe.directory /fixtures/source.git\n'
                       'ENV GIT_PYTHON_TEST_GIT_REPO_BASE=/fixtures/source.git\n')
    links = [("/source/" + role + "/" + path, target) for role in ("base", "head") for path, target in source_links[role].items()]
    if links:
        program = ("import os; links=" + repr(links) + "; "
                   "[(os.makedirs(os.path.dirname(p),exist_ok=True),os.symlink(t,p)) for p,t in links]")
        dockerfile += "RUN " + json.dumps(["python", "-c", program]) + "\n"
    dockerfile += project_install_steps(case)
    dockerfile += 'RUN ["/opt/venv/bin/pip","freeze","--all"]\nUSER 65534:65534\nWORKDIR /work\n'
    (work / "Dockerfile").write_text(dockerfile, encoding="utf-8")
    image = "it5417-expansion-" + case["case_id"].lower() + ":" + identity
    result = checked(["docker", "build", "--label", "it5417.case=" + identity, "-t", image, work],
                     evidence, "docker-build", timeout=1200, guard=guard)
    inspected = checked(["docker", "image", "inspect", image], evidence, "image-inspect", guard=guard)
    image_info = read_json(evidence / inspected["stdout"])[0]
    if image_info.get("Config", {}).get("Labels", {}).get("it5417.case") != identity:
        raise ValueError("Image case label mismatch")
    gate = {"case_id": case["case_id"], "case_hash": identity, "context": str(work.resolve()),
            "image_id": image_info["Id"], "image_tag": image, "inventories": inventories,
            "source_hash": sha256(source), "test_hashes": {p: inventories["head"][p] for p in case["frozen_test_files"]},
            "reproduction_run": evidence.name, "build": result, "head_passed": False}
    gate["resolved_test_targets"] = resolved_targets
    gate["source_links"] = source_links
    if fixture:
        gate['git_test_fixture'] = fixture
    write_json(evidence / "environment.json", gate)
    return gate


def project_install_steps(case):
    """Generate packaging metadata inside the image; never edit exported source bytes."""
    if not case.get("install_project", True):
        return ""
    version = case.get("scm_build_version")
    result = "ENV SETUPTOOLS_SCM_PRETEND_VERSION=" + version + "\n" if version else ""
    for role in (("base", "head") if version else ("head",)):
        args = ["/opt/venv/bin/pip", "install", "--no-build-isolation"]
        result += "RUN " + json.dumps(args + (["--no-deps"] if version else []) + ["-e", "/source/" + role]) + "\n"
    return result


def execute(case, gate, evidence, name, role="head", candidate=None, guard=None):
    if guard: guard(name)
    if role not in ("base", "head"): raise ValueError("Invalid source role")
    # Inspect the immutable image ID, not a tag that can be retargeted.
    container = "it5417-exp-" + __import__("uuid").uuid4().hex[:16]
    limits = case["resources"]
    args = ["docker", "run", "--name", container, "--network=none", "--read-only", "--user", "65534:65534",
            "--cap-drop=ALL", "--security-opt=no-new-privileges", "--pids-limit=128",
            "--memory=" + str(limits["memory_mb"]) + "m", "--cpus=" + str(limits["cpus"]),
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=256m", "--tmpfs", "/work:rw,noexec,nosuid,size=64m,mode=1777",
            "--workdir", "/work" if case.get("test_workdir") == "work" else "/source/" + role]
    paths = ["/source/" + role + ("/" + p if p != "." else "") for p in case.get("python_paths", ["."])]
    args += ["--env", "PYTHONPATH=" + ":".join(paths), "--env", "HOME=/tmp", "--env", "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1"]
    for path in case.get("writable_dirs", []):
        args += ["--tmpfs", "/source/" + role + "/" + path + ":rw,noexec,nosuid,size=16m,mode=1777"]
    if candidate:
        if "," in str(candidate.resolve()): raise ValueError("Invalid candidate mount path")
        args += ["--mount", "type=bind,src=" + str(candidate.resolve()) + ",dst=/source/" + role + "/" + case["allowed_file"] + ",readonly"]
    evidence.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="junit-", dir=evidence) as tmp:
        output = Path(tmp).resolve(); output.chmod(0o777)
        if "," in str(output): raise ValueError("Invalid results mount path")
        args += ["--mount", "type=bind,src=" + str(output) + ",dst=/results", gate["image_id"],
                 "/opt/venv/bin/python", "-m", "pytest", "-v", "-p", "no:cacheprovider",
                 "--junitxml=/results/results.xml"]
        for plugin in case.get("pytest_plugins", []): args += ["-p", plugin]
        targets = gate.get("resolved_test_targets", case["test_targets"])
        if case.get("test_workdir") == "work":
            args += ["--rootdir=/source/" + role]
            targets = ["/source/" + role + "/" + target for target in targets]
        args += targets
        try:
            result = command(args, evidence, name, timeout=300)
        finally:
            cleanup = command(["docker", "rm", "-f", container], evidence, name + "-cleanup", timeout=20)
        junit = output / "results.xml"
        if successful(cleanup) and not result["timed_out"] and junit.is_file() and not junit.is_symlink() and junit.stat().st_size <= 2_000_000:
            shutil.copyfile(junit, evidence / (name + ".junit.xml")); result["junit"] = name + ".junit.xml"
        result.update(container=container, container_removed=successful(cleanup), role=role)
        write_json(evidence / (name + ".json"), result)
        return result


def test_outcomes(result, folder):
    if result.get("timed_out") or not result.get("junit"): return {}
    root = ET.parse(folder / result["junit"]).getroot()
    outcomes = {}
    for t in root.iter("testcase"):
        status = "fail" if any(x.tag in ("failure", "error") for x in t) else "skip" if t.find("skipped") is not None else "pass"
        cls = (t.get("classname") or "").replace(".", "/")
        name = t.get("name", "")
        outcomes[(cls, name)] = status
    return outcomes


def test_passed(result, folder):
    outcomes = test_outcomes(result, folder)
    return successful(result) and result.get("container_removed", False) and "pass" in outcomes.values() and "fail" not in outcomes.values()


def targets_match(result, folder, targets, status):
    outcomes = test_outcomes(result, folder)
    for target in targets:
        parts = split_test_id(target); file = parts[0].removesuffix(".py"); test = parts[-1]
        cls = file + ("/" + "/".join(parts[1:-1]) if len(parts) > 2 else "")
        if outcomes.get((cls, test)) != status: return False
    return bool(targets)


def split_test_id(target):
    path, boundary, node = target.partition("::")
    if not boundary:
        return [path]
    prefix, bracket, parameter = node.partition("[")
    parts = prefix.split("::")
    parts[-1] += bracket + parameter
    return [path, *parts]


def resolve_targets(result, folder, targets, expected, mode="exact"):
    """Resolve only a unique incomplete parameter ID, never fuzzy test names."""
    outcomes = test_outcomes(result, folder); records = []
    for target in targets:
        if mode == "exact_unique_function_name":
            matches = [(c, n) for c, n in outcomes if n == target]
            resolved = matches[0] if len(matches) == 1 else None
            records.append({"source_id": target, "resolved_class": resolved[0] if resolved else None,
                            "resolved_name": resolved[1] if resolved else None,
                            "resolution": "exact_unique_function_name" if resolved else "unresolved",
                            "expected": expected, "observed": outcomes.get(resolved)})
            continue
        parts = split_test_id(target); cls = parts[0].removesuffix(".py")
        if len(parts) > 2: cls += "/" + "/".join(parts[1:-1])
        name = parts[-1]; resolved = name if (cls, name) in outcomes else None; how = "exact"
        if mode == 'swebench_pytest_options':
            # SWE-bench v4.1.0 parse_log_pytest_options canonicalizes absolute path parameters.
            def canonical(value):
                tokens = value.split(maxsplit=1)
                if not tokens: return value
                value = tokens[0]
                prefix, boundary, parameter = value.partition('[')
                parameter = parameter[:-1] if value.endswith(']') else ''
                if boundary and parameter.startswith('/') and not parameter.startswith('//') and '*' not in parameter:
                    return prefix + '[/' + parameter.rsplit('/', 1)[-1] + ']'
                return value
            matches = sorted(n for c, n in outcomes if c == cls and canonical(n) == name)
            statuses = {outcomes[(cls, n)] for n in matches}
            observed = next(iter(statuses)) if len(statuses) == 1 else 'mixed' if statuses else None
            records.append({'source_id': target, 'resolved_class': cls,
                            'resolved_name': matches[0] if len(matches) == 1 else name if matches else None,
                            'resolved_names': matches, 'resolution': 'swebench_canonical_group' if matches else 'unresolved',
                            'expected': expected, 'observed': observed})
            continue
        if resolved is None and mode == "exact_or_unique_truncated_param" and "[" in name and not name.endswith("]"):
            matches = [n for c, n in outcomes if c == cls and n.startswith(name)]
            if len(matches) == 1: resolved = matches[0]; how = "unique_truncated_parameter_prefix"
        records.append({"source_id": target, "resolved_class": cls, "resolved_name": resolved,
                        "resolution": how if resolved is not None else "unresolved",
                        "expected": expected, "observed": outcomes.get((cls, resolved))})
    return bool(records) and all(r["resolved_name"] is not None and r["observed"] == expected for r in records), records


def reproduce_case(case, folder=None, guard=None):
    folder = folder or new_run("reproduce")
    manifest = {"schema_version": 2, "kind": "case_reproduction", "run_id": folder.name, "source": case,
                "created_at": now(), "status": "running", "qualification": "Local reconstruction with frozen upstream tests; not historical CI logs"}
    write_json(folder / "manifest.json", manifest)
    try:
        gate = prepare_case(case, folder, guard); manifest["environment"] = gate
        manifest["base"] = execute(case, gate, folder, "historical-base", "base", guard=guard)
        manifest["head"] = execute(case, gate, folder, "historical-fixed", guard=guard)
        base_fail = bool(runner.failure_signature(manifest["base"], folder))
        fixed_pass = test_passed(manifest["head"], folder)
        supported = base_fail and fixed_pass
        if case["source_kind"] == "swebench":
            from . import upstream_tests
            fail_to_pass, pass_to_pass, origin = upstream_tests.references(case)
            mode = case.get("source_id_matching", "exact")
            recovered = origin == 'upstream_recovered_local'
            resolution_key = 'local_test_resolution' if recovered else 'source_test_resolution'
            manifest[resolution_key] = []
            if recovered:
                manifest['test_reference_origin'] = origin
                manifest['test_reference_implementation_sha256'] = sha256(upstream_tests.__file__)
            for role, expectation in (("base", "fail"), ("head", "pass")):
                ok, detail = resolve_targets(manifest[role], folder, fail_to_pass, expectation, mode)
                supported = supported and ok
                manifest[resolution_key].append({"role": role, "set": "LOCAL_EXPECTED_FAILURES" if recovered else "FAIL_TO_PASS", "matching_mode": mode, "records": detail})
            for role in ("base", "head"):
                if pass_to_pass:
                    ok, detail = resolve_targets(manifest[role], folder, pass_to_pass, "pass", mode)
                    supported = supported and ok
                    manifest[resolution_key].append({"role": role, "set": "LOCAL_EXPECTED_PASSES" if recovered else "PASS_TO_PASS", "matching_mode": mode, "records": detail})
        manifest["historical_supported"] = bool(supported)
        gate["head_passed"] = bool(fixed_pass)
        manifest["status"] = "hypothesis_supported_locally" if supported else "hypothesis_not_confirmed"
        manifest["head_passed"] = bool(fixed_pass)
        write_json(folder / "environment.json", gate)
        if fixed_pass:
            write_json(CACHE / "passing-seeds" / (case["case_id"] + ".json"),
                       {"reproduction_run": folder.name, "case_hash": gate["case_hash"]})
    except (OSError, RuntimeError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        manifest.update(status="environment_error", error=str(exc))
    manifest["finished_at"] = now(); write_json(folder / "manifest.json", manifest)
    return manifest


def check_git_fixture(case, gate):
    if case.get('git_test_fixture'):
        fixture = gate.get('git_test_fixture') or {}
        if (fixture.get('commit') != case['base'] or fixture.get('runtime_path') != '/fixtures/source.git'
                or inventory(Path(gate['context']) / 'fixture.git') != fixture.get('inventory')):
            raise ValueError('Pinned Git fixture changed or missing')


def check_gate(case, gate):
    if not gate.get("head_passed") or gate["case_id"] != case["case_id"]: raise ValueError("No matching passing seed")
    expected = hashlib.sha256(json.dumps(case, sort_keys=True).encode()).hexdigest()[:16]
    if gate["case_hash"] != expected: raise ValueError("Case configuration changed")
    head = Path(gate["context"]) / "head"
    if inventory(head) != gate["inventories"]["head"]: raise ValueError("Pinned source/tests changed")
    check_git_fixture(case, gate)
    return head


def apply_edit(proposal, original, allowed):
    if not isinstance(proposal, dict) or set(proposal) != set(EDIT_SCHEMA["required"]): raise ValueError("Unexpected edit fields")
    if not all(isinstance(x, str) for x in proposal.values()): raise ValueError("Edit fields must be strings")
    if proposal["path"] != allowed: raise ValueError("Edit outside allowlist")
    before, after = proposal["before"], proposal["after"]
    if not before.strip() or original.count(before) != 1: raise ValueError("Before text must match exactly once")
    if before == after or "\x00" in after or max(len(before), len(after)) > 12000: raise ValueError("Invalid edit")
    if proposal["proposed_label"] not in EDIT_SCHEMA["properties"]["proposed_label"]["enum"]: raise ValueError("Unknown generator proposal")
    return original.replace(before, after, 1)


def mutation_sites(original, focus_line, *, identity=None, test_context=""):
    """Static parsing of a pinned passing seed; never import/execute that source."""
    lines = original.splitlines(keepends=True)
    try: tree = ast.parse(original.lstrip("\ufeff"))
    except SyntaxError as exc: raise ValueError("Passing source is outside host static parser grammar") from exc
    numbers = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Compare, ast.BoolOp, ast.BinOp, ast.UnaryOp, ast.Return, ast.IfExp)): continue
        if getattr(node, "end_lineno", None) != node.lineno: continue
        text = lines[node.lineno - 1].rstrip("\r\n").strip()
        if len(text) > 220 or text.startswith(("#", "def ", "class ", "import ", "from ")): continue
        if not (text.startswith(("if ", "elif ", "return ", "while ", "assert ")) or " = " in text): continue
        numbers.add(node.lineno)
    if identity is not None:
        referenced = set(re.findall(r"\b([A-Za-z_]\w*)\s*\(", test_context))
        ranges = [(n.lineno, n.end_lineno) for n in ast.walk(tree)
                  if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name in referenced]
        relevant = [n for n in numbers if any(lo <= n <= hi for lo, hi in ranges)]
        # Static name matches are a preference, never a claim of execution coverage.
        numbers = sorted(relevant or numbers,
            key=lambda n: hashlib.sha256((identity + ":" + str(n)).encode()).digest())[:18]
    else:
        numbers = sorted(numbers, key=lambda n: (abs(n - focus_line), n))[:18]
    return [{"site_id": str(i + 1), "line": n, "source": lines[n - 1].rstrip("\r\n").lstrip()}
            for i, n in enumerate(numbers)]


def site_context(original, sites):
    lines = original.splitlines(keepends=True)
    return "\n".join("LINE " + str(site["line"]) + ":\n" +
        "".join(lines[max(0, site["line"] - 4):site["line"] + 3])
        for site in sorted(sites, key=lambda site: site["line"]))[:3600]


def apply_site_edit(proposal, original, allowed, sites):
    if not isinstance(proposal, dict) or set(proposal) != set(SITE_SCHEMA["required"]): raise ValueError("Unexpected site edit fields")
    if not all(isinstance(v, str) for v in proposal.values()): raise ValueError("Site fields must be strings")
    if proposal["path"] != allowed: raise ValueError("Edit outside allowlist")
    site = next((s for s in sites if s["site_id"] == proposal["site_id"]), None)
    if not site: raise ValueError("Site is not allowed for this attempt")
    text = proposal["replacement"]
    if not text.strip() or text != text.lstrip() or any(c in text for c in "\r\n\x00") or len(text) > 600:
        raise ValueError("Replacement must be one nonempty unindented code line")
    lines = original.splitlines(keepends=True); before = lines[site["line"] - 1]
    body = before.rstrip("\r\n"); ending = before[len(body):]; indent = body[:len(body) - len(body.lstrip())]
    if text == body.lstrip(): raise ValueError("Unchanged site")
    lines[site["line"] - 1] = indent + text + ending
    return "".join(lines)


def test_excerpt(case, head):
    targets = case.get("prompt_test_nodes", case.get("fail_to_pass", case["test_targets"]))
    if case.get("source_id_matching") == "exact_unique_function_name":
        targets = source_function_targets(case, head)
    chunks = []; budget = 2500
    for target in targets[:4]:
        parts = split_test_id(target); path = safe_relative(parts[0]); file = head / path
        if not file.is_file(): continue
        text = file.read_bytes().decode("utf-8"); lines = text.splitlines(keepends=True)
        name = parts[-1].split("[")[0] if len(parts) > 1 else None
        try:
            nodes = [n for n in ast.walk(ast.parse(text)) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                     and (n.name == name if name else n.name.startswith("test_"))]
        except SyntaxError: nodes = []
        for node in nodes[:2]:
            snippet = "".join(lines[node.lineno - 1:node.end_lineno])[:budget]
            chunks.append(path + ":" + str(node.lineno) + "\n" + snippet); budget -= len(snippet)
            if budget <= 0: return "\n".join(chunks)
    return "\n".join(chunks)


def generate_case(case, endpoint, folder=None, reproduction_run=None, guard=None):
    folder = folder or new_run("generate")
    protocol = case.get("generation_protocol", PROTOCOL)
    manifest = {"schema_version": 2, "kind": "synthetic_generation", "protocol": protocol, "run_id": folder.name,
                "created_at": now(), "status": "running", "source": case, "model": ollama.GENERATOR_MODEL,
                "attempt_count": 3, "attempts": [], "options": ollama.OPTIONS, "human_review": "pending",
                "reproduction_run": reproduction_run, "origin": "controlled_synthetic_not_historical"}
    if protocol == SITE_PROTOCOL:
        manifest["prompt_revision"] = SITE_PROMPT_REVISION
    write_json(folder / "manifest.json", manifest)
    try:
        if case.get("experiment_role") in {"validation", "test"}:
            raise ValueError("Held-out validation/test cases cannot be used for generation")
        if reproduction_run is None:
            reproduction_run = read_json(CACHE / "passing-seeds" / (case["case_id"] + ".json"))["reproduction_run"]
            manifest["reproduction_run"] = reproduction_run
        reproduced = read_json(run_path(reproduction_run) / "manifest.json")
        gate = reproduced["environment"]; head = check_gate(case, gate)
        original = (head / case["allowed_file"]).read_bytes().decode("utf-8")
        (folder / "original.py").write_bytes(original.encode("utf-8"))
        manifest["passing_seed"] = gate
        manifest["preflight"] = execute(case, gate, folder, "generation-preflight", guard=guard)
        if not test_passed(manifest["preflight"], folder): raise ValueError("Passing seed no longer passes")
        manifest["model_info"] = ollama.model_info(endpoint, ollama.GENERATOR_MODEL)
        manifest["runtime_version"] = json.loads(ollama.request(endpoint, "/api/version", timeout=10))
        lines = original.splitlines(keepends=True); focus = max(0, int(case.get("focus_line", 1)) - 1)
        start = max(0, focus - 25); excerpt = "".join(lines[start:start + 100])[:9000]
        prompt = ("Create ONE plausible controlled Python regression in the passing source below. "
                  "Return JSON with path, before, after, proposed_label, explanation. before must be an exact, unique "
                  "substring of the source excerpt; after replaces it once. Use a small edit, keep public API/imports. "
                  "Do not change tests, dependencies or other files. Do not add comments/explanations identifying the bug "
                  "in code. proposed_label is unconfirmed metadata. Return no markdown.\nFILE: " + case["allowed_file"]
                  + "\nINDEPENDENT TEST TARGETS: " + json.dumps(case["test_targets"])[:1800]
                  + "\nPASSING SOURCE EXCERPT (line " + str(start + 1) + "):\n" + excerpt)
        (folder / "prompt.txt").write_text(prompt, encoding="utf-8")
        write_json(folder / "tests.json", gate["test_hashes"])
        schema = copy.deepcopy(EDIT_SCHEMA); schema["properties"]["path"]["enum"] = [case["allowed_file"]]
        sites = []
        if protocol == SITE_PROTOCOL:
            independent_tests = test_excerpt(case, head)
            sites = mutation_sites(original, int(case.get("focus_line", 1)),
                identity=case.get("source_case_id", case["case_id"]), test_context=independent_tests)
            if not sites: raise ValueError("No bounded single-line mutation sites in passing seed")
            write_json(folder / "mutation-sites.json", sites)
            manifest["site_selection"] = "static-test-names-and-case-sha256-v1"
            (folder / "independent-tests.txt").write_text(independent_tests, encoding="utf-8")
            manifest["generator_labels"] = "not_requested_by_v3"
            (folder / "prompt.txt").write_text("Protocol " + SITE_PROTOCOL + ": actual per-attempt prompts are stored in attempt-XX/prompt.txt and request.json.\n", encoding="utf-8")
        for index in range(3):
            if guard: guard("model-attempt-" + str(index + 1))
            d = folder / ("attempt-" + str(index + 1).zfill(2)); d.mkdir()
            item = {"index": index + 1, "directory": d.name, "status": "generation_in_progress", "human_review": "pending"}
            manifest["attempts"].append(item); write_json(folder / "manifest.json", manifest)
            attempt_prompt = prompt
            allowed_sites = sites[index::3] or sites
            if protocol == SITE_PROTOCOL:
                schema = copy.deepcopy(SITE_SCHEMA)
                schema["properties"]["path"]["enum"] = [case["allowed_file"]]
                schema["properties"]["site_id"]["enum"] = [s["site_id"] for s in allowed_sites]
                attempt_prompt = ("Inject ONE small plausible WRONG behavior into this passing Python file. Do not fix or improve code. "
                    "Choose one allowed site_id and provide replacement: a single code line WITHOUT leading indentation. "
                    "The pipeline keeps original indentation/newline and replaces exactly that line. Preserve valid Python syntax, "
                    "API and tests. Choose a realistic wrong comparison, boundary, operator, attribute, call or guarded return "
                    "whose intended behavior follows from this source and its tests. Do not append arbitrary numeric offsets "
                    "or fabricated string/list markers. Do not force conditions with 'or True' or 'and False'. "
                    "Do not reverse or globally replace output strings as an arbitrary corruption. "
                    "Do not add comments explaining the bug. Return JSON path, site_id, replacement, explanation; no markdown or diagnosis label.\n"
                    + "FILE: " + case["allowed_file"] + "\nALLOWED SITES:\n" + json.dumps(allowed_sites, ensure_ascii=False)
                    + "\nPASSING SOURCE CONTEXT:\n" + site_context(original, allowed_sites)
                    + "\nIMMUTABLE UPSTREAM TEST EXCERPTS:\n" + independent_tests)
                (d / "prompt.txt").write_text(attempt_prompt, encoding="utf-8")
                write_json(d / "allowed-sites.json", allowed_sites)
            payload = {"model": ollama.GENERATOR_MODEL, "stream": False, "format": schema,
                       "messages": [{"role": "user", "content": attempt_prompt}], "options": {**ollama.OPTIONS, "seed": 5417 + index}, "keep_alive": 0}
            write_json(d / "request.json", payload); started = time.monotonic()
            try:
                raw = ollama.request(endpoint, "/api/chat", payload, timeout=180)
                (d / "response.raw.json").write_text(raw, encoding="utf-8")
                response = json.loads(raw); write_json(d / "response.json", response)
                if not response.get("done") or response.get("done_reason") == "length": raise ValueError("Incomplete/truncated model output")
                proposal = json.loads(response["message"]["content"]); write_json(d / "proposal.json", proposal)
                content = (apply_site_edit(proposal, original, case["allowed_file"], allowed_sites) if protocol == SITE_PROTOCOL
                           else apply_edit(proposal, original, case["allowed_file"]))
                (d / "candidate.py").write_text(content, encoding="utf-8", newline="")
                (d / "change.diff").write_text("".join(difflib.unified_diff(original.splitlines(True), content.splitlines(True),
                                                     fromfile="a/" + case["allowed_file"], tofile="b/" + case["allowed_file"])), encoding="utf-8", newline="")
                item.update(status="awaiting_verification", candidate_sha256=sha256(d / "candidate.py"), proposed_label=proposal.get("proposed_label"))
            except (OSError, ValueError, KeyError, TypeError) as exc:
                item.update(status="generation_error" if isinstance(exc, OSError) else "invalid_output", error=str(exc))
            item["generation_seconds"] = round(time.monotonic() - started, 3)
            write_json(folder / "manifest.json", manifest)
            print(case["case_id"], "attempt", index + 1, item["status"], flush=True)
        manifest["status"] = "generation_finished"
    except (OSError, RuntimeError, ValueError, KeyError) as exc:
        manifest.update(status="environment_error", error=str(exc))
    manifest["finished_at"] = now(); write_json(folder / "manifest.json", manifest)
    return manifest


def verify_case(generation_run, folder=None, guard=None):
    generation = run_path(generation_run); raw = read_json(generation / "manifest.json")
    if raw.get("model") != ollama.GENERATOR_MODEL: raise ValueError("Only the configured 7B generator can be verified")
    if raw.get("kind") != "synthetic_generation" or raw.get("status") != "generation_finished" or not raw.get("passing_seed"):
        raise ValueError("Verification requires a finished generation with a passing seed")
    folder = folder or new_run("verify")
    case = raw["source"]; gate = raw["passing_seed"]
    manifest = {"schema_version": 2, "kind": "synthetic_verification", "source": case, "run_id": folder.name,
                "created_at": now(), "status": "running", "generation_run": generation_run, "attempt_count": 3,
                "attempts": [], "human_review": "pending", "model": raw["model"],
                "verification_policy": "stop_repetitions_after_timeout_restore_still_required_v1"}
    write_json(folder / "manifest.json", manifest)
    try:
        head = check_gate(case, gate)
        if sha256(generation / "original.py") != gate["source_hash"]: raise ValueError("Generation source hash mismatch")
        for item in raw["attempts"]:
            result = copy.deepcopy(item); manifest["attempts"].append(result)
            if item["status"] != "awaiting_verification": continue
            candidate = generation / item["directory"] / "candidate.py"
            if sha256(candidate) != item["candidate_sha256"]: raise ValueError("Candidate hash mismatch")
            d = folder / item["directory"]; d.mkdir()
            result["baseline"] = execute(case, gate, d, "baseline", guard=guard)
            result["repetitions"] = []
            if successful(result["baseline"]):
                for i in range(3):
                    result["repetitions"].append(execute(case, gate, d, "candidate-" + str(i + 1), candidate=candidate, guard=guard))
                    write_json(folder / "manifest.json", manifest)
                    if result["repetitions"][-1]["timed_out"]:
                        break
            result["restored"] = execute(case, gate, d, "restored", guard=guard)
            accepted = (runner.accepted(result["baseline"], result["repetitions"], result["restored"], d)
                        and test_passed(result["baseline"], d) and test_passed(result["restored"], d))
            result["status"] = "execution_verified" if accepted else "verification_failed"
            if not accepted: result["rejection_reason"] = runner.rejection_reason(result["baseline"], result["repetitions"], result["restored"], d)
            write_json(d / "review.json", {"status": "pending", "reviewer": None, "confirmed_label": None,
                                           "confirmed_locations": [], "training_eligibility": "pending"})
            write_json(folder / "manifest.json", manifest)
            print(case["case_id"], "verified", item["index"], result["status"], flush=True)
        manifest["status"] = "verification_finished"
    except (OSError, RuntimeError, ValueError, KeyError) as exc:
        manifest.update(status="environment_error", error=str(exc))
    manifest["finished_at"] = now(); write_json(folder / "manifest.json", manifest)
    return manifest
