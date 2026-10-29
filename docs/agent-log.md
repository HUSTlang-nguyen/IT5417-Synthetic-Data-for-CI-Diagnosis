# Agent execution log

Append entries in chronological order. Timezone: Asia/Bangkok. Record facts, evidence paths and unresolved work; never mark planned work complete.

## 2026-10-29 02:22 +07 — Workspace initialized

- Renamed the verified-empty folder IT5417 namehere to IT5417-Synthetic-Data-for-CI-Diagnosis within the parent workspace.
- Initialized Git on main. Parent documents and slides were not moved.
- Confirmed GitHub account neikhn is authenticated; target repository does not exist yet.
- Current development host: RTX 3050 Laptop 4 GB, Python 3.13, working Docker Linux engine. Target demo host: user's separate RTX 4070 SUPER 12 GB PC, not yet tested.
- Chosen real source: AIDev v5 all_pull_request id 3256868569, properr PR #6.
- Next: implement reproducibility, isolated verification, local Ollama calls and evidence reporting; run actual Docker reproduction before publishing.

## 2026-10-29 02:30 +07 — Implementation and first reproduction

- Implemented Python CLI, pinned Git export, Docker Python 3.11/Rust/maturin build, Ollama JSON-schema calls, manifests, verification and Vietnamese HTML.
- Added two-model PC runner, revised plan, CSV feedback tracker and runbook. Copied three original research Markdown files with provenance warnings. Parent slides/documents untouched.
- Real reproduce-20261028T192709234536Z: build exit 0; base missing pytest; head two tests pass. This supports a local dependency hypothesis, not original CI/actor causality.
- Initial host tests hit restricted Windows temp permissions; reran using project-local temp outside that restriction.

## 2026-10-29 02:35 +07 — Runner defects corrected

- Integration exposed JUnit loss after stopped-container tmpfs teardown. Replaced docker-cp from /tmp with fresh output-only bind mounts. Candidate remains read-only; manifests/tests never writable mounts.
- Different repr memory addresses caused false instability. Normalize addresses only, preserving test identities/assertion values. Original failing artifacts remain in ignored .cache/runner-check.
- Reproduction rerun reproduce-20261028T193510880404Z: base exit 1, head exit 0, two passed tests and JUnit saved. Passing-seed gate records source/test hashes/image ID.
- Doctor doctor-20261028T193508157140Z confirms Docker Linux, RTX 3050 Laptop (not target), no local Ollama.

## 2026-10-29 02:37 +07 — Local acceptance

- 14 software tests passed, including real Docker pass -> three stable fixture failures -> restored pass. Checked malformed JSON, outside-scope paths, unchanged original byte hashes, timeout, report escaping and rejection reasons.
- Fixture is software-only, not model output; actual LLM attempts = 0. Target-PC testing pending.
- Saved small real logs/inventories/historical HTML under docs/evidence; full runs/cache ignored. Updated architecture/recovery context.
- Browser policy blocked file:// visual QA; no workaround attempted. HTML structure/escaping checked; visual inspection remains on PC.
- Next: staged-content review, private repository creation, commit/push main and remote verification; then target-PC model protocol.

## 2026-10-29 02:40 +07 — Private remote and staged review

- Created https://github.com/HUSTlang-nguyen/IT5417-Synthetic-Data-for-CI-Diagnosis; GitHub confirms isPrivate=true, correct owner and ADMIN permission. origin HTTPS, branch main.
- Reviewed 72 staged files: Python/config/context/references and small evidence only. Cache/runs/environments/weights/.env excluded. Credential-pattern scan found no matches; Python compile check passed.
- Code whitespace check passed. Full diff-check warnings are confined to preserved whitespace in archived source snapshots, Markdown line breaks and raw test logs.
- Next: commit/push and verify GitHub commit; then target-PC model protocol.

## 2026-10-29 02:41 +07 — Published and verified

- Committed initial implementation as 381b3beedba07ba800aea5dbeec9cbc16c159b48 and pushed main without force. GitHub API commit SHA matched local HEAD; default branch main, private=true. Working tree was clean.
- Added explicit ignore patterns for datasets/Parquet and local key/secret files before final handoff commit.
- Handoff: docs/demo-runbook.md, docs/architecture.md and committed evidence. On target PC install/start Docker Linux and Ollama, then run python scripts/demo.py --pull-models. First confirm doctor; no claim that either model or RTX 4070 SUPER has been tested.
- Remaining research work: actual 2x3 model attempts, review labels, measure runtime and revise next experiments from those results. Parent presentation/research originals unchanged.

