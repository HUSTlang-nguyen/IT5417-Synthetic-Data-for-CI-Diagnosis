"""Inert software fixtures, not research runs, model outputs or CI observations."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ci_demo import dataset, multicase, ollama
from ci_demo.common import read_json, sha256, write_json
from tests.test_multicase import config


class SyntheticDatasetTests(unittest.TestCase):
    def fixture(self, root):
        case = {**config("fixture"), "experiment_role": "train", "source_case_id": "source-fixture"}
        original = "def cause(x):\n    return x + 1\n"
        changed = original.replace("x + 1", "x - 1")
        source = root / "context/head/package/api.py"
        source.parent.mkdir(parents=True)
        source.write_text(original)
        generated = root / "generate-fixture"
        verified = root / "verify-fixture"
        candidate = generated / "attempt-01"
        candidate.mkdir(parents=True)
        (generated / "original.py").write_text(original)
        (candidate / "candidate.py").write_text(changed)
        proposal = {"path": case["allowed_file"], "site_id": "1", "replacement": "return x - 1", "explanation": "SECRET_GENERATOR_EXPLANATION"}
        write_json(candidate / "proposal.json", proposal)
        write_json(candidate / "allowed-sites.json", [{"site_id": "1", "line": 2, "source": "return x + 1"}])
        for name in ("change.diff", "prompt.txt", "request.json", "response.raw.json"):
            (candidate / name).write_text("inert software fixture")
        gate = {"head_passed": True, "case_id": case["case_id"], "context": str(root / "context"),
            "case_hash": hashlib.sha256(json.dumps(case, sort_keys=True).encode()).hexdigest()[:16],
            "source_hash": sha256(source), "inventories": {"head": multicase.inventory(root / "context/head")},
            "image_id": "sha256:fixture", "reproduction_run": "reproduce-fixture"}

        def result(folder, name, failed=False):
            folder.mkdir(parents=True, exist_ok=True)
            (folder / (name + ".stdout.txt")).write_text('File "/source/head/package/api.py", line 2\nAssertionError fixture' if failed else "fixture pass")
            (folder / (name + ".stderr.txt")).write_text("")
            (folder / (name + ".xml")).write_text('<testsuite><testcase classname="tests.test_api" name="test_bug">' +
                ('<failure message="fixture wrong value"/>' if failed else '') + '</testcase></testsuite>')
            return {"exit_code": int(failed), "timed_out": False, "container_removed": True,
                "command": ["docker", "run", "--network=none", "--read-only", "--user", "65534:65534", "--cap-drop=ALL", "--security-opt=no-new-privileges", gate["image_id"]],
                "stdout": name + ".stdout.txt", "stderr": name + ".stderr.txt", "junit": name + ".xml"}

        seed_folder = root / "reproduce-fixture"
        write_json(seed_folder / "manifest.json", {"source": case, "environment": gate, "head_passed": True,
            "head": result(seed_folder, "head")})
        attempt = {"index": 1, "directory": "attempt-01", "candidate_sha256": sha256(candidate / "candidate.py"), "status": "awaiting_verification"}
        other = [{"index": i, "directory": f"attempt-{i:02}", "status": "invalid_output"} for i in (2, 3)]
        write_json(generated / "manifest.json", {"run_id": generated.name, "source": case, "passing_seed": gate,
            "reproduction_run": seed_folder.name, "model": ollama.GENERATOR_MODEL, "protocol": multicase.SITE_PROTOCOL,
            "kind": "synthetic_generation", "attempt_count": 3, "status": "generation_finished", "attempts": [attempt, *other]})
        evidence = verified / "attempt-01"
        accepted = {**attempt, "status": "execution_verified", "baseline": result(evidence, "baseline"),
            "repetitions": [result(evidence, f"candidate-{i}", True) for i in (1, 2, 3)], "restored": result(evidence, "restored")}
        write_json(verified / "manifest.json", {"kind": "synthetic_verification", "status": "verification_finished",
            "source": case, "model": ollama.GENERATOR_MODEL, "attempt_count": 3, "generation_run": generated.name, "attempts": [accepted, *other]})
        return generated, verified, candidate

    def test_saved_chain_overlay_exports_no_generator_or_reference_answer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            generated, verified, candidate = self.fixture(root)
            with patch.object(dataset, "ROOT", root), patch.object(dataset, "run_path", side_effect=lambda rid: root / rid):
                _, _, _, hashes = dataset.synthetic_evidence(verified.name, 1)
                assessment = {"run_id": verified.name, "attempt_index": 1, "evidence_hashes": hashes,
                    "quality": "silver", "disposition": "include", "cause_type": "logic/value", "confidence": "high",
                    "locations": [{"file": "package/api.py", "function": "cause"}], "mechanism": "SECRET_REFERENCE_EXPLANATION",
                    "evidence_reason": "inert fixture", "limitations": "software fixture only", "label_source": "fixture",
                    "prompt_compliance": "pass", "plausibility": "qualified", "input_leakage_review": "fixture boundary check"}
                write_json(root / "assessment.json", assessment)
                meta = dataset.export_synthetic(verified.name, 1, root / "assessment.json", root / "output")
                text = (root / "output/input.json").read_text()
                self.assertIn("return x - 1", text)
                self.assertNotIn("SECRET_", text)
                self.assertNotIn("site_id", text)
                self.assertEqual((root / "context/head/package/api.py").read_text(), (generated / "original.py").read_text())
                self.assertEqual(meta["origin"], "controlled_synthetic")
                self.assertEqual(meta["role"], "train")
                from ci_demo.retrieval_v3 import retrieve_balanced
                updated = dataset.export_synthetic(verified.name, 1, root / "assessment.json", root / "v3-output", retriever=retrieve_balanced)
                self.assertEqual(updated["retrieval"]["method"], "balanced_source_excerpts_v3")
                self.assertIn("return x - 1", (root / "v3-output/input.json").read_text())
                self.assertNotIn("SECRET_", (root / "v3-output/input.json").read_text())
                with self.assertRaises(ValueError):
                    dataset.export_synthetic(verified.name, 1, root / "assessment.json", root / "output")
                (candidate / "candidate.py").write_text("tampered fixture")
                with self.assertRaises(ValueError):
                    dataset.synthetic_evidence(verified.name, 1)

    def test_heldout_generation_and_unsafe_execution_are_rejected(self):
        for change in ("heldout", "network", "unstable", "denominator", "syntax"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                generated, verified, _ = self.fixture(root)
                raw = read_json(verified / "manifest.json")
                if change == "heldout":
                    gen = read_json(generated / "manifest.json")
                    gen["source"]["experiment_role"] = "test"
                    write_json(generated / "manifest.json", gen)
                elif change == "network":
                    raw["attempts"][0]["repetitions"][0]["command"].remove("--network=none")
                elif change == "unstable":
                    (verified / "attempt-01/candidate-2.xml").write_text('<testsuite><testcase name="other"><failure message="different"/></testcase></testsuite>')
                elif change == "syntax":
                    candidate = generated / "attempt-01/candidate.py"
                    candidate.write_text("def cause(x):\n    return (\n")
                    proposal_path = generated / "attempt-01/proposal.json"
                    proposal = read_json(proposal_path)
                    proposal["replacement"] = "return ("
                    write_json(proposal_path, proposal)
                    gen = read_json(generated / "manifest.json")
                    gen["attempts"][0]["candidate_sha256"] = sha256(candidate)
                    raw["attempts"][0]["candidate_sha256"] = sha256(candidate)
                    write_json(generated / "manifest.json", gen)
                else:
                    raw["attempts"].pop()
                write_json(verified / "manifest.json", raw)
                with patch.object(dataset, "ROOT", root), patch.object(dataset, "run_path", side_effect=lambda rid: root / rid):
                    with self.assertRaises(ValueError):
                        dataset.synthetic_evidence(verified.name, 1)

    def test_selected_audit_checks_review_and_raw_hashes_and_detects_duplicate_edits(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); generated,verified,_=self.fixture(root)
            with patch.object(dataset,'ROOT',root), patch.object(dataset,'CACHE',root/'cache'), \
                 patch.object(dataset,'run_path',side_effect=lambda rid:root/rid):
                _,_,_,hashes=dataset.synthetic_evidence(verified.name,1)
                assessment={'run_id':verified.name,'attempt_index':1,'evidence_hashes':hashes,
                    'quality':'silver','disposition':'include','cause_type':'logic/value','confidence':'high',
                    'locations':[{'file':'package/api.py','function':'cause'}],'mechanism':'inert fixture cause',
                    'evidence_reason':'inert fixture','limitations':'software fixture','label_source':'fixture',
                    'prompt_compliance':'pass','plausibility':'supported','input_leakage_review':'fixture boundary'}
                write_json(root/'assessment.json',assessment)
                first=root/'cache/dataset-v1/one'; second=root/'cache/dataset-v1/two'
                dataset.export_synthetic(verified.name,1,root/'assessment.json',first)
                dataset.export_synthetic(verified.name,1,root/'assessment.json',second)
                audit=dataset.audit_selected_exports([first])
                self.assertEqual(len(audit['records']),1)
                self.assertEqual(audit['cross_split_groups'],[])
                self.assertEqual(audit['records'][0]['group_id'],'repo:example/fixture')
                with self.assertRaises(ValueError):dataset.audit_selected_exports([first,second])
                changed=read_json(first/'assessment.json'); changed['mechanism']='altered'
                write_json(first/'assessment.json',changed)
                with self.assertRaises(ValueError):dataset.audit_selected_exports([first])
                write_json(first/'assessment.json',assessment)
                (verified/'attempt-01/candidate-1.stdout.txt').write_text('changed raw fixture')
                with self.assertRaises(ValueError):dataset.audit_selected_exports([first])


if __name__ == "__main__":
    unittest.main()
