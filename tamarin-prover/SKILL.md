---
name: tamarin-prover
description: "Installs, configures, models, verifies, and troubleshoots symbolic security protocols with Tamarin Prover. Use when working with .spthy theories, multiset rewriting rules, SAPIC+ processes, Dolev-Yao adversaries, trace or observational-equivalence properties, batch proofs, interactive proof search, sources lemmas, Maude, or Graphviz. Don't use for computational cryptographic proofs, protocol implementation correctness, standalone theorem provers, or claims beyond the modeled symbolic theory."
compatibility: "Targets Tamarin Prover 1.12.0; installation/runtime may require Maude and Graphviz. Inspector requires Python 3.11+."
metadata:
  category: "formal-methods"
  source: "https://tamarin-prover.com/manual/master/book/001_introduction.html"
  sourceVersion: "Tamarin Prover 1.12.0@82780bbaf3328a45f624ddb41e51bf75425f851c; manual master and install guide inspected 2026-10-06"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-10-06T14:44:36+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-10-06T14:44:36+02:00"
---

# Tamarin Prover

## Step 1: Fix the analysis contract

1. STATE protocol roles, message flow, sessions, persistent state, trust anchors, compromise events, and claimed security properties.
2. DEFINE the adversary and channel assumptions. Treat `In`/`Out` as a Dolev-Yao-controlled public network unless the theory explicitly models another channel.
3. LIST every abstraction: symbolic terms instead of bit strings, equations for cryptographic behavior, omitted implementation behavior, and bounded domain assumptions.
4. CLASSIFY the goal as trace property, observational equivalence, or accountability. Record that observational-equivalence support is a sound approximation with stricter rule correspondence and limited restrictions.
5. ROUTE implementation correctness, side-channel resistance, computational reductions, and primitive security to their respective analyses; Tamarin proves only properties of the supplied symbolic model.

Completion: roles, trust, compromise, adversary, property class, and abstraction boundary are explicit.

## Step 2: Install and verify the toolchain

READ `references/installation.md` before installing, upgrading, using containers, or diagnosing `maude`/`dot` discovery.

1. REFRESH the official install page and latest release before selecting commands; package names, binary assets, dependency ranges, and supported platforms can change.
2. INSTALL one pinned release through the platform-native route. Use a source build only for Tamarin development or an explicitly required unreleased feature.
3. RUN:
   ```bash
   tamarin-prover --version
   tamarin-prover --help
   maude --version
   dot -V
   tamarin-prover test
   ```
4. RECORD the Tamarin version, install route, Maude version/path, Graphviz version/path, operating system, and architecture.

Completion: the version/help/dependency commands and installation self-test pass against the intended executables; the pinned Tamarin version is recorded.

## Step 3: Inspect or initialize the theory

1. IF a `.spthy` theory exists, RUN:
   ```bash
   python3 scripts/inspect-model.py --root path/to/model-or-directory --json
   ```
2. IF no theory exists, COPY `assets/theory-template.spthy` and rename the theory, rules, actions, and lemmas to match the protocol contract.
3. CHOOSE one primary modeling style: multiset rewriting rules or SAPIC+ processes. Avoid mixing them unless the translation interaction is understood and reviewed.
4. READ `references/modeling-verification.md` before adding custom equations, state restrictions, observational equivalence, accountability, or SAPIC+ state.
5. INVENTORY built-ins, custom functions/equations, rules/processes, linear and persistent facts, action facts, restrictions, lemmas, proof attributes, and unfinished `sorry` proofs.

Completion: the theory inventory and modeling style are explicit; every inspector finding is resolved or recorded.

## Step 4: Model messages, state, and compromise

1. DECLARE only required built-ins and function symbols. Prefer built-ins and subterm-convergent equations.
2. REQUIRE every custom equational theory to be convergent and have the finite variant property. Obtain expert evidence because Tamarin does not check this condition and unsupported equations can yield non-termination or incorrect results without warning.
3. MODEL fresh values with `Fr(~x)` in rules or `new x` in SAPIC+; use `$x`/public constants only for public values and `%x` only for guessable natural-number counters.
4. USE linear facts for consumed state and `!Persistent` facts for reusable state. Keep each fact's arity, capitalization, persistence, and multiplicity consistent.
5. PLACE protocol claims in action facts. MODEL compromise as explicit rules/events that release exactly the intended secrets.
6. TAG message variants and role/session state where implementations can enforce those distinctions.

Completion: every term constructor, fact, state transition, network exposure, and compromise path maps to one protocol assumption.

