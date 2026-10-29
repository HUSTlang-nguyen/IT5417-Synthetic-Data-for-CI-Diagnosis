"""Run the 7B generator demo on the target PC; diagnosis is a later stage."""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ci_demo.common import new_run, successful
from ci_demo.ollama import GENERATOR_MODEL
from ci_demo.pipeline import doctor
from ci_demo.session import save_session


class StageError(RuntimeError):
    def __init__(self, args, run_id):
        super().__init__("Stage failed: " + " ".join(args))
        self.run_id = run_id


def cli(*args):
    result = subprocess.run([sys.executable, "-m", "ci_demo", *args], cwd=ROOT, text=True,
                            capture_output=True, encoding="utf-8", errors="replace")
    print(result.stdout, end="", flush=True)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    run_id = next((line[5:].strip() for line in result.stdout.splitlines() if line.startswith("run: ")), None)
    if result.returncode:
        raise StageError(args, run_id)
    return run_id


def main():
    parser = argparse.ArgumentParser(description="Target-PC 7B generator demo (diagnosis not implemented)")
    parser.add_argument("--pull-models", action="store_true", help="Download only the configured 7B generator")
    parser.add_argument("--skip-reproduce", action="store_true", help="Use an already verified local passing seed")
    args = parser.parse_args()
    folder = new_run("demo")
    generation_run = doctor_run = reproduction_run = error = None
    operation = "doctor"
    save_session(folder)
    print("Demo:", folder / "report.html", flush=True)
    try:
        checks = doctor("http://127.0.0.1:11434")
        doctor_run = checks["run_id"]
        save_session(folder, doctor_run=doctor_run)
        cli("report", "--run", doctor_run)
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
            operation = "pull"
            subprocess.run(["ollama", "pull", GENERATOR_MODEL], check=True)
        if not args.skip_reproduce:
            operation = "reproduce"
            reproduction_run = cli("reproduce", "--case", "properr-6")
            if not reproduction_run:
                raise RuntimeError("Missing reproduction run ID")
            save_session(folder, reproduction_run=reproduction_run)
        operation = "generate"
        generation_run = cli("generate", "--model", GENERATOR_MODEL, "--attempts", "3")
        if not generation_run:
            raise RuntimeError("Missing generation run ID")
        save_session(folder, generation_run=generation_run)
        operation = "verify"
        cli("verify", "--run", generation_run)
    except StageError as exc:
        error = str(exc)
        if operation == "generate":
            generation_run = exc.run_id
        elif operation == "reproduce":
            reproduction_run = exc.run_id
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
        error = str(exc)
    finally:
        summary = save_session(folder, generation_run=generation_run, doctor_run=doctor_run,
                               reproduction_run=reproduction_run, error=error, finished=True)
        print("Demo:", folder / "report.html", flush=True)
    if summary["status"] != "demo_finished":
        raise RuntimeError("Demo incomplete; see the saved report. " + (error or "Verification did not finish."))


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
        print("ERROR:", exc, file=sys.stderr)
        raise SystemExit(1)
