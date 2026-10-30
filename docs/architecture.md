# Architecture and context checkpoint

## Objective

Study whether execution-verified synthetic data helps CI error diagnosis in human-agent collaboration. The first milestone is a reproducible real-repository demo, not model training or a general benchmark.

## Current implementation status

Current workflow uses only qwen2.5-coder:7b-instruct for generation. Qwen/Qwen2.5-Coder-3B-Instruct is the future primary diagnoser and is not implemented or run in W1. The auxiliary generator has been removed from active configuration and orchestration, with no legacy execution branch; historical evidence is unchanged. Target-PC properr reproduction supports the local missing-pytest hypothesis with two head tests passing. The saved 7B run has two execution-verified attempts out of three; the user has accepted the three explained keep/exclude recommendations, while formal labels/locations and training approval remain pending. W1 correction checks: 31 host tests passed, one Docker integration test intentionally skipped, no model/pilot reruns. The old 22-test PC/Docker acceptance log remains historical evidence. W1-04 is done; W1-03 is done for conclusion/disposition review. See docs/data-review.md#w1 and docs/development-summary.md#w1.

## Current expansion milestone — 30 October 2026

Implemented and published the canonical cases/<id>/case.json layout, visible index and expansion-01 evidence. Expansion 02 adds eight source cases plus two explicitly linked profile corrections, 15 real 7B calls and 11 execution-verified byte-distinct candidates in astroid/pvlib/FastAPI. One is a syntax/prompt violation flagged in review; execution acceptance is not curation approval. Combined expansion cohorts: 40 screened source cases, 17 attempted source cases across ten repositories, 36 generation attempts, 17 runner-accepted attempts / 14 accepted byte hashes. See docs/development-summary.md#expansion-02 and docs/data-review.md#expansion-02. Old W1/batch-01 evidence is immutable; user/gold/training approvals remain pending.

The read-only curation audit creates data-manifests/development-groups-v1.json: 40 source identities / 42 profile records / 20 repo groups (including screened exclusions), shared-commit alias evidence and exact/lexical-edit duplicate suggestions. It does not approve labels, delete raw artifacts or create final train/validation/test assignments. W2-04 remains doing; properr W1 is outside this two-cohort audit scope.

## Dataset scope and integration status

The research plan includes both AIDev/AIDev-pop and suitable SWE-bench subsets. Legacy W1 integrated properr. The v2 registry/runner now supports registered Python-source AIDev and SWE-bench cases; batch 01 actually attempted four AIDev and five SWE Lite dev cases. Recipes are targeted local reconstructions, not a claim of supporting every dataset repository or reproducing the entire official SWE-bench environment. Diagnostic-label mapping and final data eligibility remain separate review work.

SWE-bench provides reference solution/test patches and FAIL_TO_PASS/PASS_TO_PASS tests. These support diagnosis curation but do not automatically supply the project's cause taxonomy, confirmed causal lines or human/agent attribution. Keep the gold solution patch separate from diagnostic inputs. The selected SWE Lite dev subset is explicitly development by user decision. W2-04 must review duplicates/groups and define later train/validation/test; any future independent evaluation groups stay out of generation/train. The already-read astropy__astropy-12907 example belongs to development, not an unseen final test. See docs/implementation-plan.md and docs/reference/00_bao_cao_dinh_huong_nghien_cuu.md; new SWE-bench runs are documented in the expansion summary; no new label approval is claimed.

## Components and data flow

Repository: https://github.com/HUSTlang-nguyen/IT5417-Synthetic-Data-for-CI-Diagnosis (private), main; origin is the matching HTTPS Git URL. Files live in the renamed child folder inside the original workspace. Original parent slides/research documents remain outside the new repository.

Python CLI -> pinned case preparation -> Docker image -> historical reproduction -> passing head seed -> 7B generation -> candidate validation -> Docker baseline/three candidate repetitions/restoration -> HTML report and manual label review -> future data for 3B diagnosis after later data gates.

