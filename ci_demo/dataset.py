"""Evidence-bound silver export; references never enter retrieval or model input."""
from __future__ import annotations

import hashlib
import ast
import json
from collections import Counter, defaultdict
from pathlib import Path

from .common import CACHE, ROOT, now, read_json, run_path, sha256, write_json
from .diagnosis import LABELS, functions, locations, retrieve
from .curation import edit_fingerprint, repo_key, source_groups
from .multicase import inventory, is_test, resolve_targets, safe_relative, test_passed
from . import multicase, ollama, runner


def real_evidence(run_id):
    folder = run_path(run_id)
    raw = read_json(folder / "manifest.json")
    if raw.get("kind") != "case_reproduction" or not raw.get("historical_supported") or not raw.get("head_passed"):
        raise ValueError("Real export requires strict reproduction, not only a passing seed")
    case, gate = raw["source"], raw["environment"]
    if case.get("experiment_role") not in {"train", "validation", "test"}:
        raise ValueError("Missing frozen experiment role")
    for field in ("repair_patch", "test_patch"):
        if sha256(ROOT / case[field]) != case[field + "_sha256"]:
            raise ValueError("Reference patch hash mismatch")
    for role in ("base", "head"):
        if inventory(Path(gate["context"]) / role) != gate["inventories"][role]:
            raise ValueError("Source/test inventory changed: " + role)
    multicase.check_git_fixture(case, gate)
    if not test_passed(raw["head"], folder):
        raise ValueError("Fixed execution no longer supported by saved evidence")
    mode = case.get("source_id_matching", "exact")
    from .upstream_tests import references
    fail_to_pass, pass_to_pass, origin = references(case)
    if origin != 'dataset_supplied' and raw.get('test_reference_origin') != origin:
        raise ValueError('Local-test origin missing from execution evidence')
    if case.get('local_compilation_check'):
        from .compilation import check
        check(case, gate)
    if case.get('local_configuration_check'):
        from .configuration import check
        check(case, gate)
    if origin == 'upstream_recovered_local':
        from .upstream_tests import verify_products
        verify_products(case, Path(gate['context']) / 'head')
    for role, expectation in (("base", "fail"), ("head", "pass")):
        if not resolve_targets(raw[role], folder, fail_to_pass, expectation, mode)[0]:
            raise ValueError("FAIL_TO_PASS reference IDs not supported")
        if pass_to_pass and not resolve_targets(raw[role], folder, pass_to_pass, "pass", mode)[0]:
            raise ValueError("PASS_TO_PASS reference IDs not supported")
    artifacts = {"manifest.json": sha256(folder / "manifest.json"),
                 "license-evidence.json": sha256(folder / "license-evidence.json")}
    if case.get('git_test_fixture'):
        artifacts['git-test-fixture.json'] = sha256(folder / 'git-test-fixture.json')
    if case.get('local_compilation_check'):
        artifacts['compilation-harness.json'] = sha256(folder / 'compilation-harness.json')
    if case.get('local_configuration_check'):
        artifacts['configuration-harness.json'] = sha256(folder / 'configuration-harness.json')
    for role in ("base", "head"):
        result = raw[role]
        if not result.get("container_removed") or result.get("timed_out"):
            raise ValueError("Incomplete isolated execution")
        for key in ("stdout", "stderr", "junit"):
            path = safe_relative(result[key])
            artifacts[path] = sha256(folder / path)
    return raw, artifacts


