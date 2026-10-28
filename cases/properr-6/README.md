# properr PR #6 — provenance

- Dataset: [hao-li/AIDev v5](https://huggingface.co/datasets/hao-li/AIDev/tree/v5), revision b8dc67df93e7c11f6f20c84129db7232eb1ec253; all_pull_request, record 3256868569, inspected row index 12.
- Upstream: [properr PR #6](https://github.com/kurtbrose/properr/pull/6), “Fix CI by including pytest”.
- Base: eff739a28971a66a36d443bfde91c515f7a858ea; head: 8fd30245ed66b5145d651efc9203eb9a911e95d5.
- source-snapshot.json is previously inspected PR metadata/diff copied from the parent workspace; not an execution log. case.json drives the runnable pipeline.

Exact Git objects are fetched/verified; tracked files are inventoried. Docker build compares immutable base/head tests. Local reconstruction installs base without pytest and head with pytest, following the PR dependency change; toolchain versions are approximations of the original CI environment.

Laptop observation: base missing pytest, head two tests pass (docs/evidence). Synthetic generation only edits properr/__init__.py on passing head, never tests or Rust. This new wrapper-regression experiment is distinct from the historical dependency error. PR agent metadata does not establish who caused that historical error.

Ollama integration follows official [chat API](https://docs.ollama.com/api/chat), [structured outputs](https://docs.ollama.com/capabilities/structured-outputs) and [model metadata](https://docs.ollama.com/api/tags), checked 2026-10-29. No target-PC model run completed yet.
