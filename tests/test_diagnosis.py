"""Software fixtures only; these are not research observations or synthetic data."""
from pathlib import Path
import tempfile
import unittest

from ci_demo.diagnosis import evaluate, failure_log, functions, retrieve


class DiagnosisTests(unittest.TestCase):
    def test_candidate_overlay_cannot_add_files_or_escape_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.py").write_text("def f():\n    return 1\n")
            for overlay in ({"../escape.py": "text"}, {"missing.py": "text"}, {"a.py": 42}):
                with self.assertRaises(ValueError):
                    retrieve(root, "f", source_overrides=overlay)

    def test_retrieval_ignores_pass_progress_and_can_retrieve_module_registry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "render.py").write_text("mapping = {'Abs': 'abs'}\n\ndef unrelated():\n    return 1\n")
            (root / "noise.py").write_text("def chatter():\n    return 'noise ' * 10\n")
            log = ("noise " * 1000 + "\n================ FAILURES ================\n"
                   "test_render.py:5: AssertionError: mapping missing Min\n"
                   "================ short test summary info ================\nmore noise")
            self.assertNotIn("noise", failure_log(log))
            snippets = retrieve(root, log)["snippets"]
            self.assertEqual((snippets[0]["file"], snippets[0]["function"]), ("render.py", "<module>"))

    def test_retrieval_uses_observed_stack_not_test_or_reference_location(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "library.py").write_text("def first():\n    return 1\n\ndef second():\n    return 2\n")
            (root / "test_leak.py").write_text("def answer():\n    return 1\n")
            result = retrieve(root, 'File "/source/base/library.py", line 5, in second\nTypeError')
            self.assertEqual(result["snippets"][0]["function"], "second")
            self.assertTrue(all(s["file"] == "library.py" for s in result["snippets"]))

    def test_qualified_functions_are_parsed_without_execution(self):
        source = "raise RuntimeError('must not execute')\nclass C:\n    async def method(self):\n        return 1\n"
        self.assertEqual(functions(source), [("C.method", 3, 4)])

    def test_invalid_and_retrieval_miss_stay_in_localization_denominator(self):
        refs = [{"sample_id": str(i), "cause_type": "API/type", "locations": [{"file": "a.py", "function": "f"}],
                 "retrieved_locations": []} for i in range(3)]
        predictions = {"0": {"cause_type": "API/type", "locations": [{"file": "a.py", "function": "f"}], "explanation": "x"},
                       "1": {"cause_type": "API/type", "locations": [], "explanation": "x"}}
        result = evaluate(refs, predictions)
        self.assertEqual(result["counts"]["localization_eligible"], 3)
        self.assertEqual(result["function_top1"], 0)
        self.assertEqual(result["joint_top1"], 0)
        self.assertEqual(result["retrieval_function_coverage"], 0)
        self.assertEqual(result["counts"]["invalid_output"], 1)

    def test_class_correct_does_not_mask_wrong_function(self):
        ref = {"sample_id": "a", "cause_type": "logic/value", "locations": [{"file": "a.py", "function": "cause"}],
               "retrieved_locations": [{"file": "a.py", "function": "cause"}]}
        pred = {"cause_type": "logic/value", "locations": [{"file": "a.py", "function": "detection"}], "explanation": "x"}
        result = evaluate([ref], {"a": pred})
        self.assertEqual(result["classification_accuracy"], 1)
        self.assertEqual(result["file_top1"], 1)
        self.assertEqual(result["function_top1"], 0)
        self.assertEqual(result["joint_top1"], 0)

    def test_unknown_refs_not_silently_treated_as_gold_and_duplicate_ids_rejected(self):
        result = evaluate([{"sample_id": "a", "cause_type": "unknown", "locations": []}], {})
        self.assertIsNone(result["joint_top1"])
        self.assertIsNone(result["macro_f1"])
        with self.assertRaises(ValueError):
            evaluate([{"sample_id": "a"}, {"sample_id": "a"}], {})

    def test_multiple_reference_locations_report_recall_and_bad_path_invalid(self):
        ref = {"sample_id": "a", "cause_type": "logic/value", "locations": [
            {"file": "a.py", "function": "f"}, {"file": "b.py", "function": "g"}],
            "retrieved_locations": [{"file": "a.py", "function": "f"}, {"file": "b.py", "function": "g"}]}
        pred = {"cause_type": "logic/value", "locations": [{"file": "a.py", "function": "f"}], "explanation": "x"}
        result = evaluate([ref], {"a": pred})
        self.assertEqual(result["function_top1"], 1)
        self.assertEqual(result["function_recall_at1"], .5)
        pred["locations"].append({"file": "../escape.py", "function": "f"})
        result = evaluate([ref], {"a": pred})
        self.assertEqual(result["counts"]["invalid_output"], 1)
        self.assertEqual(result["function_top1"], 0)


if __name__ == "__main__":
    unittest.main()
