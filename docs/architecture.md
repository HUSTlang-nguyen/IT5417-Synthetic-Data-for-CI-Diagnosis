# Architecture and context checkpoint

## Objective

Study whether execution-verified synthetic data helps CI error diagnosis in human-agent collaboration. The first milestone is a reproducible real-repository demo, not model training or a general benchmark.

## Current implementation status

CLI, Docker runner, Ollama adapter and Vietnamese HTML reports implemented. Real laptop reproduction: base missing pytest (exit 1), head 2 tests pass (exit 0). All 14 software tests pass, including actual Docker fixture integration. No LLM generation or target-PC validation has run. See docs/evidence/README.md and latest agent-log before resuming.

## Components and data flow

Repository: https://github.com/HUSTlang-nguyen/IT5417-Synthetic-Data-for-CI-Diagnosis (private), main; origin is the matching HTTPS Git URL. Files live in the renamed child folder inside the original workspace. Original parent slides/research documents remain outside the new repository.

Python CLI -> pinned case preparation -> Docker image -> historical reproduction -> passing head seed -> Ollama generation -> candidate validation -> Docker baseline/three candidate repetitions/restoration -> HTML report and manual label review.

- cli: commands doctor, reproduce, generate, verify, report.
- sources: fetch exact Git commits and export source snapshots.
- runner: immutable tests, no-network unprivileged containers with timeout/resource limits.
- ollama: local /api/chat JSON-schema outputs; store raw responses, digest, configuration and timing.
- pipeline: manifests and state transitions; invalid attempts remain in denominators.
- report: escaped, offline-readable Vietnamese HTML with raw artifact links.

## Persistent state

- cases/properr-6/case.json: source identity and exact revisions.
- .cache/: ignored source checkout, exported sources, Docker build context and environment evidence.
- runs/<run-id>/: ignored immutable input/output evidence, per-command logs, JSON manifest, review stub and report.
- docs/evidence/: small committed summaries and selected actual textual logs, without vendor code/model weights.
- docs/agent-log.md: append-only chronology.
- This file: current architecture, decisions, limitations and resumption instructions.

## Fixed decisions

- No cloud API/key required. Target models: qwen2.5-coder:7b-instruct and qwen2.5-coder:1.5b-instruct, sequential, three attempts each, matching prompt/options.
- Source base eff739a28971a66a36d443bfde91c515f7a858ea; head 8fd30245ed66b5145d651efc9203eb9a911e95d5.
- Source has a Rust extension; the orchestrator is Python. Python 3.11 matches the recorded CI workflow.
- Historical reproduction tests the original missing-pytest installation distinction, without preinstalling pytest in the base environment.
- Synthetic generation edits only properr/__init__.py at passing head. Original tests remain unchanged.
- Execution acceptance is pass -> repeated fail -> restored pass; cause/location labels stay pending human review.
- The PC target cannot be declared tested from laptop-only evidence.
- Docker toolchain: Debian Bookworm Python 3.11, Rust 1.85, maturin 1.7.8, pytest 8.3.5. Image ID/build logs saved. Base image tags/apt are not fully hermetic locks; rebuilds can differ.
- Verification mounts only candidate read-only and fresh JUnit output writable; source/tests/manifests never mounted writable. Output mount preserves JUnit after container termination; /tmp stays tmpfs.
- Stable failures: same JUnit test identity, failure kind and assertion message in all three repetitions. Only repr memory addresses (` at 0x...`) are normalized; assertion values remain significant.

## Configuration, commands and state

Run from repository root with Python >=3.11; standard library only. Optional `python -m pip install -e .`; documented python -m commands need no installation. Case is cases/properr-6/case.json; model tags/schema/options in ci_demo/ollama.py. CLI --endpoint or OLLAMA_HOST must be loopback HTTP origins; default http://127.0.0.1:11434.

Both models use three attempts, the same passing source/prompt, temperature 0.2, context 4096, output budget 1536 and seed sequence 5417/5418/5419. Model digest/Ollama version are saved; seeds do not guarantee bitwise determinism across runtimes/hardware.

doctor records host/runtime/endpoint; reproduce creates passing-seed gate; generate rechecks image/baseline then saves requests/raw outputs/diffs; verify checks hashes and baseline/three candidates/restoration; report renders saved artifacts only. scripts/demo.py --pull-models runs both models on the target PC.

Historical status: running -> hypothesis_supported_locally / hypothesis_not_confirmed / environment_error. Seed eligibility depends separately on actual head pass. Synthetic status: running -> generation_finished / environment_error. Attempts retain generation_error / invalid_output / awaiting_verification -> execution_verified / verification_failed; failures preserve timeout, execution error, baseline/restoration failure, absent or unstable test failure as rejection_reason. Finished stages may have zero accepted samples. Requested denominator remains three; unexecuted attempts are shown separately. Gold labels never assigned automatically.

## Next milestone

On RTX 4070 SUPER PC: doctor, reproduce, then scripts/demo.py --pull-models (add --skip-reproduce only after a local passing-seed gate exists). Review both three-attempt reports and labels; archive run folders. Only then report target latency/VRAM/acceptance. No fine-tuning, interceptor or ablation implemented.

## Recovery sequence

1. Read latest docs/agent-log.md entries and this file.
2. Inspect Git status and docs/demo-runbook.md.
3. Run doctor; inspect existing manifests before re-running a stage.
4. Continue the next unresolved milestone. Never overwrite a completed run to hide failures.
