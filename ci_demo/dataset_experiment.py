"""Sequential, resumable real-case reconstruction for the frozen dataset experiment."""
from __future__ import annotations

import argparse
from collections import Counter

from . import multicase
from .batch import BudgetStop, batch_lock
from .common import ROOT, case_config, new_run, now, read_json, sha256, write_json
from .experiment import active_experiment


def freeze_plan(experiment, path):
    destination = experiment.folder / ("source-plan-lock.json" if path.name == "dataset-v1-plan.json" else "source-plan-lock-" + path.stem + ".json")
    plan = read_json(path)
    identities = [row["case_id"] for row in plan["selected"]]
    from .data_study import DataStudy
    target = 1000 if isinstance(experiment, DataStudy) else 250
    if len(identities) != len(set(identities)) or plan["targets"]["real"] != target:
        raise ValueError("Duplicate profile or changed real-data target")
    if isinstance(experiment, DataStudy):
        from .source_roles import validate_plan_sources
        expected_sources = validate_plan_sources(read_json(experiment.manifest), plan)
    if destination.exists():
        locked = read_json(destination)
        if locked["plan_sha256"] != sha256(path):
            raise ValueError("Source plan changed after lock")
    else:
        locked = {"locked_at": now(), "plan_sha256": sha256(path), "cases": {}}
        for row in plan["selected"]:
            identity = row["case_id"]
            case = case_config(identity)
            if row.get('case_sha256') and row['case_sha256'] != sha256(ROOT / 'cases' / identity / 'case.json'):
                raise ValueError('Prepared recipe changed before source lock')
            if (case["experiment_role"] != row["role"] or plan["repo_roles"].get(row["repo"]) != row["role"]
                    or case["repo_url"] != "https://github.com/" + row["repo"]
                    or case["source_case_id"] != row["source_case_id"]):
                raise ValueError("Case identity/repository/role differs from source plan")
            locked["cases"][identity] = {"case_sha256": sha256(ROOT / "cases" / identity / "case.json"),
                "repair_patch_sha256": case["repair_patch_sha256"], "test_patch_sha256": case["test_patch_sha256"]}
        write_json(destination, locked)
    for row in plan["selected"]:
        identity = row["case_id"]
        case = case_config(identity)
        if isinstance(experiment, DataStudy):
            expected = expected_sources[row['source_case_id']]
            if case['base'] != expected['base_commit'] or case['dataset_revision'] != expected['source_revision']:
                raise ValueError('Case commit/revision differs from frozen source cohort')
            if case.get('source_kind') == 'aidev' and case['head'] != expected.get('upstream_head'):
                raise ValueError('AIDev head differs from frozen upstream commit')
        hashes = locked["cases"][identity]
        if sha256(ROOT / "cases" / identity / "case.json") != hashes["case_sha256"]:
            raise ValueError("Frozen case changed: " + identity)
        for field in ("repair_patch", "test_patch"):
            if sha256(ROOT / case[field]) != hashes[field + "_sha256"]:
                raise ValueError("Frozen patch changed: " + identity)
    return plan


def ordered_cases(plan):
    pools = {role: [row for row in plan["selected"] if row["role"] == role]
             for role in ("train", "validation", "test")}
    for index in range(max(map(len, pools.values()), default=0)):
        for role in pools:
            if index < len(pools[role]):
                yield pools[role][index]


def summary(experiment, plan):
    state = read_json(experiment.manifest)
    totals = {role: Counter(selected=sum(r["role"] == role for r in plan["selected"]))
              for role in ("train", "validation", "test")}
    sources = {role: {key: set() for key in ("attempted_source_cases", "strict_reproduced", "seed_pass")}
               for role in totals}
    for operation, record in state.get("operations", {}).items():
        if not operation.startswith("real-"):
            continue
        artifacts = record.get("artifacts", {})
        case = case_config(artifacts.get("case_id", operation.removeprefix("real-")))
        role, identity = case["experiment_role"], case["source_case_id"]
        counts = totals[role]
        counts["attempted"] += 1
        counts[record["status"]] += 1
        result = record.get("result") or {}
        sources[role]["attempted_source_cases"].add(identity)
        for field, flag in (("strict_reproduced", "historical_supported"), ("seed_pass", "head_passed")):
            if result.get(flag):
                sources[role][field].add(identity)
    for role in totals:
        totals[role].update({key: len(values) for key, values in sources[role].items()})
    result = {"updated_at": now(), "plan_sha256": plan.get("_locked_plan_sha256"),
              "by_role": {role: dict(counts) for role, counts in totals.items()},
              "qualification": "Reconstruction counts, not finalized silver labels or training eligibility"}
    write_json(experiment.folder / "real-reproduction-summary.json", result)
    return result


