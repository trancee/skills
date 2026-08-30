---
name: omp-skill-hardener
description: "Hardens OMP skills and AGENTS.md rules from recurring failures in persisted OMP sessions. Use when repeated agent friction should be mined, attributed, converted into approved guardrails, and locked down with regression tests. Don't use for one-off mistakes, brand-new skills without history, general code debugging, or automatic edits without review."
license: MIT
metadata:
  source: https://github.com/eristoddle/agent-skills/tree/main/skills/skill-hardener
  category: "agent-tooling"
  createdAt: "2026-08-29T18:07:51+02:00"
  updatedAt: "2026-08-30T11:05:26+02:00"
---

# OMP skill hardener

Turn repeated failures in persisted OMP sessions into narrow, approved changes to the responsible skill or `AGENTS.md`. Never edit from one anecdote or from a generated proposal alone.

## Non-negotiable gates

1. Require at least three matching events across at least two sessions. More than one recurrence after a recorded fix is strong evidence for another review.
2. Read the cited session lines and the effective target before proposing a change. A signature is a lead, not proof of root cause.
3. Reject environmental failures, user indecision, unrelated tool outages, and failures already forbidden by a stronger active instruction.
4. Show the user the evidence, attributed target, exact proposed wording, affected file, and regression scenario. Obtain explicit approval before editing.
5. Apply at most three narrow instruction edits per approved hardening pass. Do not refactor the rest of the skill opportunistically.
6. Keep raw sessions, mined events, reports, and the fix ledger outside the skill installation directory with permissions limited to the user.

Read [the session format](references/omp-session-format.md) before changing the miner or interpreting unusual records. Read [the signature catalogue](references/signatures.md) before accepting a cluster.

## 1. Establish private state

Resolve `<skill-directory>` from the path supplied when this skill was loaded. Use a private state directory, not the repository:

```bash
umask 077
mkdir -p "${OMP_SKILL_HARDENER_STATE:-$HOME/.local/state/omp-skill-hardener}"
```

Do not copy entire transcripts into reports or prompts. The miner emits short, redacted excerpts and writes JSON with mode `0600`; reports and the ledger also use mode `0600`.

## 2. Mine persisted OMP sessions

Default to the current project and a 30-day window. Broaden only when the recurrence evidence is too sparse:

```bash
python3 <skill-directory>/scripts/mine_friction.py \
  --project "$(basename "$PWD")" \
  --days 30 \
  --min-cluster 3 \
  --json "${OMP_SKILL_HARDENER_STATE:-$HOME/.local/state/omp-skill-hardener}/events.json"
```

Use `--session <file>` for a sanitized fixture or one known session, `--sessions-dir <dir>` for a nonstandard store, and `--days 0` only for an intentional all-history scan.

The miner reconstructs the latest persisted branch, excludes injected user-like messages, tracks explicit and model-loaded skills, and detects:

- direct user frustration or correction;
- user interruption;
- repeated consecutive tool errors;
- plan reversal immediately after leaving plan mode;
- hook or approval blocks;
- repeated edits to one file;
- completion claims without an observed verification action.

## 3. Rank clusters and check recurrence

```bash
python3 <skill-directory>/scripts/report.py \
  "${OMP_SKILL_HARDENER_STATE:-$HOME/.local/state/omp-skill-hardener}/events.json" \
  --ledger "${OMP_SKILL_HARDENER_STATE:-$HOME/.local/state/omp-skill-hardener}/ledger.json" \
  --output "${OMP_SKILL_HARDENER_STATE:-$HOME/.local/state/omp-skill-hardener}/report.md"
```

Open the report. For each cluster above the recurrence gate:

1. Inspect its `sessionFile` and `line` locators in the private events file. Read only enough surrounding lines to establish what happened.
2. Confirm that independent sessions express the same failure mode, not merely the same word.
3. Confirm timestamps, active branch, tool name, and relevant user correction.
4. Treat the generated guardrail as a seed. Rewrite it against the surrounding target instead of pasting it blindly.

