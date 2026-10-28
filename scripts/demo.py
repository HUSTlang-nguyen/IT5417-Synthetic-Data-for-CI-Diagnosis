"""Run the two documented models sequentially on the target PC."""
from __future__ import annotations
import argparse
from html import escape
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ci_demo.common import new_run, now, write_json, successful
from ci_demo.ollama import MODELS
from ci_demo.pipeline import doctor

def cli(*args):
    result = subprocess.run([sys.executable, "-m", "ci_demo", *args], cwd=ROOT, text=True,
                            capture_output=True, encoding="utf-8", errors="replace")
    print(result.stdout, end="", flush=True)
    if result.stderr: print(result.stderr, file=sys.stderr)
    if result.returncode: raise RuntimeError("Stage failed: " + " ".join(args))
    run_id = next((line[5:].strip() for line in result.stdout.splitlines() if line.startswith("run: ")), None)
    return run_id

def main():
    parser = argparse.ArgumentParser(description="Target-PC demo runner (real local models only)")
    parser.add_argument("--pull-models", action="store_true", help="Download the two models through installed Ollama")
    parser.add_argument("--skip-reproduce", action="store_true", help="Use an already verified local passing seed")
    args = parser.parse_args()
    checks = doctor("http://127.0.0.1:11434")
    if not successful(checks["checks"]["docker"]) or checks["checks"]["docker"].get("server_os") != "linux":
        raise RuntimeError("Start Docker with its Linux engine before running the demo.")
    if not checks["checks"]["ollama"]["ok"]:
        raise RuntimeError("Install/start Ollama first: https://ollama.com/download/windows")
    if not checks["target_gpu_matches"]:
        raise RuntimeError("This helper targets RTX 4070 SUPER. Use individual CLI commands for laptop development checks.")
    if args.pull_models:
        for model in MODELS: subprocess.run(["ollama", "pull", model], check=True)
    if not args.skip_reproduce: cli("reproduce", "--case", "properr-6")
    results = []
    for model in MODELS:
        run_id = cli("generate", "--model", model, "--attempts", "3")
        if not run_id: raise RuntimeError("Missing generation run ID")
        cli("verify", "--run", run_id)
        cli("report", "--run", run_id)
        manifest = json.loads((ROOT / "runs" / run_id / "manifest.json").read_text(encoding="utf-8"))
        results.append({"model": model, "run_id": run_id, "status": manifest["status"],
                        "requested": manifest["attempt_count"],
                        "execution_verified": sum(a["status"] == "execution_verified" for a in manifest["attempts"]),
                        "attempts": manifest["attempts"]})
    summary_dir = new_run("comparison")
    summary = {"kind": "pilot_comparison", "run_id": summary_dir.name, "created_at": now(),
               "models": results, "human_review": "pending", "not_training_evaluation": True}
    write_json(summary_dir / "manifest.json", summary)
    rows = "".join("<tr><td>" + escape(r["model"]) + "</td><td>" + str(r["execution_verified"]) + "/" + str(r["requested"])
                   + '</td><td><a href="../' + r["run_id"] + '/report.html">Artifact đã lưu</a></td></tr>' for r in results)
    (summary_dir / "report.html").write_text('<!doctype html><meta charset="utf-8"><h1>So sánh pilot hai model sinh</h1>'
        '<p>Kết quả đã lưu, không phải live. Nhãn chờ người duyệt. Cùng một seed không đủ kết luận tổng quát hoặc hiệu quả huấn luyện.</p>'
        '<table border="1"><tr><th>Model</th><th>Đạt kiểm tra thực thi/tổng lượt</th><th>Báo cáo</th></tr>'
        + rows + '</table>', encoding="utf-8")
    print("Comparison:", summary_dir / "report.html")

if __name__ == "__main__":
    try: main()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print("ERROR:", exc, file=sys.stderr)
        raise SystemExit(1)