def reproduce(experiment, plan, *, limit=None):
    from .data_study import DataStudy
    processed = 0
    with batch_lock(experiment.folder / "reproduction-worker.lock"):
        uncertain = [name for name, record in read_json(experiment.manifest).get("operations", {}).items()
                     if name.startswith("real-") and record["status"] == "reserved"]
        if uncertain:
            raise RuntimeError("Uncertain interrupted reconstruction; inspect before any new profile: " + ", ".join(uncertain))
        for row in ordered_cases(plan):
            operation = "real-" + row["case_id"]
            previous = read_json(experiment.manifest).get("operations", {}).get(operation)
            if previous:
                if previous["status"] == "reserved":
                    raise RuntimeError("Uncertain interrupted operation; inspect artifacts, do not replay: " + operation)
                continue
            counts = summary(experiment, plan)["by_role"][row["role"]]
            # V2 still needs fault curation, deduplication and class/repository quotas.
            if not isinstance(experiment, DataStudy) and counts.get("strict_reproduced", 0) >= plan["targets"][row["role"]]:
                continue
            state = read_json(experiment.manifest)
            if any((r.get("result") or {}).get("historical_supported") and
                   case_config(r["artifacts"]["case_id"])["source_case_id"] == row["source_case_id"]
                   for name, r in state.get("operations", {}).items() if name.startswith("real-")):
                continue
            if isinstance(experiment, DataStudy):
                profiles = [r for name, r in state.get('operations', {}).items() if name.startswith('real-')
                            and case_config(r['artifacts']['case_id'])['source_case_id'] == row['source_case_id']]
                if len(profiles) >= 2:
                    raise BudgetStop('Only one environment correction is allowed per source case')
                if profiles:
                    correction = case_config(row['case_id'])
                    reason = correction.get('environment_correction')
                    if (correction.get('profile_parent_case_id') != profiles[0]['artifacts']['case_id']
                            or not isinstance(reason, str) or not reason.strip()):
                        raise ValueError('Environment correction needs its exact parent and recorded reason')
            if limit is not None and processed >= limit:
                break
            experiment.reserve(operation, "real_reproduction", timeout=1200)
            folder = new_run("reproduce")
            experiment.attach(operation, run_id=folder.name, case_id=row["case_id"], role=row["role"])
            experiment.attach(operation, implementation_sha256=sha256(multicase.__file__))
            if isinstance(experiment, DataStudy):
                from . import data_study, source_roles
                experiment.attach(operation, budget_guard_sha256=sha256(data_study.__file__),
                                  orchestration_sha256=sha256(__file__),
                                  source_role_policy_sha256=sha256(source_roles.__file__))

            def guard(name):
                timeout = 1200 if name == "docker-build" else 300 if name.startswith("historical-") else 180
                if isinstance(experiment, DataStudy) and name != 'docker-build' and not name.startswith('historical-'):
                    experiment.check_prepare_step(timeout=timeout)
                else:
                    experiment.check("real_reproduction", timeout=timeout)

            print(row["role"], row["case_id"], folder.name, "started", flush=True)
            try:
                result = multicase.reproduce_case(case_config(row["case_id"]), folder, guard)
                experiment.finish(operation, "finished", result={"run_id": folder.name, "role": row["role"],
                    "status": result["status"], "historical_supported": result.get("historical_supported", False),
                    "head_passed": result.get("head_passed", False), "error": result.get("error")})
            except Exception as exc:
                experiment.finish(operation, "failed", result={"run_id": folder.name, "role": row["role"]}, error=str(exc))
                summary(experiment, plan)
                raise
            processed += 1
            summary(experiment, plan)
            print(row["case_id"], result["status"], result.get("error", ""), flush=True)
    return summary(experiment, plan)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, help="Maximum new cases this invocation; completed cases are skipped")
    parser.add_argument("--plan", default="data-manifests/dataset-v1-plan.json", help="Explicit immutable source/profile plan")
    parser.add_argument('--study-v2', action='store_true', help='Use the separate dataset-v2 study and limits')
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")
    if args.study_v2:
        from .data_study import DataStudy
        from .common import CACHE
        experiment = DataStudy(read_json(CACHE / 'dataset-v2-active.json')['run_id'])
    else:
        experiment = active_experiment()
    with batch_lock(experiment.lock, wait_seconds=experiment.metadata_lock_wait_seconds):
        plan = freeze_plan(experiment, ROOT / args.plan)
    plan["_locked_plan_sha256"] = sha256(ROOT / args.plan)
    try:
        print(reproduce(experiment, plan, limit=args.limit), flush=True)
    except BudgetStop as exc:
        write_json(experiment.folder / "budget-stop.json", {"recorded_at": now(), "error": str(exc)})
        print(str(exc), flush=True)


if __name__ == "__main__":
    main()
