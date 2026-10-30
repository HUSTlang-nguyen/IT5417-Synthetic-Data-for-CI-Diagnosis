"""Read-only development lineage/duplicate audit; never approves labels or creates a train split."""
from __future__ import annotations
from collections import defaultdict
import difflib
import hashlib
import io
import json
from pathlib import Path
import re
import tokenize
from .common import ROOT, case_config, read_json, sha256


def repo_key(url):
    return url.rstrip("/").removesuffix(".git").lower()


def source_groups(records, configs):
    repos = sorted({repo_key(r["repo_url"]) for r in records}); parents = {r: r for r in repos}
    def find(x):
        while parents[x] != x: parents[x] = parents[parents[x]]; x = parents[x]
        return x
    shared = {}; edges = []
    for record in records:
        repo = repo_key(record["repo_url"]); case = configs.get(record["case_id"], {})
        for revision in (case.get("base", ""), case.get("head", "")):
            if not re.fullmatch(r"[a-f0-9]{40}", revision): continue
            if revision in shared:
                other = shared[revision]
                if find(repo) != find(other):
                    a, b = sorted((find(repo), find(other))); parents[b] = a
                    edges.append({"left": repo, "right": other, "reason": "shared_immutable_commit", "revision": revision})
            else: shared[revision] = repo
    groups = {}
    for record in records:
        root = find(repo_key(record["repo_url"])); key = "repo:" + root.removeprefix("https://github.com/")
        group = groups.setdefault(key, {"group_id": key, "repo_urls": set(), "case_ids": set(), "split": "development"})
        group["repo_urls"].add(record["repo_url"]); group["case_ids"].add(record["case_id"])
    return [{**g, "repo_urls": sorted(g["repo_urls"]), "case_ids": sorted(g["case_ids"])} for g in groups.values()], edges


def lexical_tokens(code):
    """Formatting-only normalization; string literal contents stay significant."""
    try:
        return [(t.type, t.string) for t in tokenize.generate_tokens(io.StringIO(code).readline)
                if t.type not in {tokenize.ENCODING, tokenize.ENDMARKER, tokenize.NEWLINE, tokenize.NL,
                                  tokenize.INDENT, tokenize.DEDENT, tokenize.COMMENT}]
    except (tokenize.TokenError, IndentationError):
        return [("exact_fallback", code)]


def edit_fingerprint(before, after, path):
    old, new = before.splitlines(True), after.splitlines(True); edits = []
    for tag, i, j, a, b in difflib.SequenceMatcher(a=old, b=new, autojunk=False).get_opcodes():
        if tag != "equal": edits.append({"before": lexical_tokens("".join(old[i:j]).lstrip()),
                                          "after": lexical_tokens("".join(new[a:b]).lstrip())})
    return hashlib.sha256(json.dumps({"path": path, "edits": edits}, sort_keys=True).encode()).hexdigest()


def audit_cohorts(paths):
    registries = [read_json(Path(p)) for p in paths]; records = []; seen = set()
    for registry in registries:
        if registry["split"] != "development": raise ValueError("Only declared development cohorts are supported")
        for record in registry["screening"]:
            if record["case_id"] in seen: continue
            seen.add(record["case_id"]); records.append(record)
    configs = {r["case_id"]: case_config(r["case_id"]) for r in records if r.get("eligible")}
    groups, edges = source_groups(records, configs)
    case_group = {c: g["group_id"] for g in groups for c in g["case_ids"]}
    cohorts = {r["case_id"] for registry in registries for r in registry["screening"]}
    attempts = []; exact = defaultdict(list); lexical = defaultdict(list); batches = []
    for manifest in sorted((ROOT / "runs").glob("batch-*/manifest.json")):
        batch = read_json(manifest)
        if batch.get("kind") != "development_batch" or batch["status"] != "batch_finished": continue
        if not all(c["case_id"] in cohorts for c in batch["cases"]): continue
        batches.append(batch["run_id"])
        for item in batch["cases"]:
            if "generate" not in item["stages"]: continue
            folder = ROOT / "runs" / item["stages"]["generate"]["run_id"]; raw = read_json(folder / "manifest.json")
            verification = {}
            if "verify" in item["stages"]:
                verified = read_json(ROOT / "runs" / item["stages"]["verify"]["run_id"] / "manifest.json")
                verification = {a["index"]: a["status"] for a in verified["attempts"]}
            for attempt in raw["attempts"]:
                identity = raw["run_id"] + "/" + attempt["directory"]
                row = {"artifact_id": identity, "case_id": item["case_id"], "group_id": case_group[item["case_id"]],
                       "source_case_id": item.get("source_case_id", item["case_id"]),
                       "generation_run": raw["run_id"], "index": attempt["index"], "protocol": raw.get("protocol", "legacy"),
                       "status": verification.get(attempt["index"], attempt["status"]), "split": "development",
                       "human_confirmation": "pending", "training_eligibility": "pending"}
                if attempt.get("candidate_sha256"):
                    candidate = folder / attempt["directory"] / "candidate.py"
                    if sha256(candidate) != attempt["candidate_sha256"]: raise ValueError("Candidate bytes changed: " + identity)
                    before = (folder / "original.py").read_bytes().decode("utf-8"); after = candidate.read_bytes().decode("utf-8")
                    fingerprint = edit_fingerprint(before, after, raw["source"]["allowed_file"])
                    row.update(candidate_sha256=sha256(candidate), lexical_edit_fingerprint=fingerprint)
                    exact[row["candidate_sha256"]].append(identity)
                    lexical[(case_group[item["case_id"]], fingerprint)].append(identity)
                attempts.append(row)
    return {"schema_version": 1, "scope": "development registries and their finished batches only", "registry_files": [str(p) for p in paths],
            "source_case_records": len({r.get("source_case_id", r["case_id"]) for r in records}),
            "profile_records": len(records), "groups": groups, "shared_commit_edges": edges, "batch_runs": batches,
            "attempts": attempts, "exact_duplicate_candidate_families": [{"sha256": h, "artifacts": ids} for h, ids in exact.items() if len(ids)>1],
            "same_lexical_edit_suggestions": [{"group_id": g, "fingerprint": h, "artifacts": ids} for (g,h),ids in lexical.items() if len(ids)>1],
            "qualification": "Lexical edit similarity is a review suggestion, not semantic equivalence or approval. No raw edits/deletions, gold labels, training export or final train/validation/test assignment."}
