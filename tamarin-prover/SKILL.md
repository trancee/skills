---
name: tamarin-prover
description: "Installs, models, verifies, and troubleshoots symbolic security protocols with Tamarin Prover. Use for .spthy rules, SAPIC+, trace/equivalence/accountability properties, batch or interactive proofs, sources lemmas, Maude, or Graphviz setup. Don't use for computational cryptographic proofs, implementation correctness, unrelated theorem provers, or claims beyond the symbolic model."
compatibility: "Tamarin Prover 1.12.0; Maude and Graphviz runtime dependencies; inspector requires Python 3.11+."
metadata:
  category: "formal-methods"
  source: "https://tamarin-prover.com/manual/master/book/001_introduction.html"
  sourceVersion: "Tamarin Prover 1.12.0@82780bbaf3328a45f624ddb41e51bf75425f851c; latest release/manual/install checked 2026-10-06"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-10-06T14:44:36+02:00"
  updatedBy: "github-copilot/gpt-6.1-sol"
  updatedAt: "2026-10-06T15:15:21+02:00"
---

# Tamarin Prover

## 1. Contract

1. RECORD roles, messages, sessions/state, trust anchors, channels, compromise/reveal/erasure timing, and claims.
2. ASSUME Dolev-Yao network control for `In`/`Out` unless explicitly modeled otherwise.
3. CLASSIFY trace | observational equivalence | accountability. LIST symbolic abstractions, equations, omitted implementation behavior, and bounds.
4. ROUTE computational reductions, primitive security, implementation correctness, and side channels to separate analyses.

Gate: explicit threat model, property class, and symbolic-to-protocol boundary.

## 2. Toolchain

READ `references/installation.md` for installation/upgrade, dependency discovery, WSL, or remote access. SELECT a supported pinned release; source build only for development/required unreleased features.

```bash
tamarin-prover --version
tamarin-prover --help
maude --version
dot -V
tamarin-prover test
```

RECORD versions, executable paths, install origin, OS/architecture. REFRESH release notes before version changes.

Gate: intended executables pass version/dependency checks and self-test.

## 3. Theory

Resolve `scripts/` and `assets/` from the skill package; pass target paths explicitly:

```bash
python3 scripts/inspect-model.py --root path/to/model-or-directory --json
```

1. EXISTING model -> inventory and review every finding; inspector is heuristic, not Tamarin parsing/proof.
2. NEW model -> COPY `assets/theory-template.spthy`; replace the smoke model with actual roles/messages/claims, not just renamed rules.
3. CHOOSE rules or SAPIC+ as primary style; mix only with reviewed translation interaction.
4. READ `references/modeling-verification.md` for custom equations, state/restrictions, SAPIC+, equivalence, or accountability. INVENTORY built-ins/functions/equations, facts/actions, restrictions, lemmas/attributes, unfinished proofs.

Gate: complete protocol behavior, declared style, and accounted model inventory.

## 4. Model and properties

1. ENABLE only used built-ins/functions. Prefer subterm-convergent equations; custom theories need external convergence/FVP evidence. Tamarin does not check that requirement; unsupported equations can silently invalidate results.
2. GENERATE secrets with `Fr(~x)`/`new x`; `$x`/quoted constants are public, `%x` is a guessable counter, `#i` is temporal.
3. USE linear consumed state versus persistent `!Fact`; preserve arity/case/persistence/multiplicity across all occurrences.
4. MAP state/role/session/tag distinctions to enforceable protocol behavior; explicit compromise rules release exactly intended secrets.
5. LABEL claims with action facts. ADD honest `exists-trace` completion lemmas before safety claims to detect vacuity.
6. STATE secrecy through `K(m)` and explicit timed compromise exceptions; authentication binds identities/roles/agreed data and prior peer events. Injectivity needs uniqueness.
7. GUARD variables: universal action guard -> implication; existential action guard -> conjunction.
8. RESTRICT only real enforceable assumptions; prove executable traces through restricted behavior.
9. FOR equivalence, record sound approximation, strict rule correspondence, limited restrictions. FOR accountability, discharge generated conditions and replacement property.

Gate: every term/state/action/assumption maps to the protocol; complete, non-vacuous property definitions.

## 5. Parse and precompute

Run Tamarin commands from the model directory:

```bash
tamarin-prover --parse-only model.spthy
tamarin-prover --quit-on-warning --precompute-only model.spthy
```

FIX parser/well-formedness failures before proof search. INSPECT raw/refined sources and partial deconstructions. OPEN chains -> READ `references/troubleshooting.md`; prove `[sources]` reasoning or sound refinement. `--auto-sources` only generates a candidate; inspect/prove `AUTO_typing` and confirm sufficiency.

Gate: no parser/well-formedness diagnostics; open chains absent or understood with proved source reasoning.

## 6. Prove

```bash
tamarin-prover --quit-on-warning --prove=executability model.spthy
tamarin-prover --quit-on-warning --prove=lemma_name model.spthy
tamarin-prover --quit-on-warning --prove model.spthy
```

1. PROVE honest completion first, named claims next, complete theory last.
2. CLASSIFY each lemma: verified (exact theory/version/options) | falsified (review model attack) | inconclusive (timeout/non-termination/unfinished).
3. AUTOMATION stalls -> `tamarin-prover interactive model.spthy`; open `http://127.0.0.1:3001`, inspect sources/constraints, guide search without weakening claims.
4. SAVE completed proof skeletons; `sorry` never establishes completion. Semantic model changes require rechecking all claims.

Gate: every target lemma has a proof, understood attack, or explicit inconclusive result.

## 7. Evidence

1. RE-RUN inspector, parse/precomputation, named/full proofs on final theory with pinned toolchain.
2. COPY `assets/tamarin-review.md`; record digests, commands/options, outcomes, proof/attack artifacts, sources, restrictions, and limits.
3. COMPARE encoding/parsing, state, compromise timing, and acceptance with specification/implementation.
4. REPORT symbolic-only scope, undecidability, custom-equation evidence, equivalence approximation, and all unproved claims.

Gate: each claim has reproducible evidence; correspondence and unresolved risks explicit.

## Failure routing

- Missing/wrong executable -> installation reference; correct version/PATH before proof.
- Parser location misleading -> preceding token, undefined/reserved function.
- Fact inconsistency -> fix every schema/case/persistence occurrence.
- Unbound value -> input/state binding or `Fr`/`new`, according to meaning.
- Honest trace falsified -> repair disconnected state/over-strong restrictions before safety claims.
- Open chains/loop/attack -> troubleshooting reference; preserve claim and admissible traces.
- Timeout -> inconclusive, not verified/falsified.
- WSL/remote GUI -> installation reference; loopback/SSH tunnel, not public bind.