## 4. Resolve attribution

Attribution is intentionally conservative:

- `custom_message` with `customType: skill-prompt` and a skill directory: high confidence; edit that `SKILL.md`.
- Assistant `read` of `skill://<name>` without a recorded directory: medium confidence; read `skill://<name>` to verify the effective content, then locate the matching authored source under OMP's provider precedence.
- No active skill: low confidence; inspect the nearest active `AGENTS.md` rules before attributing to `base:AGENTS.md`.

Duplicate skill names are a blocking ambiguity. The effective `skill://<name>` content must match the file proposed for editing. If the evidence comes from a rule supplied by a parent `AGENTS.md`, edit that parent rather than adding a second rule to a child file.

## 5. Design and approve the guardrail

A useful guardrail is imperative, observable, and placed at the decision point that failed. It names the prohibited branch and the required replacement behavior. It does not restate generic good practice.

Before any edit, present:

- event and session counts;
- two or three short excerpts;
- root-cause judgment and rejected alternatives;
- effective target and exact insertion/replacement;
- expected behavior before and after;
- structural assertion and fresh replay that will fail without the change.

Ask for approval. A normal tool approval is not approval to change behavioral instructions; the user must approve the wording and target.

## 6. Apply the approved change

Before editing, capture the working-tree status and exact original affected lines. A dirty tree is a warning, not permission to overwrite: identify pre-existing changes and preserve them. Stop if the hardening patch cannot be separated from the user's work.

Read the complete affected section and every referenced instruction that controls the same decision. Reuse its vocabulary and remove directly contradictory obsolete wording. Make no more than three narrow edits. Show the resulting diff or exact changed lines.

If the approved change requires broader restructuring, stop and request separate approval rather than hiding it inside the hardening pass.

## 7. Add and run regressions

Copy [the regression template](assets/regression-test.json) outside the installed skill, customize it for the approved behavior, and follow [the regression guide](references/regression-testing.md).

Run deterministic structural assertions first:

```bash
python3 <skill-directory>/scripts/run_regression.py <regression.json> \
  --root <target-root> \
  --skip-replay
```

Then run the selected fresh OMP replay. The runner filters discovery to the target skill, appends an instruction to read it, requires an observed `read` call for its `skill://` URI, and evaluates only final assistant text:

```bash
python3 <skill-directory>/scripts/run_regression.py <regression.json> \
  --root <target-root> \
  --replay "<scenario name>"
```

A replay that did not load the target skill is invalid, even if its answer looks correct. Compare the fixed behavior against the preserved pre-fix failure evidence; do not weaken assertions until a failing result turns green.

If a regression fails because of the hardening edit, restore only the captured lines changed by this pass and show the rollback. Never use a reset, checkout, or broad restore that could discard pre-existing work. Diagnose an unrelated or flaky failure without modifying the approved guardrail.

## 8. Record and monitor the fix

After approval, application, and passing regressions:

```bash
python3 <skill-directory>/scripts/record_fix.py \
  --ledger "${OMP_SKILL_HARDENER_STATE:-$HOME/.local/state/omp-skill-hardener}/ledger.json" \
  --target 'skill:<name>' \
  --signature '<signature>' \
  --guardrail '<exact approved instruction or concise change summary>' \
  --changed-file '<path>' \
  --source-report '<private report path>'
```

Rerun mining and reporting after enough new sessions exist. One post-fix event triggers inspection; two independent post-fix recurrences trigger another hardening review. No recurrence is evidence of absence only within the scanned sessions and window.

## Stop conditions

Stop without editing when attribution is unresolved, the cluster misses the recurrence gate, the source failure is environmental, the proposed rule duplicates a stronger active rule, the user rejects the wording, or no regression can distinguish the desired behavior from the failure.

## Provenance

This OMP-specific adaptation preserves the evidence-first, approval-gated workflow of Stephan Miller's `skill-hardener`, retrieved from `eristoddle/agent-skills` at observed revision `b0b9ab82e0db`. See [the upstream license](references/upstream-license.txt).
