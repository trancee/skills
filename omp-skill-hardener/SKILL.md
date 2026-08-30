---
name: omp-skill-hardener
description: "Hardens OMP skills/AGENTS.md from repeated persisted-session failures. Use to mine, attribute, propose approved guardrails, and add regressions. Don't use for one-off errors, new skills without history, general debugging, or automatic edits."
license: MIT
metadata:
  category: "agent-tooling"
  source: "https://github.com/eristoddle/agent-skills/tree/main/skills/skill-hardener"
  sourceVersion: "eristoddle/agent-skills@0bb8bd82e0db30ac955938914f78685338112c82"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-29T18:07:51+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-30T11:48:01+02:00"
---

# OMP skill hardener

## Gates

- recurrence >=3 matching events AND >=2 sessions
- post-fix: 1 event => inspect; >=2 independent => review
- source lines + effective target read before proposal
- exclude environment/user indecision/tool outage/already-forbidden behavior
- before edit: show evidence,target,path,exact text,before/after,replay; require explicit wording+target approval
- max 3 narrow instruction edits/pass
- raw/events/report/ledger: outside skill dir; mode `0600`; never share without manual redaction

READ `references/omp-session-format.md` for unusual records/miner changes. READ `references/signatures.md` before accepting clusters.

## 1. Private state

```bash
umask 077
mkdir -p "${OMP_SKILL_HARDENER_STATE:-$HOME/.local/state/omp-skill-hardener}"
```

## 2. Mine

```bash
python3 <skill-directory>/scripts/mine_friction.py \
  --project "$(basename "$PWD")" --days 30 --min-cluster 3 \
  --json "${OMP_SKILL_HARDENER_STATE:-$HOME/.local/state/omp-skill-hardener}/events.json"
```

Options: `--session FILE`; `--sessions-dir DIR`; intentional all-history=`--days 0`.
Signals: frustration, interrupt, same-tool error loop, post-plan reversal, hook/approval block, same-file edit loop, done-without-verifier.

## 3. Rank+confirm

```bash
python3 <skill-directory>/scripts/report.py \
  "${OMP_SKILL_HARDENER_STATE:-$HOME/.local/state/omp-skill-hardener}/events.json" \
  --ledger "${OMP_SKILL_HARDENER_STATE:-$HOME/.local/state/omp-skill-hardener}/ledger.json" \
  --output "${OMP_SKILL_HARDENER_STATE:-$HOME/.local/state/omp-skill-hardener}/report.md"
```

For each gated cluster:
1. READ `sessionFile:line` vicinity.
2. CONFIRM same failure, independent sessions, active branch, timestamps/tool/correction.
3. Generated guardrail=seed only.

## 4. Attribute

- explicit `custom_message(skill-prompt)` + dir => high
- `read skill://name`, no dir => medium; compare effective `skill://name` with authored file/provider precedence
- no active skill => low; inspect nearest active `AGENTS.md`
- duplicate skill names => BLOCK
- parent rule caused failure => edit parent, not duplicate child rule

## 5. Propose+approve

Root cause form: `WHEN <condition>, agent does <failure> vs <required>`.
Guardrail: imperative+observable at failed decision; no generic advice.
Present: counts; 2-3 excerpts; root cause+rejected alternatives; effective target; exact patch; behavior delta; red regression.
ASK approval. Tool approval != behavioral-rule approval.

## 6. Edit

1. CAPTURE tree status + original affected lines; preserve pre-existing work; inseparable dirty patch => STOP.
2. READ full affected section + referenced controlling rules.
3. APPLY <=3 narrow edits; remove direct contradictions; show diff/lines.
4. Broader restructure => separate approval.

## 7. Regression

Copy `assets/regression-test.json` outside installed skill; READ `references/regression-testing.md`.

```bash
python3 <skill-directory>/scripts/run_regression.py SPEC --root TARGET --skip-replay
python3 <skill-directory>/scripts/run_regression.py SPEC --root TARGET --replay "SCENARIO"
```

GATE: red before edit; green after; target `skill://` read observed. Never weaken assertion to pass.
Edit-caused failure => restore only captured lines; never reset/checkout broad user work. Flaky/unrelated => diagnose, keep approved text.

## 8. Record

```bash
python3 <skill-directory>/scripts/record_fix.py \
  --ledger "${OMP_SKILL_HARDENER_STATE:-$HOME/.local/state/omp-skill-hardener}/ledger.json" \
  --target 'skill:<name>' --signature '<signature>' \
  --guardrail '<approved text/change>' --changed-file '<path>' \
  --source-report '<private report>'
```

STOP without edit if: unresolved attribution; recurrence gate miss; environmental cause; duplicate stronger rule; rejected wording; no distinguishing regression.

Provenance: Stephan Miller `skill-hardener`, `eristoddle/agent-skills@0bb8bd82e0db`; MIT in `references/upstream-license.txt`.
