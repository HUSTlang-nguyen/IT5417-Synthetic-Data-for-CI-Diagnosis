"""Create a derived lineage snapshot from finished runs without models or Docker."""
from pathlib import Path
import argparse
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ci_demo.curation import audit_cohorts
from ci_demo.common import write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", action="append", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output).resolve()
    if not output.is_relative_to((ROOT / "data-manifests").resolve()):
        raise ValueError("Derived lineage output must stay under data-manifests")
    result = audit_cohorts(args.cohort); write_json(output, result)
    print("Source records:", result["source_case_records"], "profiles:", result["profile_records"],
          "groups:", len(result["groups"]), "attempts:", len(result["attempts"]))


if __name__ == "__main__": main()
