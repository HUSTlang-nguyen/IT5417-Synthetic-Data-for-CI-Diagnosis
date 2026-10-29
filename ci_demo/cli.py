"""Command-line entry point; run from the repository root."""
from __future__ import annotations
import argparse
import os
import sys
from . import ollama
from .pipeline import doctor, generate_run, reproduce, verify_run
from .report import report_run

def main(argv=None):
    parser = argparse.ArgumentParser(description="IT5417: real-repository CI data evidence")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("doctor")
    check.add_argument("--endpoint", default=os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434"))
    check.add_argument("--target-gpu", default="RTX 4070 SUPER")
    repro = sub.add_parser("reproduce")
    repro.add_argument("--case", default="properr-6")
    gen = sub.add_parser("generate")
    gen.add_argument("--case", default="properr-6")
    gen.add_argument("--model", required=True, choices=[ollama.GENERATOR_MODEL])
    gen.add_argument("--attempts", type=int, default=3, choices=[3])
    gen.add_argument("--endpoint", default=os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434"))
    for name in ("verify", "report"):
        sub.add_parser(name).add_argument("--run", required=True)
    batch = sub.add_parser("batch")
    mode = batch.add_mutually_exclusive_group(required=True)
    mode.add_argument("--manifest")
    mode.add_argument("--resume", metavar="BATCH-ID")
    batch.add_argument("--endpoint", default=os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434"))
    args = parser.parse_args(argv)
    try:
        if args.command == "report":
            print(report_run(args.run))
            return 0
        if args.command == "doctor":
            manifest = doctor(args.endpoint, args.target_gpu)
            print("target_gpu_matches:", manifest["target_gpu_matches"])
            print("ollama_available:", manifest["checks"]["ollama"]["ok"])
        elif args.command == "reproduce":
            manifest = reproduce(args.case)
        elif args.command == "generate":
            manifest = generate_run(args.model, args.attempts, args.endpoint, args.case)
        elif args.command == "batch":
            from .batch import run_batch
            manifest = run_batch(args.manifest, args.resume, args.endpoint)
        else:
            manifest = verify_run(args.run)
        print("run:", manifest["run_id"])
        print("status:", manifest.get("status", "doctor_finished"))
        print("report:", report_run(manifest["run_id"]))
        if manifest.get("error"): print("error:", manifest["error"], file=sys.stderr)
        return 1 if manifest.get("status") in {"environment_error", "hypothesis_not_confirmed", "batch_incomplete", "batch_stopped"} else 0
    except (OSError, RuntimeError, ValueError) as exc:
        print("ERROR:", str(exc), file=sys.stderr)
        return 1