def check_assessment(assessment, raw, *, source_role="base"):
    if assessment.get("quality") != "silver" or assessment.get("disposition") != "include":
        raise ValueError("Only explicitly assessed silver candidates may be exported")
    if assessment.get("cause_type") not in LABELS or assessment.get("confidence") not in {"medium", "high"}:
        raise ValueError("Unresolved cause classification")
    if any(not isinstance(assessment.get(field), str) or not assessment[field].strip()
           for field in ("mechanism", "evidence_reason", "limitations", "label_source")):
        raise ValueError("Assessment must explain causality, evidence, source and limits")
    expected = locations(assessment.get("locations"), limit=None)
    if not expected or len(expected) != len(assessment["locations"]) or len(expected) > 5:
        raise ValueError("Unresolved or malformed reference locations")
    if source_role not in {"base", "head"}:
        raise ValueError("Invalid assessment source role")
    tree = Path(raw["environment"]["context"]) / source_role
    for file, function in expected:
        if is_test(file):
            raise ValueError("Test detection is not a production causal location")
        text = (tree / file).read_text(encoding="utf-8")
        if function == '<module>':
            continue
        try:
            present = {name for name, _, _ in functions(text)}
            unparseable = False
        except SyntaxError:
            present, unparseable = set(), True
        if function not in present:
            missing = locations(assessment.get("missing_definitions"), limit=None)
            syntax_locations = locations(assessment.get('unparseable_definitions'), limit=None)
            reviewed = syntax_locations if unparseable else missing
            head = (Path(raw["environment"]["context"]) / "head" / file).read_text(encoding="utf-8") if (file, function) in reviewed else ""
            head_functions = {name: start for name, start, _ in functions(head)}
            if function not in head_functions:
                raise ValueError("Reference function absent without reviewed missing-definition evidence")
            # An unchanged prefix anchors the same qualified header before the syntax fault.
            if unparseable and text.splitlines()[:head_functions[function]] != head.splitlines()[:head_functions[function]]:
                raise ValueError('Unparseable reference function lacks an unchanged qualified header')
    if assessment.get("actor", "unknown") != "unknown":
        raise ValueError("Real actor attribution requires a separately approved provenance protocol")
    return expected


def synthetic_evidence(run_id, index):
    """Read a saved verification chain only; never execute, repair or call a model."""
    if isinstance(index, bool) or not isinstance(index, int) or not 1 <= index <= 3:
        raise ValueError("Invalid synthetic attempt")
    folder = run_path(run_id)
    verified = read_json(folder / "manifest.json")
    if (verified.get("kind") != "synthetic_verification" or verified.get("status") != "verification_finished"
            or verified.get("model") != ollama.GENERATOR_MODEL or verified.get("attempt_count") != 3):
        raise ValueError("Expected a complete 7B verification session")
    generated_folder = run_path(verified["generation_run"])
    generated = read_json(generated_folder / "manifest.json")
    if any(sorted(a["index"] for a in raw["attempts"]) != [1, 2, 3] for raw in (generated, verified)):
        raise ValueError("Synthetic session must retain all three attempt identities")
    case, gate = generated["source"], generated["passing_seed"]
    if (case.get("experiment_role") != "train" or verified["source"] != case
            or generated.get("model") != ollama.GENERATOR_MODEL or generated.get("protocol") != multicase.SITE_PROTOCOL
            or generated.get("status") != "generation_finished" or generated.get("kind") != "synthetic_generation"
            or generated.get("attempt_count") != 3 or generated.get("run_id") != verified["generation_run"]):
        raise ValueError("Synthetic export requires current-protocol train-only generation")
    multicase.validate_case(case)
    multicase.check_gate(case, gate)
    seed_folder = run_path(generated["reproduction_run"])
    seed = read_json(seed_folder / "manifest.json")
    if (gate["reproduction_run"] != generated["reproduction_run"] or seed["source"] != case
            or seed["environment"]["image_id"] != gate["image_id"] or not seed.get("head_passed")
            or not test_passed(seed["head"], seed_folder)
            or gate["inventories"]["head"][case["allowed_file"]] != gate["source_hash"]):
        raise ValueError("Passing seed lineage/image/test evidence mismatch")
    item = next((a for a in verified["attempts"] if a["index"] == index), None)
    proposal_item = next((a for a in generated["attempts"] if a["index"] == index), None)
    if not item or not proposal_item or item["status"] != "execution_verified":
        raise ValueError("Only execution-verified candidates may receive a synthetic export")
    directory = safe_relative(item["directory"])
    if directory != proposal_item["directory"]:
        raise ValueError("Generation/verification attempt identity mismatch")
    candidate_folder = generated_folder / directory
    original = (generated_folder / "original.py").read_bytes()
    candidate = (candidate_folder / "candidate.py").read_bytes()
    if (sha256(generated_folder / "original.py") != gate["source_hash"]
            or hashlib.sha256(candidate).hexdigest() != item["candidate_sha256"]
            or item["candidate_sha256"] != proposal_item["candidate_sha256"]):
        raise ValueError("Candidate or passing source hash changed")
    rebuilt = multicase.apply_site_edit(read_json(candidate_folder / "proposal.json"), original.decode("utf-8"),
        case["allowed_file"], read_json(candidate_folder / "allowed-sites.json"))
    if rebuilt.encode("utf-8") != candidate:
        raise ValueError("Candidate no longer matches the saved single-line protocol")
    try:
        ast.parse(candidate.decode("utf-8").lstrip("\ufeff"))
    except SyntaxError as exc:
        raise ValueError("Candidate violates the valid-Python generation protocol") from exc
    evidence = folder / directory
    if (not runner.accepted(item["baseline"], item["repetitions"], item["restored"], evidence)
            or not test_passed(item["baseline"], evidence) or not test_passed(item["restored"], evidence)):
        raise ValueError("Saved baseline/failure/restoration chain no longer supports acceptance")
    paths = [folder / "manifest.json", generated_folder / "manifest.json", generated_folder / "original.py", seed_folder / "manifest.json"]
    paths += [seed_folder / safe_relative(seed["head"][name]) for name in ("stdout", "stderr", "junit")]
    paths += [candidate_folder / name for name in ("candidate.py", "proposal.json", "allowed-sites.json", "change.diff", "prompt.txt", "request.json", "response.raw.json")]
    for result in [item["baseline"], *item["repetitions"], item["restored"]]:
        command = result.get("command", [])
        if (not result.get("container_removed") or result.get("timed_out") or not command or command[0] != "docker"
                or not {"--network=none", "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges", gate["image_id"]}.issubset(command)
                or "--user" not in command or command[command.index("--user") + 1:command.index("--user") + 2] != ["65534:65534"]):
            raise ValueError("Unverified isolated execution/cleanup")
        paths += [evidence / safe_relative(result[name]) for name in ("stdout", "stderr", "junit")]
    return generated, verified, item, {str(p.relative_to(ROOT).as_posix()): sha256(p) for p in paths}