## 2026-10-29 12:36 +07 — Target PC confirmed; comparison evidence implemented

- Resumed the existing implementation goal after reading architecture, latest log and demo runbook. User confirms this is now the RTX 4070 SUPER PC. Preserve the original laptop validation-summary.json as historical evidence.
- Doctor doctor-20261029T052953774365Z: Python 3.11.9, target GPU match; Docker engine initially absent and restricted local socket check failed. Unrestricted doctor-20261029T053310246298Z confirmed Ollama port refused connections and Docker engine stopped.
- Initial `python -m unittest discover -v`: three temporary-directory permission errors, one skipped Docker integration. Rerun with TEMP/TMP=.cache/test-temp: original 13 host tests passed, integration skipped. No generated code executed on host.
- Implemented offline `compare --runs`, compatibility checks, measured-only timings and fixed three-attempt denominators. Demo helper saves comparison before preflight, checkpoints stages and continues after an isolated model error. Added seven software regression tests; latest suite: 20 passed, one Docker integration skipped. Fixtures are not model/research results.
- Real `python scripts/demo.py` before setup returned exit 1 and preserved comparison-20261029T053313134040Z with both models not_started, three unexecuted each, unknown timings and prerequisite errors.
- Started installed Docker Desktop hidden; actual engine reports Linux. Started PC reproduction reproduce-20261029T053446089841Z (source commits exported; build in progress). Downloading official standalone Ollama into ignored .cache/tools, following https://docs.ollama.com/windows. GitHub release API query hit an unauthenticated rate limit; switched to official latest-release download URL. Download/setup not yet complete.
- Updated README/runbook and architecture for compare/checkpoint behavior. `git diff --check` passed. Next: finish PC reproduction/runtime setup, run actual Docker fixture, then the two models sequentially and retain all outcomes.

## 2026-10-29 12:38 +07 — Real target-PC reproduction and runner acceptance

- PC reproduce-20261029T053446089841Z completed with hypothesis_supported_locally: base exit 1 / No module named pytest; head exit 0 / 2 tests passed, actual JUnit retained. Container interpreter reports Python 3.11.2. Passing gate written with source/test hashes and image sha256:4aa2ac18be6a80bc53e4861b08db38ddddfccc648d898e45ebe643a264b621a5.
- `CI_DEMO_DOCKER_TESTS=1 python -m unittest discover -v`, with project-local TEMP/TMP: 21 tests passed, no skips. Real fixture baseline pass -> three stable failures -> restored pass succeeded on PC; fixture is not model output. Full software output retained in .cache/target-pc-software-tests.txt; selected small evidence copied to docs/evidence/target-pc without replacing laptop artifacts.
- Portable Ollama download continues; actual LLM attempts still zero. Next: start loopback-only Ollama with ignored local model storage, pull both documented models and run the fixed 2x3 protocol.

## 2026-10-29 12:39 +07 — Portable local model runtime started

- Official portable Ollama archive completed (1,601,969,847 downloaded bytes); client reports 0.40.13. Extracted executable is .cache/tools/ollama/ollama.exe. No system installation or PATH change persisted.
- Started `ollama serve` hidden, loopback 127.0.0.1:11434, server-process OLLAMA_MODELS pointing to .cache/models. Server stdout/stderr retained under .cache; models/runtime excluded from Git.
- Started real `python scripts/demo.py --skip-reproduce --pull-models` with portable runtime added only to that process PATH. Full helper output retained in .cache/target-pc-demo.txt. New comparison run is checkpointed before pulls/generation; outcome still pending.
- Next: inspect actual two-model generation and Docker verification results, report rejected attempts and denominators, update target-PC evidence independently of preserved laptop results.

## 2026-10-29 12:43 +07 — Report visual check limitation

- Read the computer-use skill and attempted to open the PC historical report through the in-app browser. Browser security policy rejected the file:// protocol. No alternate browser surface, local server, indirect execution or other workaround attempted. Visual QA remains pending; report structure/escaping is covered by software tests.
- Two-model helper continues independently; model downloads are setup time, not generation measurements. Raw outcomes will remain in their run folders.

## 2026-10-29 12:46 +07 — Final comparison regression coverage