- cli: commands doctor, reproduce, generate, verify, report, batch. reproduce/generate accept registered --case (default properr-6). batch takes exactly one of --manifest or --resume; it does not route to 3B. generate and the HTTP generation adapter accept only the 7B generator; verify refuses other model runs before Docker or evidence changes. No diagnosis command exists yet.
- sources: fetch exact Git commits and export source snapshots.
- runner: immutable tests, no-network unprivileged containers with timeout/resource limits.
- ollama: local /api/chat JSON-schema outputs; store raw responses, digest, configuration and timing.
- pipeline: manifests and state transitions; invalid attempts remain in denominators.
- report: escaped, offline-readable Vietnamese HTML with raw artifact links.
- session: single-generator generation_demo manifests/reports checkpoint before preflight and after stages; fixed denominator three, explicit unexecuted attempts, measured-only timings and raw-run links. Historical pilot_comparison reports remain readable; no active comparison creation command/module remains.
- repository skill: `.agents/skills/ci-data-review/` provides Vietnamese instructions and a detailed review guide for agent-led technical CI data assessment. It reads available artifacts and reuses read-only hash/JUnit helpers; it adds no pipeline command or dependency. The user reviews evidence-linked conclusions, not an unprocessed code/log checklist. Invocation is `$ci-data-review` or normal matching; UI metadata preserves default implicit selection.

## Persistent state

- docs/development-summary.md and docs/data-review.md are the two canonical narrative reports, organized by W1/cohort. The six prior report paths retain section links and legacy anchors. Execution evidence, manifests and approval states remain unchanged.

- cases/<case-id>/case.json: canonical source/config identity; cases/README.md indexes W1 and expansion profiles. data-manifests holds registry/group selections only.
- .cache/: ignored source checkout, exported sources, Docker build context and environment evidence.
- runs/<run-id>/: ignored immutable input/output evidence, per-command logs, JSON manifest, review stub and report.
- docs/evidence/: small committed summaries and selected actual textual logs, without vendor code/model weights.
- New target-PC historical snapshots and software logs have targeted .gitattributes -text rules to preserve their recorded bytes in Git; original laptop evidence is unchanged.
- docs/agent-log.md: append-only chronology.
- This file: current architecture, decisions, limitations and resumption instructions.
- The skill instructions, guide and UI metadata are versioned in the repository. `.cache/skill-authoring/` holds isolated authoring-tool dependencies; it is ignored and separate from the standard-library pipeline.

## Fixed decisions

- No cloud API/key required. ollama.GENERATOR_MODEL is qwen2.5-coder:7b-instruct, the sole generator. ollama.DIAGNOSTIC_MODEL is the future HF checkpoint identity Qwen/Qwen2.5-Coder-3B-Instruct, not a generation tag. User explicitly removed the auxiliary generator; never download/call/rerun/review it as part of current work. Preserve its archived artifacts without changing them.
- W1 properr source base eff739a28971a66a36d443bfde91c515f7a858ea; head 8fd30245ed66b5145d651efc9203eb9a911e95d5.
- Source has a Rust extension; the orchestrator is Python. Python 3.11 matches the recorded CI workflow.
- Historical reproduction tests the original missing-pytest installation distinction, without preinstalling pytest in the base environment.
- W1 synthetic generation edits only properr/__init__.py at passing head. V2 edits exactly one registered production Python file on a passing fixed seed. Test patches/harness files are frozen separately and never edited by candidates.
- Execution acceptance is pass -> repeated fail -> restored pass; cause/location labels stay pending human review.
- For future reviews, separate observed execution facts, generator self-labels, agent proposals and explicit human confirmation. Comment-based leakage is assessed against actual diagnostic input; unknown input means a conditional risk, not automatic rejection. Stack traces/line numbers are valid diagnostic evidence. Skill creation alone does not approve data. Subsequent explicit user acceptance of the three recommendations is recorded separately in docs/data-review.md#w1; official label/location and training fields remain pending.
- The PC target cannot be declared tested from laptop-only evidence.
- Docker toolchain: Debian Bookworm Python 3.11, Rust 1.85, maturin 1.7.8, pytest 8.3.5. Image ID/build logs saved. Base image tags/apt are not fully hermetic locks; rebuilds can differ.
- Verification mounts only candidate read-only and fresh JUnit output writable; source/tests/manifests never mounted writable. Output mount preserves JUnit after container termination; /tmp stays tmpfs.
- Stable failures: same JUnit test identity, failure kind and assertion message in all three repetitions. Only repr memory addresses (` at 0x...`) are normalized; assertion values remain significant.

## Configuration, commands and state