def export_synthetic(run_id, index, assessment_path, destination, *, retriever=None):
    generated, verified, item, hashes = synthetic_evidence(run_id, index)
    case, gate = generated["source"], generated["passing_seed"]
    assessment = read_json(assessment_path)
    if assessment.get("run_id") != run_id or assessment.get("attempt_index") != index or assessment.get("evidence_hashes") != hashes:
        raise ValueError("Synthetic assessment is not bound to this exact attempt/evidence")
    if (assessment.get("prompt_compliance") != "pass" or assessment.get("plausibility") not in {"supported", "qualified"}
            or not isinstance(assessment.get("input_leakage_review"), str) or not assessment["input_leakage_review"].strip()):
        raise ValueError("Synthetic protocol, plausibility and actual-input review are required")
    expected = check_assessment(assessment, {"environment": gate}, source_role="head")
    candidate = run_path(generated["run_id"]) / item["directory"] / "candidate.py"
    log = (run_path(run_id) / item["directory"] / item["repetitions"][0]["stdout"]).read_text(encoding="utf-8")
    # Overlay represents the failing repository version; it adds no query terms or ranking boost.
    retrieval = (retriever or retrieve)(Path(gate["context"]) / "head", log,
        source_overrides={case["allowed_file"]: candidate.read_bytes().decode("utf-8")})
    model_input = {"execution_log": log, "code": retrieval["snippets"]}
    sample_id = "synthetic-" + generated["run_id"] + "-" + str(index)
    reference = {"sample_id": sample_id, "cause_type": assessment["cause_type"],
        "locations": [{"file": file, "function": function} for file, function in expected], "explanation": assessment["mechanism"],
        "retrieved_locations": [{"file": s["file"], "function": s["function"]} for s in retrieval["snippets"]],
        "quality": "silver", "human_gold": "pending"}
    destination = Path(destination)
    if destination.exists():
        raise ValueError("Refuse to overwrite a synthetic dataset record")
    destination.mkdir(parents=True)
    for name, value in (("input", model_input), ("reference", reference), ("assessment", assessment)):
        write_json(destination / (name + ".json"), value)
    metadata = {"created_at": now(), "origin": "controlled_synthetic", "sample_id": sample_id,
        "case_id": case["case_id"], "source_case_id": case["source_case_id"], "role": "train", "repo": case["repo_url"],
        "group_id": case["repo_url"], "source_commit": case["head"], "image_id": gate["image_id"],
        "dataset_revision": case.get("dataset_revision"),
        "generation_run": generated["run_id"], "verification_run": run_id, "attempt_index": index,
        "candidate_sha256": item["candidate_sha256"], "injected_by": {"model": generated["model"], "model_info": generated.get("model_info")},
        "label_source": assessment["label_source"], "quality": "silver", "human_gold": "pending",
        "experimental_use": "marked_silver_authorized_by_active_goal", "evidence_hashes": hashes,
        "input_sha256": sha256(destination / "input.json"), "reference_sha256": sha256(destination / "reference.json"),
        "assessment_sha256": sha256(assessment_path), "retrieval": {k: v for k, v in retrieval.items() if k != "snippets"}}
    write_json(destination / "manifest.json", metadata)
    return metadata


