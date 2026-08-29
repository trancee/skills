# Regression testing

A hardening regression must distinguish the observed failure from the approved behavior. Preserve a redacted pre-fix scenario; do not invent an easy prompt that the model already answers correctly without the target skill.

## Version 1 spec

```json
{
  "version": 1,
  "skill": "target-skill-name",
  "structural": [
    {
      "name": "approved rule exists once",
      "path": "target-skill-name/SKILL.md",
      "contains": ["exact approved instruction"],
      "notContains": ["obsolete contradictory instruction"],
      "regex": ["optional multiline regex"],
      "notRegex": ["optional forbidden regex"],
      "maxOccurrences": [{"text": "exact approved instruction", "max": 1}]
    }
  ],
  "replays": [
    {
      "name": "redacted recurrence scenario",
      "prompt": "A realistic prompt preserving the decision that failed.",
      "requireSkillRead": true,
      "expect": {
        "exitCode": 0,
        "contains": ["observable required answer fragment"],
        "notContains": ["observable failed answer fragment"],
        "regex": [],
        "notRegex": []
      }
    }
  ]
}
```

Paths resolve against `--root`. Structural checks read UTF-8 text. Replay regexes use Python multiline regular expressions.

## Red/green proof

1. Write the structural and replay assertions before applying the approved change.
2. Run against the old target when that can be done without discarding user work. At least one material assertion must fail.
3. Apply the approved change.
4. Run structural checks with `--skip-replay`; they must pass.
5. Run only the affected replay by name. It must load the skill and pass the behavior assertions.
6. Run adjacent existing skill evaluations when the target already has them.

If preserving the old target requires destructive version-control operations, do not do that. The cited pre-fix session and a structural assertion absent from the old file can supply the red evidence.

## Fresh OMP replay behavior

The runner executes `omp -p --mode json --no-session --no-title`, filters discovered skills to the target name, appends a system instruction to read the target skill, and runs from `--root`. It fails if the JSON event stream lacks an observed `read` tool call for `skill://<name>` or lacks final assistant text.

Use `--model` only when the failure was model-specific. Use `--timeout` for a bounded slow replay. A fake or cached answer is not valid release evidence; fake executables are appropriate only for testing the runner itself.

## Assertion quality

Assert outputs the user can observe: a required decision, refusal, ordering, boundary, or omission. Do not assert model phrasing unless exact wording is the contract. Avoid source-string-only tests as the sole evidence; structural checks prevent rule loss, while fresh replays exercise behavior.

A replay can be nondeterministic. One failure is evidence to inspect, not permission to weaken the assertion. Re-run once only after identifying a transient cause. If the scenario remains unstable, sharpen the skill rule or state that a reliable regression could not be built and stop without recording the fix.
