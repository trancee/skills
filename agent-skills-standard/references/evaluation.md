# Agent Skills eval

Spec validation != activation/output proof.

## Trigger

- cases: 8-10 positive + 8-10 near-miss negative; vary phrasing/detail/explicitness/multistep context
- fixed train set for edits; held-out validation selects result
- >=3 runs/query; threshold chosen before results
- observe actual `SKILL.md` load, not answer mention/correctness
- positive miss => add general missing intent
- negative hit => sharpen boundary
- never copy eval wording into description
- full loop: [description eval](https://agentskills.io/skill-creation/optimizing-descriptions)

## Output

1. Same prompt/files/output/model/client/tool policy; fresh context.
2. Compare with-skill vs no-skill or previous version.
3. Assertions after first outputs: observable validity/behavior/count/boundary/error, not exact prose.
4. Grade PASS only with cited output evidence.
5. Record time/tokens if available; inspect traces for waste, retries, ignored directives, missing resource loads.
6. Subjective quality => blind compare + concrete human feedback.
7. Full method: [output eval](https://agentskills.io/skill-creation/evaluating-skills).

## Client transitions

ASSERT:
1. valid package -> catalog
2. matching prompt -> activate once
3. referenced resource -> package-root resolution
4. near miss -> no activation
5. duplicate -> precedence+diagnostic
6. invalid/untrusted -> no model context
7. reload -> add/change/delete reflected

Activation evidence required: tool call, trace event, loaded-source record, or equivalent.
