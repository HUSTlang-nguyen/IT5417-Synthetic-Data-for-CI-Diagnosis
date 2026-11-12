"""Dataset-locked learning helpers; optional ML dependencies stay out of the core CLI."""
from __future__ import annotations

from collections import Counter, defaultdict
import json
import math
from pathlib import Path

from .common import CACHE, now, read_json, sha256, write_json
from .curation import repo_key
from .diagnosis import LABELS, locations
from .ml import prepare_input


def check_learning_gate(rows):
    """Recompute gates from records instead of trusting a ready flag in a manifest."""
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
    if len(synthetic) != counts["train"] or any(r["role"] != "train" for r in synthetic):
        raise ValueError("Synthetic must be train-only and matched to real train")
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


def load_locked_dataset(path, tokenizer, *, context=2048):
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
    return rows, check_learning_gate(rows)


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
