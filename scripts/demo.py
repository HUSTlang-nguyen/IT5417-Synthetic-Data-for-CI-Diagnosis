"""Run the two documented models sequentially on the target PC."""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ci_demo.common import new_run, read_json, successful
from ci_demo.comparison import save_comparison
from ci_demo.ollama import MODELS
from ci_demo.pipeline import doctor

def cli(*args, allow_failure=False):
    result = subprocess.run([sys.executable, "-m", "ci_demo", *args], cwd=ROOT, text=True,
                            capture_output=True, encoding="utf-8", errors="replace")
    print(result.stdout, end="", flush=True)
    if result.stderr: print(result.stderr, file=sys.stderr)
    run_id = next((line[5:].strip() for line in result.stdout.splitlines() if line.startswith("run: ")), None)
    if result.returncode and not (allow_failure and run_id):
        raise RuntimeError("Stage failed: " + " ".join(args))
    return run_id

def main():
    parser = argparse.ArgumentParser(description="Target-PC demo runner (real local models only)")
    parser.add_argument("--pull-models", action="store_true", help="Download the two models through installed Ollama")
    parser.add_argument("--skip-reproduce", action="store_true", help="Use an already verified local passing seed")
    args = parser.parse_args()
    summary_dir = new_run("comparison")
    run_ids, errors = [], []
    doctor_run = None
    print("Comparison:", summary_dir / "report.html")
    save_comparison(folder=summary_dir, finished=False)
    try:
        checks = doctor("http://127.0.0.1:11434")
        doctor_run = checks["run_id"]
        cli("report", "--run", doctor_run)
        save_comparison(folder=summary_dir, doctor_run=doctor_run, finished=False)
        prerequisites = []
        if not successful(checks["checks"]["docker"]) or checks["checks"]["docker"].get("server_os") != "linux":
            prerequisites.append("Start Docker with its Linux engine.")
        if not checks["checks"]["ollama"]["ok"]:
            prerequisites.append("Install/start Ollama: https://ollama.com/download/windows")
        if not checks["target_gpu_matches"]:
            prerequisites.append("This helper targets RTX 4070 SUPER; use individual CLI commands for laptop checks.")
        if prerequisites:
            raise RuntimeError(" ".join(prerequisites))
        if args.pull_models:
            for model in MODELS:
                subprocess.run(["ollama", "pull", model], check=True)
        if not args.skip_reproduce:
            cli("reproduce", "--case", "properr-6")
        for model in MODELS:
            try:
                run_id = cli("generate", "--model", model, "--attempts", "3", allow_failure=True)
                if not run_id:
                    raise RuntimeError("Missing generation run ID for " + model)
                run_ids.append(run_id)
                save_comparison(run_ids, folder=summary_dir, doctor_run=doctor_run, finished=False)
                manifest = read_json(ROOT / "runs" / run_id / "manifest.json")
                if manifest["status"] == "generation_finished":
                    cli("verify", "--run", run_id, allow_failure=True)
                else:
                    errors.append(model + ": " + manifest.get("error", manifest["status"]))
            except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
                errors.append(model + ": " + str(exc))
            save_comparison(run_ids, folder=summary_dir, doctor_run=doctor_run, error="; ".join(errors) or None,
                            finished=False)
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        errors.append(str(exc))
    finally:
        summary = save_comparison(run_ids, folder=summary_dir, doctor_run=doctor_run,
                                  error="; ".join(errors) or None)
        print("Comparison:", summary_dir / "report.html")
    if summary["status"] != "comparison_finished" or errors:
        raise RuntimeError("Demo incomplete; see the saved comparison report. " + "; ".join(errors))

if __name__ == "__main__":
    try: main()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print("ERROR:", exc, file=sys.stderr)
        raise SystemExit(1)
