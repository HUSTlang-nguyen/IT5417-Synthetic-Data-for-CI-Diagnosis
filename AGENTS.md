# Agent working instructions

- Read docs/architecture.md and the latest entries in docs/agent-log.md before working or after context compaction.
- Log actual milestones, commands/results, failures, decisions and the next step in docs/agent-log.md (Asia/Bangkok).
- Update docs/architecture.md when implementation, interfaces or decisions change.
- Implement the pipeline in Python. Keep responses concise.
- Never invent execution logs, model outputs, gold labels, historical CI results or PC-specific measurements.
- Preserve immutable source commits, tests and raw evidence. Synthetic and historical cases are different experiments.
- Generated code runs only in the constrained Docker runner. Never run it on the host.
- Keep models, source checkouts, runtime artifacts and secrets out of Git.
- Read docs/demo-runbook.md before changing the demo protocol.