def export_real(run_id, assessment_path, destination, *, retriever=None, input_protocol=None):
    """Export observed input first; use the separate assessment only for target/metadata."""
    raw, evidence_hashes = real_evidence(run_id)
    case, gate = raw["source"], raw["environment"]
    if case.get('local_configuration_check'):
        if input_protocol is None:
            raise ValueError('Configuration export requires a separately frozen configuration input protocol')
        from .input_protocol_v5 import checked_retriever
        if checked_retriever(input_protocol)[0] is not retriever:
            raise ValueError('Configuration export requires the exact frozen retriever')
    assessment = read_json(assessment_path)
    if assessment.get("run_id") != run_id or assessment.get("evidence_hashes") != evidence_hashes:
        raise ValueError("Assessment is not bound to these exact execution artifacts")
    expected = check_assessment(assessment, raw)
    source = Path(gate["context"]) / "base"
    log = (run_path(run_id) / raw["base"]["stdout"]).read_text(encoding="utf-8")
    retrieval = (retriever or retrieve)(source, log)
    # No repair patch, selected edit, assessment or reference location is supplied to retrieve().
    model_input = {"execution_log": log, "code": retrieval["snippets"]}
    model_input_hash = hashlib.sha256(json.dumps(model_input, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    reference = {"sample_id": case["source_case_id"], "cause_type": assessment["cause_type"],
                 "locations": [{"file": file, "function": function} for file, function in expected],
                 "explanation": assessment["mechanism"],
                 "retrieved_locations": [{"file": s["file"], "function": s["function"]} for s in retrieval["snippets"]],
                 "quality": "silver", "human_gold": "pending"}
    destination = Path(destination)
    if destination.exists():
        raise ValueError("Refuse to overwrite a dataset record")
    destination.mkdir(parents=True)
    write_json(destination / "input.json", model_input)
    write_json(destination / "reference.json", reference)
    write_json(destination / "assessment.json", assessment)
    metadata = {"created_at": now(), "origin": "real_local_reconstruction", "sample_id": case["source_case_id"],
                "case_id": case["case_id"], "run_id": run_id, "role": case["experiment_role"],
                "repo": case["repo_url"], "group_id": case["repo_url"], "source_commit": case["base"],
                "image_id": gate["image_id"], "dataset_revision": case["dataset_revision"],
                "actor": "unknown", "label_source": assessment["label_source"], "quality": "silver",
                "human_gold": "pending", "experimental_use": "marked_silver_authorized_by_active_goal",
                "input_sha256": sha256(destination / "input.json"), "input_content_sha256": model_input_hash,
                "reference_sha256": sha256(destination / "reference.json"),
                "assessment_sha256": sha256(assessment_path), "evidence_hashes": evidence_hashes,
                "retrieval": {k: v for k, v in retrieval.items() if k != "snippets"}}
    if case.get('test_reference_policy'):
        metadata['source_test_reference_policy'] = case['test_reference_policy']
        metadata['source_test_reference_qualification'] = 'Upstream recovered local expectations; source F2P/P2P absent'
    if case.get('local_compilation_check'):
        from .compilation import POLICY
        metadata['source_test_reference_policy'] = POLICY
        metadata['source_test_reference_qualification'] = 'Pipeline-owned local compilation smoke, not upstream tests or historical CI'
    if case.get('local_configuration_check'):
        from .configuration import POLICY, QUALIFICATION
        metadata['source_test_reference_policy'] = POLICY
        metadata['source_test_reference_qualification'] = QUALIFICATION
        metadata['generator_seed_eligible'] = False
    write_json(destination / "manifest.json", metadata)
    return metadata


def audit_real_exports(root):
    """Check exported inputs/lineage; proposals are not automatic duplicate adjudication."""
    records = []
    configs = {}
    identities = defaultdict(list)
    edits = defaultdict(list)
    counts = Counter()
    support = {role: Counter() for role in ("train", "validation", "test")}
    methods = set()
    for path in sorted(Path(root).glob("*/manifest.json")):
        meta = read_json(path)
        if meta.get("origin") != "real_local_reconstruction" or meta.get("quality") != "silver":
            raise ValueError("Expected marked-silver real records only")
        folder = path.parent
        for field in ("input", "reference"):
            if sha256(folder / (field + ".json")) != meta[field + "_sha256"]:
                raise ValueError("Dataset record hash mismatch")
        model_input, reference = read_json(folder / "input.json"), read_json(folder / "reference.json")
        if set(model_input) != {"execution_log", "code"} or reference["sample_id"] != meta["sample_id"]:
            raise ValueError("Input/reference boundary or sample identity mismatch")
        if reference.get("cause_type") not in LABELS or not locations(reference.get("locations"), limit=None):
            raise ValueError("Unresolved silver target")
        role = meta["role"]
        if role not in support:
            raise ValueError("Invalid split")
        raw_path = run_path(meta["run_id"]) / "manifest.json"
        if sha256(raw_path) != meta["evidence_hashes"]["manifest.json"]:
            raise ValueError("Source execution manifest changed since review")
        raw = read_json(raw_path)
        case, gate = raw["source"], raw["environment"]
        if (case["source_case_id"] != meta["sample_id"] or case["experiment_role"] != role
                or case["repo_url"] != meta["repo"]):
            raise ValueError("Source lineage/split changed")
        configs[case["case_id"]] = case
        identities[(repo_key(meta["repo"]), case["base"], case["repair_patch_sha256"])].append(meta["sample_id"])
        source = Path(gate["context"])
        texts = {}
        for name in ("base", "head"):
            file = source / name / case["allowed_file"]
            if sha256(file) != gate["inventories"][name][case["allowed_file"]]:
                raise ValueError("Curation source changed")
            texts[name] = file.read_text(encoding="utf-8")
        # Express both real and future synthetic edits in the passing -> failing direction.
        edits[edit_fingerprint(texts["head"], texts["base"], case["allowed_file"])].append(meta["sample_id"])
        counts[role] += 1
        support[role][reference["cause_type"]] += 1
        methods.add(meta["retrieval"]["method"])
        records.append({"sample_id": meta["sample_id"], "case_id": case["case_id"], "repo_url": meta["repo"],
                        "role": role, "directory": str(folder.resolve()), "manifest_sha256": sha256(path)})
    if len({r["sample_id"] for r in records}) != len(records):
        raise ValueError("Repeated independent sample ID")
    if len(methods) > 1:
        raise ValueError("Mixed retrieval versions; export a separate uniform input version")
    groups, edges = source_groups(records, configs)
    roles = {r["case_id"]: r["role"] for r in records}
    cross_split = [g for g in groups if len({roles[c] for c in g["case_ids"]}) > 1]
    exact_families = [values for values in identities.values() if len(values) > 1]
    lexical_suggestions = [values for values in edits.values() if len(values) > 1]
    reasons = []
    if len(identities) < 250:
        reasons.append("fewer_than_250_independent_real_situations")
    if any(counts[role] < 25 for role in support):
        reasons.append("split_below_25_real")
    if len(support["train"]) < 2 or any(n < 10 for n in support["train"].values()):
        reasons.append("insufficient_training_class_support")
    if exact_families or lexical_suggestions:
        reasons.append("duplicate_families_require_curation")
    if cross_split:
        reasons.append("repository_or_shared_commit_group_crosses_splits")
    # Near duplicates still require a recorded technical review before a dataset can lock.
    reasons.append("near_duplicate_review_and_final_dataset_lock_pending")
    return {"created_at": now(), "status": "draft_audit", "real_gate_ready": False,
            "counts": dict(counts), "independent_source_identities": len(identities),
            "label_support": {role: dict(values) for role, values in support.items()},
            "retrieval_methods": sorted(methods), "records": records, "groups": groups,
            "shared_commit_edges": edges, "cross_split_groups": cross_split,
            "exact_source_duplicate_families": exact_families, "lexical_edit_suggestions": lexical_suggestions,
            "remaining_gates": reasons, "synthetic_gate": "not_checked_by_real_only_audit"}


def selection_hash(records):
    return hashlib.sha256(json.dumps(records, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def audit_selected_exports(directories):
    """Revalidate selected real/synthetic exports; never infer a completed group review."""
    records, configs, evidence = [], {}, {}
    exact_real, exact_candidates, edits = defaultdict(list), defaultdict(list), defaultdict(list)
    for folder in sorted(Path(p).resolve() for p in directories):
        if not folder.is_relative_to((CACHE / "dataset-v1").resolve()):
            raise ValueError("Dataset export outside the controlled cache")
        meta = read_json(folder / "manifest.json")
        for name in ("input", "reference", "assessment"):
            if sha256(folder / (name + ".json")) != meta[name + "_sha256"]:
                raise ValueError("Exported input/reference/assessment changed")
        data, reference, assessment = (read_json(folder / (name + ".json")) for name in ("input", "reference", "assessment"))
        if (set(data) != {"execution_log", "code"} or reference["sample_id"] != meta["sample_id"]
                or meta.get("quality") != "silver" or reference.get("quality") != "silver"
                or meta.get("human_gold") != "pending" or reference.get("human_gold") != "pending"):
            raise ValueError("Invalid input/reference identity or silver provenance")
        if meta["origin"] == "real_local_reconstruction":
            key = (meta["run_id"],)
            if key not in evidence:
                evidence[key] = real_evidence(meta["run_id"])
            raw, hashes = evidence[key]
            case, gate = raw["source"], raw["environment"]
            expected = check_assessment(assessment, raw)
            if assessment.get("run_id") != meta["run_id"]:
                raise ValueError("Real assessment run identity mismatch")
            exact_real[(repo_key(meta["repo"]), case["base"], case["repair_patch_sha256"])].append(meta["sample_id"])
            before = (Path(gate["context"]) / "head" / case["allowed_file"]).read_text(encoding="utf-8")
            after = (Path(gate["context"]) / "base" / case["allowed_file"]).read_text(encoding="utf-8")
        elif meta["origin"] == "controlled_synthetic":
            generated, _, item, hashes = synthetic_evidence(meta["verification_run"], meta["attempt_index"])
            case, gate = generated["source"], generated["passing_seed"]
            if (meta["generation_run"] != generated["run_id"] or meta["candidate_sha256"] != item["candidate_sha256"]
                    or assessment.get("run_id") != meta["verification_run"] or assessment.get("attempt_index") != meta["attempt_index"]
                    or assessment.get("prompt_compliance") != "pass" or assessment.get("plausibility") not in {"supported", "qualified"}
                    or not assessment.get("input_leakage_review")):
                raise ValueError("Synthetic identity or quality review mismatch")
            expected = check_assessment(assessment, {"environment": gate}, source_role="head")
            exact_candidates[meta["candidate_sha256"]].append(meta["sample_id"])
            before = (run_path(generated["run_id"]) / "original.py").read_text(encoding="utf-8")
            after = (run_path(generated["run_id"]) / item["directory"] / "candidate.py").read_text(encoding="utf-8")
        else:
            raise ValueError("Unknown dataset origin")
        if hashes != meta["evidence_hashes"] or hashes != assessment["evidence_hashes"]:
            raise ValueError("Raw evidence changed since assessment/export")
        if (meta.get("source_case_id", meta["sample_id"]) != case["source_case_id"] or meta["case_id"] != case["case_id"]
                or meta["role"] != case["experiment_role"] or meta["repo"] != case["repo_url"]
                or reference["cause_type"] != assessment["cause_type"] or set(locations(reference["locations"], limit=None)) != set(expected)
                or reference["explanation"] != assessment["mechanism"]):
            raise ValueError("Source role or assessed reference changed")
        configs[case["case_id"]] = case
        edits[edit_fingerprint(before, after, case["allowed_file"])].append(meta["sample_id"])
        records.append({"sample_id": meta["sample_id"], "case_id": case["case_id"], "repo_url": meta["repo"],
            "role": meta["role"], "directory": str(folder), "manifest_sha256": sha256(folder / "manifest.json")})
    if len({r["sample_id"] for r in records}) != len(records):
        raise ValueError("Repeated selected sample identity")
    groups, edges = source_groups(records, configs)
    group_ids = {case: g["group_id"] for g in groups for case in g["case_ids"]}
    for record in records:
        record["group_id"] = group_ids[record["case_id"]]
    cross_split = [g["group_id"] for g in groups if len({r["role"] for r in records if r["group_id"] == g["group_id"]}) > 1]
    return {"created_at": now(), "status": "evidence_checked_group_review_pending", "records": records,
        "selection_sha256": selection_hash(records), "groups": groups, "shared_commit_edges": edges,
        "cross_split_groups": cross_split,
        "exact_source_duplicate_families": [v for v in exact_real.values() if len(v) > 1],
        "exact_candidate_duplicate_families": [v for v in exact_candidates.values() if len(v) > 1],
        "lexical_edit_suggestions": [v for v in edits.values() if len(v) > 1]}