## Step 5: State sanity and security properties

1. ADD an `exists-trace` executability lemma that reaches each claimed role completion with the intended honest conditions. Prove it before relying on safety lemmas.
2. EXPRESS secrecy through claim actions and adversary knowledge `K(m)`, with explicit compromise exceptions and ordering.
3. EXPRESS authentication through matching running/commit or send/receive actions; include peer identities, roles, and agreed data. Add uniqueness only when injective agreement is claimed.
4. KEEP formulas guarded: universally quantified variables occur in an action constraint before implication; existentially quantified variables occur in an action constraint before conjunction.
5. USE restrictions only for assumptions the real protocol/environment enforces. Add executability lemmas that exercise restricted behavior.
6. SEPARATE all-traces lemmas from `exists-trace` lemmas and label every compromise exception.

Completion: non-vacuity, secrecy/authentication/equivalence goals, and compromise exceptions are represented by reviewable action facts and lemmas.

## Step 6: Parse and precompute before proof search

RUN from the directory containing the theory:

```bash
tamarin-prover --parse-only model.spthy
tamarin-prover --quit-on-warning --precompute-only model.spthy
```

1. FIX every parser and well-formedness diagnostic; do not continue from warning-bearing output.
2. INSPECT raw/refined source counts and every remaining partial deconstruction.
3. IF partial deconstructions remain, READ `references/troubleshooting.md`; add a proved `[sources]` lemma or sound model refinement rather than a restriction that merely suppresses the unwanted trace.
4. IF `--auto-sources` is evaluated, inspect and prove the generated `AUTO_typing` lemma; generation does not guarantee sufficiency or correctness.

Completion: parsing and well-formedness pass, and partial deconstructions are absent or explicitly understood with proved source reasoning.

## Step 7: Prove and inspect attacks

1. PROVE the executability lemma first:
   ```bash
   tamarin-prover --quit-on-warning --prove=executability model.spthy
   ```
2. PROVE one named security lemma at a time, then the complete theory:
   ```bash
   tamarin-prover --quit-on-warning --prove=lemma_name model.spthy
   tamarin-prover --quit-on-warning --prove model.spthy
   ```
3. TREAT `verified` as conditional on the exact theory/version/options. TREAT `falsified`/attack traces as model counterexamples requiring semantic review. TREAT timeout or non-termination as inconclusive.
4. IF automation stalls, START:
   ```bash
   tamarin-prover interactive model.spthy
   ```
   Open `http://127.0.0.1:3001`, inspect sources and the constraint system, and guide proof search without changing the claim merely to force termination.
5. STORE completed proof skeletons in the theory. Reject `sorry` from completion evidence.

Completion: every target lemma is verified, has an understood attack, or is explicitly inconclusive; no result is inferred from timeout.

## Step 8: Review evidence and report limits

1. RE-RUN the inspector, parse-only, precompute-only, named proofs, and full batch proof with the pinned toolchain.
2. COPY `assets/tamarin-review.md`; fill every field with commands, versions, proof outcomes, attacks, partial-deconstruction status, assumptions, and limits.
3. COMPARE the `.spthy` message parsing, state transitions, compromise timing, and acceptance conditions against the protocol specification and implementation.
4. REPORT Tamarin's symbolic-model boundary, undecidability/non-termination risk, custom-equation evidence, observational-equivalence approximation, and any unproved lemma.

Completion: reproducible commands and artifacts support each claim; model-to-protocol correspondence and all unresolved risks are explicit.

## Error Handling

- `tamarin-prover` missing -> read `references/installation.md`; install one supported pinned release and verify `PATH`.
- `maude` or `dot` missing/wrong -> resolve the intended executable/version before proof search; do not suppress dependency checks.
- Parser location appears misleading -> inspect the preceding token and undefined function symbols; the grammar can report slightly before the actual undefined symbol.
- Fact arity/capitalization/persistence warning -> normalize every occurrence of that fact before proving.
- Unbound variable -> bind it in a premise/input or generate it with `Fr`/`new` according to its meaning.
- Executability lemma falsified -> repair disconnected roles/state or over-strong restrictions before evaluating security lemmas.
- Partial deconstruction or looping proof -> read `references/troubleshooting.md`; inspect sources, typing/tagging, and sound source lemmas.
- Batch proof times out -> classify the result as inconclusive and switch to precomputation/interactive diagnosis.
- GUI needed from WSL/remote host -> bind only as intended and use the port-forwarding procedure in `references/installation.md`.
