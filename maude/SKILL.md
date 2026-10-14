---
name: maude
description: "Installs, models, executes, and analyzes Maude rewriting-logic specifications. Use when writing functional or system modules, debugging equations and rewrite rules, exploring reachable states, checking LTL properties, controlling rewriting strategies, or using Maude reflection and symbolic narrowing. Don't use for FDA MAUDE medical-device reports, general-purpose theorem-prover claims, or Tamarin-specific security protocol workflows."
compatibility: "Baseline: Core Maude 3.5.1 with matching prelude/model-checker libraries. Official binaries: Linux x86_64 and macOS x86_64/arm64; Windows via WSL or separately verified build. Batch helper requires Python 3.9+. Full Maude, strategy-aware model checking, SMT and external proof tools require separately verified environments."
metadata:
  category: "formal-methods"
  source: "https://maude.lcc.uma.es/maude-manual/"
  sourceVersion: "Manual 3.5.1 (July 2025); Maude3.5.1@7269fc720072a2cd8b7222736721ba26dd3752b2; inspected 2026-10-14"
  createdBy: "github-copilot/gpt-6.1-sol"
  createdAt: "2026-10-14T15:49:23+02:00"
  updatedBy: "github-copilot/gpt-6.1-sol"
  updatedAt: "2026-10-14T19:19:29+02:00"
---

# Maude executable specifications and analysis

## Step 1: Define the semantics and claim

1. Record the model files/imports, initial states, state sort, environment/fairness assumptions, and required claim: data evaluation, sample execution, reachability, invariant, LTL, strategy-restricted behavior, or symbolic solutions.
2. Separate equations/axioms (state equality and normalization) from rules (transitions). Record equation termination/confluence/sort-decreasingness and rule coherence evidence or assumptions; Maude accepting a module proves none of these.
3. Read `references/install-model-execute.md`. Distinguish Core Maude from separately loaded Full Maude and extension tools; route Tamarin security-protocol work to `tamarin-prover` rather than translating its claims silently.
4. Review command files before loading. Files can contain arbitrary interpreter commands and IO; keep risky execution capabilities disabled for pure specifications. Bound potentially infinite computation and use a disposable workspace.

Gate: the model semantics, analysis mode, scope, assumptions, and executable trust boundary are explicit.

## Step 2: Establish the executable environment

1. Install a deliberately selected release using the installation branch in `references/install-model-execute.md`; verify archive/source identity and run `maude --version` / `maude --help`.
2. Preserve the matching distribution libraries. Set MAUDE_LIB when needed and verify `prelude.maude` and `model-checker.maude` resolution from the actual cwd; a lone binary or stale prelude is not a valid setup.
3. New environment -> copy `assets/finite-state.maude` and `assets/smoke.maude` into one disposable directory. Run from that directory with the skill's helper:
   ```bash
   python3 scripts/run-maude.py path/to/smoke.maude --maude path/to/maude \
     --expect-result Bool=true --expect-result CounterState=q1 \
     --expect-result Bool=true --expect-result CounterState=q2 \
     --expect-result Bool=true --counterexamples 1 --require 'No solution.' --json
   ```
   Resolve helper/assets from the skill root; input/model paths are consumer paths. The helper defaults cwd to the command file's parent. Use `--cwd` for a different load root.
4. Confirm actual values, the reachability path, a safe LTL result, and the expected liveness counterexample. Treat helper PASS as transcript evidence only, not formal validity or exhaustive-search certification.

Gate: the real interpreter loads matching libraries and executes reductions, rules, search, strategy, reflection, and both LTL verdict branches without diagnostics.

## Step 3: Build and debug the model

