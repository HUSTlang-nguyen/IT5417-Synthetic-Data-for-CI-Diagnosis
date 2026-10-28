"""Fetch immutable commits; export only Git-tracked regular files."""
from __future__ import annotations
import io
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile
from .common import CACHE, ROOT, command, require_success, sha256, write_json

def prepare(case, evidence):
    repo = CACHE / "sources" / "properr"
    repo.parent.mkdir(parents=True, exist_ok=True)
    if not (repo / ".git").is_dir():
        result = command(["git", "clone", "--no-checkout", case["repo_url"] + ".git", repo],
                         evidence, "source-clone", timeout=180)
        require_success(result, "Clone failed")
    locations = {}
    for role in ("base", "head"):
        revision = case[role]
        check = command(["git", "-C", repo, "cat-file", "-e", revision + "^{commit}"],
                        evidence, role + "-commit")
        if check["exit_code"] != 0:
            fetched = command(["git", "-C", repo, "fetch", "--depth", "1", "origin", revision],
                              evidence, role + "-fetch", timeout=180)
            require_success(fetched, "Fetch failed")
        actual = subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", revision + "^{commit}"], text=True).strip()
        if actual != revision:
            raise RuntimeError("Unexpected source revision")
        destination = CACHE / "exports" / revision
        destination.mkdir(parents=True, exist_ok=True)
        archive = subprocess.check_output(["git", "-C", str(repo), "archive", revision], timeout=60)
        tracked = []
        with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
            for member in bundle.getmembers():
                relative = PurePosixPath(member.name)
                if relative.is_absolute() or ".." in relative.parts or not member.isfile():
                    if member.isdir(): continue
                    raise RuntimeError("Unsupported archive entry: " + member.name)
                target = destination.joinpath(*relative.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                stream = bundle.extractfile(member)
                if stream is None: raise RuntimeError("Missing archive content")
                target.write_bytes(stream.read())
                tracked.append(relative.as_posix())
        inventory = {p: sha256(destination / p) for p in tracked}
        write_json(evidence / (role + "-source.json"),
                   {"revision": actual, "files": inventory, "repo": case["repo_url"]})
        locations[role] = destination
    context = CACHE / "docker-context"
    context.mkdir(exist_ok=True)
    shutil.copy2(ROOT / "docker" / "Dockerfile", context / "Dockerfile")
    for role, path in locations.items():
        shutil.copytree(path, context / role, dirs_exist_ok=True)
    return locations, context
