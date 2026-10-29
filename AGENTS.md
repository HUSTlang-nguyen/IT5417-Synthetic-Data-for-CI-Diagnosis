# Agent working instructions

- Read docs/architecture.md and the latest entries in docs/agent-log.md before working or after context compaction.
- Then read docs/implementation-plan.md, especially its current next task. Follow task dependencies and completion gates; do not restart completed experiments just to recover context.
- Update task status, evidence and the next concrete task in docs/implementation-plan.md at each milestone. Weekly slots are estimates, not confirmed calendar deadlines; never infer gold-label approval from execution success.
- Log actual milestones, commands/results, failures, decisions and the next step in docs/agent-log.md (Asia/Bangkok).
- Update docs/architecture.md when implementation, interfaces or decisions change.
- Implement the pipeline in Python. Keep responses concise.
- Never invent execution logs, model outputs, gold labels, historical CI results or PC-specific measurements.
- Preserve immutable source commits, tests and raw evidence. Synthetic and historical cases are different experiments.
- Generated code runs only in the constrained Docker runner. Never run it on the host.
- Keep models, source checkouts, runtime artifacts and secrets out of Git.
- Read docs/demo-runbook.md before changing the demo protocol.
- When reviewing CI data samples from code/diff/logs, use `.agents/skills/ci-data-review/SKILL.md`. The agent prepares the technical analysis and evidence; the user reviews the conclusions and remaining decisions. Keep skill use scoped to the requested samples, not unrelated development tasks.