Run from repository root with Python >=3.11; standard library only. Optional `python -m pip install -e .`; documented python -m commands need no installation. Default case is cases/properr-6/case.json; all registered cases now use cases/<case-id>/case.json; old data-manifests/cases/*.json is read-only fallback for older artifacts. Model tags/schema/options are in ci_demo/ollama.py; exact-edit-v2 schema and execution adapter are in ci_demo/multicase.py. CLI --endpoint or OLLAMA_HOST must be loopback HTTP origins; default http://127.0.0.1:11434.

The generator uses three attempts, the same passing source/prompt, temperature 0.2, context 4096, output budget 1536 and seed sequence 5417/5418/5419. These values and the prompt are unchanged by the role correction. Model digest/Ollama version are saved; seeds do not guarantee bitwise determinism across runtimes/hardware.

doctor records host/runtime/endpoint; reproduce creates passing-seed gate; generate rechecks image/baseline then saves requests/raw outputs/diffs; verify checks hashes and baseline/three candidates/restoration; report renders saved artifacts only. scripts/demo.py --pull-models downloads only 7B. It creates a demo session before doctor, checkpoints doctor/reproduction/generation links and final verification, stops on stage errors without automatic retry, and preserves the generation run ID even when the CLI exits nonzero. --skip-reproduce requires an existing local passing seed. No models were called to implement/review W1.

Historical status: running -> hypothesis_supported_locally / hypothesis_not_confirmed / environment_error. Seed eligibility depends separately on actual head pass. Synthetic status: running -> generation_finished / environment_error. Attempts retain generation_error / invalid_output / awaiting_verification -> execution_verified / verification_failed; failures preserve timeout, execution error, baseline/restoration failure, absent or unstable test failure as rejection_reason. Finished stages may have zero accepted samples. Requested denominator remains three; unexecuted attempts are shown separately. Gold labels never assigned automatically.

Session kind generation_demo: running -> demo_finished / demo_incomplete. Completion requires verification_finished and three terminal attempt records (generation_error, invalid_output, execution_verified or verification_failed), with no stage/run error; zero accepted samples is valid. Session fields include generator role/model/run/counts/timing, diagnostic role/model with not_implemented status, doctor/reproduction links and pending human review. No fake timing or success for absent attempts. Completed sessions cannot be checkpointed again; start a new session. Raw linked run manifests are read only.

## Next milestone

W2-04: complete grouping/near-duplicate review and later split roles before training. Read the new task-contract/labeling-guide and expansion summary/review; all new data remains development and pending gold/training approval. Completed conclusion review is in docs/data-review.md#w1 R2, produced with ci-data-review for only the three attempts in generate-20261029T054921315491Z. Rechecked source/test/candidate hashes and all 15 saved stage JSON/JUnit results without reruns. Attempt 1 leaves tested aliases unchanged and does not fail tests; attempt 2 multiplies a method object and raises TypeError at candidate line 16; attempt 3 multiplies the numerical result by 1.1 and fails assertions (causal candidate line 15, detection test lines 13/25). All three generator proposals say syntax, which is not supported by those outcomes.

R2 supersedes the earlier blanket comment-based exclusion recommendation: comments violate the saved prompt, but leakage remains conditional on the still-unfixed diagnostic input contract. Agent recommends excluding attempt 1 from the synthetic-failure set and retaining attempts 2/3 as development/review candidates with supported error mechanisms, not training-approved samples. The user explicitly accepted these explanations and keep/exclude recommendations; the chat decision and recording time are documented separately. Formal data-review identity/labels/locations and training approval remain pending. Raw reviews and model outputs are unchanged; the prior analysis was saved separately in .cache/w1-03-prior-review.md. W1-03 is done for review of the explained conclusions/dispositions; W1-04 remains done. The original W1 review included no W2/SFT or 3B runtime work; later development expansion is described above. 3B/SFT remain unimplemented.

Full historical runs and comparison HTML are preserved locally in .cache/archives/target-pc-runs-20261029.zip and runs/. A pre-change hash inventory of runs/evidence/cases is .cache/w1-evidence-before.json. Report only saved target measurements; doctor memory snapshots are not peak model VRAM. Visual QA remains pending because browser file-protocol access was blocked. No fine-tuning, interceptor or ablation implemented.

Current local runtime is portable .cache/tools/ollama/ollama.exe, with OLLAMA_MODELS set for its server process to .cache/models and OLLAMA_HOST=127.0.0.1:11434. It is not installed into system PATH or registered as a service. After reboot, start that executable with `serve` and the same process environment, and prepend its directory to PATH when using the demo helper's --pull-models option. Raw server/setup/demo logs stay ignored in .cache.


## Multi-case v2 execution and evidence

ci_demo/multicase.py owns versioned Python-source recipes; ci_demo/batch.py schedules serial Docker/model work with case-specific contexts, images, config hashes and gates. Sources are fetched by full commit, regular tracked files exported without following symlinks, and Git apply uses explicit private Git/work-tree roots. SWE base/fixed receive identical source test patches, then only fixed receives the reference repair. AIDev freezes declared upstream head regression tests onto base and records this reconstruction qualification.

Image builds can access package sources; runtime has no network, runs as 65534 with a read-only root, drops capabilities and has declared memory/CPU/PID/time limits. Explicit log/test_logs tmpfs and per-case pytest version/plugin allowlists remain bounded and cannot mask source or tests. Only candidate input is bind-mounted read-only, with a fresh JUnit output directory writable. Declared logs tmpfs is allowed for TCM; source/tests/raw run roots remain unwritable. Post-batch audit confirmed all inventoried source/test bytes inside both roles of eight images, not just host exports.

Passing gates carry full source inventories and image IDs. Generation v2 provides a passing-source excerpt, asks 7B for one exact before/after edit, stores request/raw response/proposal/full candidate/hash and keeps three requested attempts even on errors. It does not send gold patch or reference labels/explanations as diagnosis input. Schema self-labels remain unconfirmed. Generation and verification have separate linked runs; verification does not rewrite finished generation. Prompt v2 is separate from immutable W1 protocol.

Batch active runtime budget is six hours including measured discovery, excluding coding; no new operation below 20 GiB free or after budget. Per-operation bounds: build 1200s, tests 300s, model 180s. No model/environment automatic retry. Resume skips completed stages and creates an interruption event linked to incomplete raw runs instead of reissuing uncertain calls. OS-level batch locks prevent concurrent resume; these locks and preservation of diff newlines were hardened after batch 01, with unit tests and no experiment rerun. Raw batch-01 diffs retain their original Windows newline translation; candidate bytes were verified separately.

Raw context, metadata, patches, runs and models remain ignored. Registry configs and actual compact summary/software log live in versioned locations. All batch-01 cases are development; exact duplicate candidate hashes are reported separately from accepted-attempt counts. Task contract and labeling guide are development v0.1, not approved gold data or a final evaluation protocol.

## Versioned generation and profile corrections

single-line-site-v3 is opt-in for cohort-02 configs; v2 and W1 defaults remain unchanged. Static AST inspection of passing seed/test text selects bounded lines and independent test excerpts, with separate site subsets per attempt. The response is path/site_id/replacement/explanation: no generator diagnosis label is requested. Replacement has no leading indentation/newline; renderer preserves the original indentation/line ending and edits one declared line. Full raw prompt/response/site catalog/candidate/diff and hashes are saved. A v3 candidate produced IndentationError despite its valid-syntax instruction; review flags it without changing the raw execution_verified status.

SWE source identities default to exact matching. New profiles may explicitly opt into exact_or_unique_truncated_param: only an incomplete bracketed parameter identifier with exactly one full observed match is resolved, with source/resolved/expected/observed evidence persisted. No fuzzy/plain-prefix mapping. Unresolved escaped identifiers remain unconfirmed.

Correction profiles carry source_case_id/trial_of/reason and inherit already-charged budget in their own batch. They are additional experiment jobs, not new source cases or automatic retries. PyLabRobot plural-test classification was fixed but its new trial remained blocked by undeclared test differences; no guard was relaxed. FastAPI's pinned pytest/plugin conflict was corrected in -r1, which actually passed its fixed tests and produced one accepted candidate. Existing failed profiles/manifests stay intact.

## Recovery sequence

1. Read latest docs/agent-log.md entries and this file.
2. Read docs/implementation-plan.md for the current task/dependencies/gates; inspect Git status and docs/demo-runbook.md. Next task is W2-04 grouping/duplicate/split protocol after the completed development expansion, following the recorded W1-03 conclusion/disposition approval in docs/data-review.md#w1; W1-04 is done. Do not rerun the completed pilot or continue reviewing the removed auxiliary generator just to resume.
3. Inspect existing manifests before re-running a stage. Run doctor before runtime work; documentation-only changes do not require model, Docker or doctor reruns.
4. Continue the next unresolved milestone. Never overwrite a completed run to hide failures.