1. Pure functions/data -> use fmod/eq/ceq/membership declarations. Concurrent state change -> use mod/rl/crl. Keep constructors/sorts/variables and imported module ownership explicit; reuse prelude data modules instead of redefining incompatible arithmetic.
2. Use `parse in MODULE : term .` before execution when syntax is uncertain. Fix ambiguous mixfix/overload/sort errors; do not accept an error-kind result as valid domain data.
3. Encode intended algebraic equality using operator attributes such as assoc/comm/id, not looping equations. Inspect identity/AC matches, conditions, `[owise]`, `[nonexec]`, `frozen`, and equation evaluation strategies for semantic effects.
4. Exercise each changed equation/rule on positive and negative boundary inputs. Use explicit `in MODULE :`, labels, `show module MODULE .`, match/xmatch, and targeted traces to identify the first mismatch.
5. Require diagnostics-free actual evaluation: compilation is lazy, and Maude can exit 0 after parse warnings. Never hide diagnostics or add nonexec/frozen attributes just to make the run terminate.

Gate: changed declarations and transitions produce intended values/matches; unresolved typing/admissibility/coherence obligations remain named.

## Step 4: Select the analysis branch

1. Sample behavior -> bounded rewrite/frewrite; report it as one execution, not all reachable behavior.
2. Reachability/invariants -> read `references/search-model-checking.md`. Specify search arrow, solution/depth bounds, target predicate, and exhaustion status. Retrieve/replay witness paths. A bounded or interrupted no-witness search is inconclusive outside its explored scope.
3. LTL -> read `references/search-model-checking.md`. Define total state predicates, select the initial state and exact formula, verify finite reachable state space and normalization/coherence assumptions, and interpret counterexample prefix/cycle. Keep positive and negative controls to catch a vacuous or reversed property.
4. Strategies, unification/variants/narrowing, reflection, or SMT -> read `references/strategies-symbolic-meta.md` **only for the selected branch**. Check its executability/completeness/tool prerequisites before claiming results. Strategy execution does not make ordinary modelCheck strategy-aware.
   Symbolic setup proof -> run `assets/symbolic.maude`; confirm the B -> zero unifier, both concrete flip variants, and the narrowing goal unifier. Apply the reported accumulated substitution **and** goal unifier; a printed symbolic state alone is not the concrete witness.
5. Infinite-state model -> justify a sound abstraction or use a suitable external proof technique; do not relabel bounded exploration as unbounded verification.

Gate: the chosen command matches the requested semantics; bounds, fairness, state space, and evidence support exactly the reported claim.

## Step 5: Validate and report

1. Execute the changed model path and a meaningful counterexample/negative control. For automation, run reviewed command files through `scripts/run-maude.py` with exact expected result sequences and required witness text; preserve transcripts and wall-clock limits.
2. Inspect helper JSON fields and raw interpreter output. `No solution.`, true, an exit code, or a counterexample count alone does not establish the modeling assumptions or a completed exhaustive proof.
3. Copy `assets/analysis-report.md`; report interpreter/manual/source identity, model equations/rules, analysis mode/formula, initial states, all bounds, exhaustion status, witnesses, assumptions, and unavailable evidence. Distinguish proven finite-model claims from bounded observations and external-tool obligations.

## Error Handling

- Missing prelude/import/library -> verify MAUDE_LIB, actual cwd, distribution version, and load path; follow the installation reference.
- Parse warning/ambiguous term/kind result -> inspect exact module/sorts/operator syntax and declarations; fix the first diagnostic before accepting later results.
- Reduction hangs -> check equations, conditions, AC/identity matches and evaluation strategy; rewrite-step bounds do not bound equation normalization.
- Missing transition -> inspect equations/coherence, frozen arguments, rule condition variables, labels, and nonexec/strategy restrictions.
- Search or LTL does not terminate -> check reachable state-space finiteness and bounds; stop with an explicitly incomplete claim rather than replacing the model secretly.
- Unexpected counterexample -> replay states/labels and predicate equations; distinguish a real model bug, property/fairness mismatch, and an unsound abstraction.
- Helper fails -> use --help, repair exact result/diagnostic mismatch, or provision the real executable; no fallback interpreter or suppressed warning is acceptable.