- Added comparison-report error escaping coverage and exposed per-model environment errors in the HTML summary. Eight new comparison/demo tests now cover denominators, unexecuted/unknown timing, protocol mismatch, snapshot modification, historical/duplicate input rejection, preflight failure, continuation to the second model and escaped error text.
- Final `CI_DEMO_DOCKER_TESTS=1 python -m unittest discover -v` passed all 22 tests, no skips; real Docker fixture ran again because production report rendering changed. Final output preserved separately as .cache/target-pc-software-tests-final.txt and docs/evidence/target-pc/software-tests-final.txt; earlier 21-test log remains unchanged.
- Checked all local artifact links in the target-PC historical report (8) and current comparison (2): no missing destinations. Actual results saved in .cache/target-pc-report-links.json. Visual browser QA remains blocked by file-protocol policy.
- No further code changes planned before the live model run completes; preserve all model outcomes, then write final PC evidence and context.

## 2026-10-29 12:54 +07 — First actual 2x3 PC pilot completed and archived

- `python scripts/demo.py --skip-reproduce --pull-models` completed exit 0. Comparison comparison-20261029T053856421402Z is comparison_finished with protocol_compatible=true, both requested denominators three, all six actual requests retained, no unexecuted attempts.
- 7B run generate-20261029T054921315491Z: attempt 1 verification_failed / does_not_fail_consistently; attempts 2 and 3 execution_verified. Per-request seconds 39.984 / 4.781 / 4.609, total 49.374. First request includes initial runtime warmup/loading; these are not steady-state benchmark timings.
- 1.5B run generate-20261029T055021908791Z: attempts 1 and 2 invalid_output, both done_reason=length at 1536 eval tokens; attempt 3 execution_verified. Per-request seconds 6.906 / 6.985 / 2.187, total 16.078. Raw responses, requests, candidates/diffs and Docker evidence stay unchanged in ignored runs.
- Important quality findings from actual evidence, not assigned gold labels: 7B output includes comments identifying the regression contrary to prompt. Its verified attempt 2 raises TypeError and attempt 3 fails numerical assertions. Verified 1.5B attempt 3 has an unfinished __all__ list causing SyntaxError during test collection. All review labels remain pending; execution-verified does not approve prompt compliance, plausibility or training eligibility.
- Final doctor doctor-20261029T055141374481Z confirms target GPU, Docker Linux and Ollama available. Version 0.40.13; actual model digests are in target-PC summary. GPU memory is a doctor snapshot, not peak model VRAM.
- `python -m ci_demo compare --runs generate-20261029T054921315491Z generate-20261029T055021908791Z` completed exit 0, creating comparison-20261029T055142213496Z entirely offline. Both original generation manifests remain unchanged.
- Saved docs/evidence/target-pc/README.md and validation-summary.json, selected actual historical logs and separate software-test logs. Preserved original laptop summary and raw results. Updated evidence index, README, architecture, feedback tracker and portable-runtime restart runbook.
- Archived all runs to .cache/archives/target-pc-runs-20261029.zip. Verified ZIP CRC and exact bytes against 297 source artifact files; checked 12 HTML reports, zero broken local links. Archive checksum/check details retained in .cache/archives/target-pc-archive-check.json. No model weights or source clones in archive or Git.
- Final whitespace check passed. Credential-pattern scan found no matches (rg exit 1 means no match). Final software validation remains 22/22 passed including constrained Docker fixture; no generated candidate ran on host. Visual QA remains pending because browser file protocol was blocked; no workaround attempted.
- Next: human review of the four materialized candidates and three execution-verified cases, confirm taxonomy/locations/plausibility and reject bug-disclosing comments before training use. Decide on any separately versioned follow-up prompt/output-budget experiment from these actual outcomes. No fine-tuning, interceptor or ablation is implemented or claimed.

## 2026-10-29 12:59 +07 — Stash backup and publication preparation

- User requested stash, commit and push. Fetched origin successfully; main and origin/main were equal before committing.
- Created stash backup cd1a89ec1732070f1e74ef0377c720f57f8d0022 (includes untracked implementation/evidence files, excludes ignored cache/models/runs); applied it with --index while retaining the stash as a backup.
- Reviewed changed/new files and the actual final 22-test log. Whitespace check passed before staging; credential-pattern scan returned no matches. No production code has changed since the successful full Docker-inclusive test suite.
- Stash exposed Git line-ending normalization on copied PC raw evidence. Added targeted .gitattributes -text rules for the new historical artifacts and software logs, then recopied those bytes from the untouched runs/cache originals. Existing laptop evidence remains unchanged.
- Next: stage implementation, docs and selected small evidence only; verify staged paths and raw evidence bytes; commit and push main without force; verify remote commit.
