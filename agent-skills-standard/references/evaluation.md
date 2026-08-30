# Agent Skills evaluation

Use this reference when an audit includes activation accuracy or task output. Specification validation cannot prove either behavior.

## Trigger evaluation

Create realistic should-trigger and should-not-trigger prompts. Use near misses for negative cases, not unrelated prompts. Vary phrasing, detail, explicit domain terms, and multi-step context.

Keep a fixed training set for description changes and a held-out validation set for selection. Run each query several times because model activation varies. Record whether the client loaded the target `SKILL.md`, not whether the final answer mentioned the skill.

A useful starting set has 8 to 10 positive prompts and 8 to 10 near misses. Three runs per prompt expose unstable activation. Choose thresholds before reviewing results.

When a positive misses, add the general user intent that was absent from the description. When a near miss triggers, sharpen the boundary. Do not paste wording from individual eval prompts into the description.

Read [Optimizing skill descriptions](https://agentskills.io/skill-creation/optimizing-descriptions) for the full loop.

## Output evaluation

Run each task with the skill and against a baseline without the skill or with the previous version. Use a fresh context and the same input files, output location, model, client, and tool policy.

Define observable assertions after inspecting the first outputs. Prefer file validity, required behavior, counts, boundaries, and error handling over exact prose. Grade each assertion with cited output evidence.

Record duration and token use when the client exposes them. A quality improvement with a large context or latency cost is a tradeoff, not an automatic pass.

Inspect execution traces for unnecessary reads, repeated attempts, ignored instructions, and missing resource loads. Compare outputs blindly when subjective quality matters. Keep human feedback concrete and tied to a task result.

Read [Evaluating skill output quality](https://agentskills.io/skill-creation/evaluating-skills) for workspace and grading examples.

## Client integration evaluation

Test these observable transitions:

1. A valid package appears in the catalog.
2. A matching prompt activates the package.
3. Activation loads the intended instructions once.
4. A referenced resource resolves from the package root.
5. A near miss leaves the package unloaded.
6. A duplicate follows precedence and reports shadowing.
7. An invalid or untrusted package never reaches model context.
8. Reload reflects a package addition, change, and removal.

Do not infer activation from a correct final answer. Require a tool call, trace event, loaded-source record, or another client signal.
