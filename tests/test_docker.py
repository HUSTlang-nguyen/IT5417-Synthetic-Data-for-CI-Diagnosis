"""Opt-in runner integration, with a hand-written FIXTURE, never model evidence."""
import os
from pathlib import Path
import unittest
from ci_demo import runner
from ci_demo.common import CACHE, case_config, now, successful, write_json
from ci_demo.pipeline import passing_seed


@unittest.skipUnless(os.getenv("CI_DEMO_DOCKER_TESTS") == "1", "Set CI_DEMO_DOCKER_TESTS=1 after reproduce")
class DockerIntegrationTests(unittest.TestCase):
    def test_real_container_pass_fail_fail_fail_pass(self):
        case = case_config()
        _, source = passing_seed(case)
        from datetime import datetime, timezone
        folder = CACHE / "runner-check" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        folder.mkdir(parents=True)
        original = (source / case["allowed_file"]).read_text(encoding="utf-8")
        self.assertIn("nominal = _rust.nominal", original)
        candidate = folder / "fixture.py"
        candidate.write_text(original.replace("nominal = _rust.nominal", "nominal = lambda value: _rust.nominal(value) + 1"), encoding="utf-8")
        baseline = runner.execute(case, folder, "baseline")
        repetitions = [runner.execute(case, folder, "fixture-" + str(i), candidate=candidate) for i in range(1, 4)]
        restored = runner.execute(case, folder, "restored")
        accepted = runner.accepted(baseline, repetitions, restored, folder)
        write_json(folder / "test-summary.json", {
            "kind": "software_integration_fixture_NOT_model_generation", "recorded_at": now(),
            "accepted": accepted, "baseline": baseline, "repetitions": repetitions,
            "restored": restored, "research_attempt_count": 0,
        })
        self.assertTrue(successful(baseline))
        self.assertTrue(all(r["exit_code"] == 1 for r in repetitions))
        self.assertTrue(all("junit" in r for r in [baseline, *repetitions, restored]))
        self.assertTrue(all(r["container_removed"] for r in [baseline, *repetitions, restored]))
        self.assertTrue(accepted)


if __name__ == "__main__":
    unittest.main()
