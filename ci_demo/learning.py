"""Dataset-locked learning helpers; optional ML dependencies stay out of the core CLI."""
from __future__ import annotations

from collections import Counter, defaultdict
import json
import math
from pathlib import Path

from .common import CACHE, ROOT, now, read_json, sha256, write_json
from .curation import repo_key
from .diagnosis import LABELS, locations
from .ml import prepare_input


def check_learning_gate(rows, *, protocol="v1.0", model=None):
    """Recompute gates from records instead of trusting a ready flag in a manifest."""
    if protocol not in {"v1.0", "v1.1"} or model not in {None, "M0", "M1", "M2", "M5"}:
        raise ValueError("Unknown learning protocol/model")
    real = [r for r in rows if r["origin"] == "real_local_reconstruction"]
    synthetic = [r for r in rows if r["origin"] == "controlled_synthetic"]
    if len(real) + len(synthetic) != len(rows):
        raise ValueError("Unknown dataset origin")
    if len({r["sample_id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate sample identities")
    counts = Counter(r["role"] for r in real)
    support = Counter(r["reference"]["cause_type"] for r in real if r["role"] == "train")
    if len(real) < 250 or any(counts[role] < 25 for role in ("train", "validation", "test")):
        raise ValueError("Real dataset size/split gate not met")
    if len(support) < 2 or any(n < 10 for n in support.values()):
        raise ValueError("Training class support gate not met")
    if any(r["role"] != "train" for r in synthetic):
        raise ValueError("Synthetic must be train-only")
    if protocol == "v1.0" and len(synthetic) != counts["train"]:
        raise ValueError("Synthetic must be train-only and matched to real train")
    if protocol == "v1.1":
        if counts != {"train": 175, "validation": 37, "test": 38}:
            raise ValueError("Pilot v1.1 requires frozen 175/37/38 real split")
        if model in {None, "M5"} and len(synthetic) != 101:
            raise ValueError("Pilot v1.1 mixed training requires 101 reviewed synthetic")
    groups = defaultdict(set)
    repos = defaultdict(set)
    for row in rows:
        if row["role"] not in {"train", "validation", "test"} or row["quality"] != "silver":
            raise ValueError("Invalid split/reference quality")
        if row["reference"].get("cause_type") not in LABELS or not locations(row["reference"].get("locations"), limit=None):
            raise ValueError("Unresolved learning reference")
        groups[row["group_id"]].add(row["role"])
        repos[repo_key(row["repo"])].add(row["role"])
    if any(len(v) != 1 for v in [*groups.values(), *repos.values()]):
        raise ValueError("Repository/related group crosses splits")
    return {"real": len(real), "synthetic": len(synthetic), "real_by_role": dict(counts), "train_support": dict(support)}


def check_group_review(review, records):
    from .dataset import selection_hash
    if (review.get("status") != "completed" or review.get("selection_sha256") != selection_hash(records)
            or review.get("reviewed_sample_ids") != sorted(r["sample_id"] for r in records)
            or not isinstance(review.get("semantic_review"), str) or not review["semantic_review"].strip()):
        raise ValueError("Group review is not bound to the complete selected dataset")


def lock_dataset(directories, review_path, destination):
    from .dataset import audit_selected_exports
    destination = Path(destination)
    if destination.exists():
        raise ValueError("Refuse to overwrite a dataset lock")
    audit = audit_selected_exports(directories)
    if any(audit[name] for name in ("cross_split_groups", "exact_source_duplicate_families", "exact_candidate_duplicate_families")):
        raise ValueError("Cross-split group or exact duplicate remains")
    review = read_json(review_path)
    check_group_review(review, audit["records"])
    decisions = review.get("lexical_family_decisions", [])
    wanted = {tuple(sorted(family)) for family in audit["lexical_edit_suggestions"]}
    decided = {tuple(sorted(d.get("sample_ids", []))) for d in decisions
               if d.get("decision") == "distinct_mechanisms" and isinstance(d.get("reason"), str) and d["reason"].strip()}
    if wanted != decided or len(decisions) != len(wanted):
        raise ValueError("Unresolved lexical duplicate family")
    rows = []
    for record in audit["records"]:
        folder = Path(record["directory"])
        rows.append({**read_json(folder / "manifest.json"), "group_id": record["group_id"],
                     "reference": read_json(folder / "reference.json")})
    gate = check_learning_gate(rows)
    manifest = {"created_at": now(), "status": "locked", "records": audit["records"], "gate": gate,
        "selection_sha256": audit["selection_sha256"], "evidence_audit": audit,
        "group_review": {"status": "completed", "path": str(Path(review_path).resolve()), "sha256": sha256(review_path)},
        "qualification": "Evidence-reviewed silver, not expert gold; no model prediction used for selection"}
    write_json(destination, manifest)
    return manifest


def load_locked_dataset(path, tokenizer, *, context=2048, model=None):
    manifest = read_json(path)
    if manifest.get("status") != "locked" or manifest.get("group_review", {}).get("status") != "completed":
        raise ValueError("A locked dataset with completed group review is required")
    review = manifest["group_review"]
    if sha256(review["path"]) != review["sha256"]:
        raise ValueError("Locked group review changed")
    check_group_review(read_json(review["path"]), manifest["records"])
    rows = []
    methods = set()
    for item in manifest["records"]:
        folder = Path(item["directory"]).resolve()
        if not folder.is_relative_to((CACHE / "dataset-v1").resolve()):
            raise ValueError("Learning record outside the exported dataset cache")
        if sha256(folder / "manifest.json") != item["manifest_sha256"]:
            raise ValueError("Locked record metadata changed")
        meta = read_json(folder / "manifest.json")
        for name in ("input", "reference", "assessment"):
            if sha256(folder / (name + ".json")) != meta[name + "_sha256"]:
                raise ValueError("Locked learning text/target changed")
        data = read_json(folder / "input.json")
        reference = read_json(folder / "reference.json")
        if set(data) != {"execution_log", "code"} or item["sample_id"] != meta["sample_id"] or reference["sample_id"] != meta["sample_id"]:
            raise ValueError("Input/reference identity boundary mismatch")
        if item["role"] != meta["role"]:
            raise ValueError("Locked split differs from record provenance")
        prepared = prepare_input(data, tokenizer, context=context)
        reference = {**reference, "retrieved_locations": prepared["retrieved_locations_after_tokenization"]}
        rows.append({**meta, "group_id": item["group_id"], "reference": reference, "prepared": prepared,
                     "model_text": tokenizer.decode(prepared["input_ids"], skip_special_tokens=False)})
        methods.add(meta["retrieval"]["method"])
    if len(methods) != 1:
        raise ValueError("Mixed retrieval versions in locked dataset")
    return rows, check_learning_gate(rows, protocol=manifest.get("protocol", "v1.0"), model=model)


def lock_reviewed_pilot(selection_path, destination):
    """Bind v1.1 to the previously completed deep audit; never claim a new source scan."""
    from .dataset import selection_hash
    selection = read_json(selection_path)
    source = selection["full_audit"]
    audit_path = (ROOT / source["path"]).resolve()
    review_path = (ROOT / selection["group_review"]["path"]).resolve()
    if not all(p.is_relative_to(ROOT.resolve()) for p in (audit_path, review_path)):
        raise ValueError("Pilot audit/review outside the project")
    if sha256(audit_path) != source["sha256"] or sha256(review_path) != selection["group_review"]["sha256"]:
        raise ValueError("Reviewed pilot audit/review changed")
    parent = read_json(audit_path)
    if parent.get("status") != "evidence_checked_group_review_pending":
        raise ValueError("Pilot requires a completed evidence audit")
    if any(parent[k] for k in ("cross_split_groups", "exact_source_duplicate_families", "exact_candidate_duplicate_families")):
        raise ValueError("Pilot parent audit has unresolved groups/duplicates")
    indexed = {r["sample_id"]: r for r in parent["records"]}
    records, rows = [], []
    for item in selection["records"]:
        folder = (ROOT / item["directory"]).resolve()
        if not folder.is_relative_to((CACHE / "dataset-v1").resolve()):
            raise ValueError("Pilot export outside dataset cache")
        record = {**item, "directory": str(folder)}
        if record != indexed.get(item["sample_id"]) or sha256(folder / "manifest.json") != item["manifest_sha256"]:
            raise ValueError("Pilot selection differs from audited record")
        meta = read_json(folder / "manifest.json")
        for name in ("input", "reference", "assessment"):
            if sha256(folder / (name + ".json")) != meta[name + "_sha256"]:
                raise ValueError("Reviewed pilot input/reference/assessment changed")
        rows.append({**meta, "group_id": record["group_id"], "reference": read_json(folder / "reference.json")})
        records.append(record)
    review = read_json(review_path)
    check_group_review(review, records)
    ids = {r["sample_id"] for r in records}
    wanted = {tuple(sorted(f)) for f in parent["lexical_edit_suggestions"] if len(ids.intersection(f)) > 1}
    decided = {tuple(sorted(d["sample_ids"])) for d in review.get("lexical_family_decisions", [])
               if d.get("decision") == "distinct_mechanisms" and d.get("reason", "").strip()}
    if wanted != decided or len(review.get("lexical_family_decisions", [])) != len(wanted):
        raise ValueError("Pilot lexical family not reviewed")
    gate = check_learning_gate(rows, protocol="v1.1")
    manifest = {"created_at": now(), "status": "locked", "protocol": "v1.1", "records": records, "gate": gate,
                "selection_sha256": selection_hash(records),
                "selection_source": {"path": str(Path(selection_path).resolve()), "sha256": sha256(selection_path)},
                "evidence_audit": {"parent": source, "selected_records": len(records),
                                   "qualification": "Inherited completed deep audit plus unchanged export hashes; no repeated source inventory scan"},
                "group_review": {"status": "completed", "path": str(review_path), "sha256": sha256(review_path)},
                "qualification": "User-authorized v1.1 pilot, marked silver not expert gold; v1.0 target remains unmet"}
    destination = Path(destination)
    if destination.exists():
        saved = read_json(destination)
        if any(saved.get(k) != manifest[k] for k in ("protocol", "records", "selection_sha256", "selection_source", "group_review")):
            raise ValueError("Refuse to overwrite a different pilot lock")
        return saved
    write_json(destination, manifest)
    return manifest


def check_prepared_pilot(dataset_path):
    """Check prepared metadata/bytes without importing or running a model."""
    manifest = read_json(dataset_path)
    if manifest.get("status") != "locked" or manifest.get("protocol") != "v1.1":
        raise ValueError("Prepared pilot v1.1 lock missing")
    spec = read_json(ROOT / "data-manifests" / "training-v1.1.json")
    if sha256(dataset_path) != spec["dataset_sha256"]:
        raise ValueError("Pilot lock hash differs from approved setup")
    group = manifest["group_review"]
    if sha256(group["path"]) != group["sha256"]:
        raise ValueError("Pilot group review changed")
    check_group_review(read_json(group["path"]), manifest["records"])
    rows = []
    for item in manifest["records"]:
        folder = Path(item["directory"])
        if not folder.resolve().is_relative_to((CACHE / "dataset-v1").resolve()):
            raise ValueError("Prepared pilot export escaped cache")
        meta = read_json(folder / "manifest.json")
        if sha256(folder / "manifest.json") != item["manifest_sha256"]:
            raise ValueError("Prepared pilot record changed")
        for name in ("input", "reference", "assessment"):
            if sha256(folder / (name + ".json")) != meta[name + "_sha256"]:
                raise ValueError("Prepared pilot learning text changed")
        rows.append({**meta, "group_id": item["group_id"], "reference": read_json(folder / "reference.json")})
    gate = check_learning_gate(rows, protocol="v1.1")
    return {"status": "ready_metadata_checked_no_model_run", "protocol": "v1.1", "dataset_sha256": sha256(dataset_path),
            "gate": gate, "optimizer_updates_per_sft": update_budget(rows),
            "qualification": "No model loaded, trained or evaluated; CUDA/backward runtime remains unmeasured"}


def training_example(row, tokenizer):
    target = {key: row["reference"][key] for key in ("cause_type", "locations", "explanation")}
    target_ids = tokenizer.encode(json.dumps(target, ensure_ascii=False, separators=(",", ":")), add_special_tokens=False)
    target_ids.append(tokenizer.eos_token_id)
    if len(target_ids) > row["prepared"]["max_new_tokens"]:
        raise ValueError("Target exceeds locked response budget; do not silently truncate")
    prompt = row["prepared"]["input_ids"]
    return {"input_ids": prompt + target_ids, "attention_mask": [1] * (len(prompt) + len(target_ids)),
            "labels": [-100] * len(prompt) + target_ids, "sample_id": row["sample_id"]}


def update_budget(rows):
    mixed = sum(r["role"] == "train" for r in rows)
    return min(180, math.ceil(3 * mixed / 8))


def select_checkpoint(records):
    eligible = [r for r in records if isinstance(r.get("joint_top1"), (float, int)) and not isinstance(r["joint_top1"], bool)
                and math.isfinite(r["joint_top1"]) and 0 <= r["joint_top1"] <= 1]
    if not eligible:
        raise ValueError("No eligible validation checkpoint")
    return min(eligible, key=lambda r: (-r["joint_top1"], r["step"]))


def fit_classifier(train):
    if not train or any(r["role"] != "train" or r["origin"] != "real_local_reconstruction" for r in train):
        raise ValueError("M0 fits only real train")
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    model = Pipeline([("text", TfidfVectorizer(ngram_range=(1, 2), max_features=20000)),
                      ("classifier", LogisticRegression(C=1, class_weight="balanced", max_iter=1000, random_state=5417))])
    model.fit([r["model_text"] for r in train], [r["reference"]["cause_type"] for r in train])
    return model
