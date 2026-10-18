---
name: lean
description: "Installs, develops, proves, and troubleshoots Lean 4 projects. Use when configuring elan or Lake, writing Lean programs, formalizing theorem statements, completing tactic or term proofs, using Mathlib, auditing proof axioms, or debugging elaboration and build failures. Don't use for Lean 3 migrations without a separate compatibility plan, Lean manufacturing, or unverified claims about external programs."
compatibility: "Baseline: Lean 4.35.0 and its bundled Lake through elan; respect each project's lean-toolchain and dependency manifest. Mathlib requires a compatible revision and caches. Axiom-audit helper: Python 3.9+. Sandboxed lake check/comparator require Linux and bubblewrap; other host/editor paths need separate verification."
metadata:
  category: "formal-methods"
  source: "https://lean-lang.org/"
  sourceVersion: "Lean v4.35.0@eb6cafb7290e8bd5f2937522d8d804f58f02bafc; Mathlib v4.35.0@56a005855ea17e0b0958f73ec801ae140b0a1679; official guides inspected 2026-10-18"
  createdBy: "github-copilot/gpt-6.1-sol"
  createdAt: "2026-10-18T15:57:54+02:00"
  updatedBy: "github-copilot/gpt-6.1-sol"
  updatedAt: "2026-10-18T16:10:48+02:00"
---

# Lean 4 programming and proof development

Resolve bundled resources from the skill root; run Lake commands from the consumer's package root. Use [official Lean documentation](https://lean-lang.org/learn/) and the reference matching the actual compiler, not a different `/latest/` release.

## Step 1: Fix the contract and trust level

1. Identify the task: installation, existing package change, executable behavior, mathematical formalization, or validation of an untrusted proof. Read project instructions, `lean-toolchain`, Lake configuration, manifest, affected imports and declarations before changing them.
2. Record exact theorem statements, binders, hypotheses, type classes, definitions and intended informal meaning. Preserve the requested statement; proving a weaker, shadowed or vacuous proposition is not completion.
3. Separate Lean's formal model from an external program/system. A kernel-checked theorem proves its elaborated proposition relative to its definitions and axioms, not that an unmodeled implementation matches it.
4. Treat Lake configurations, imports, macros, tactics and `#eval` as executable code. Review ordinary project code before building. For untrusted/AI-generated proof submissions, read `references/proofs-mathlib-trust.md` **before loading them**; use the sandboxed validation route and a trusted challenge when statement identity matters.

Gate: the target statement/runtime contract, toolchain selection and executable trust boundary are explicit.

## Step 2: Establish the package environment

1. Read `references/install-lake.md` for host setup, elan selection, new/existing packages, target coverage, dependency pins and diagnostics. Keep an existing project at its pin unless migration is the task.
2. Confirm `elan show`, `lean --version`, and `lake --version` from the intended package root; align the editor's project and toolchain with that terminal.
3. New core-only smoke project -> generate with the chosen stable release:
   ```bash
   lake +leanprover/lean4:v4.35.0 new VerifiedDemo std
   ```
   In that disposable package, copy `assets/Verified.lean` to `Verified.lean` and replace generated `Main.lean` with `assets/Main.lean`. Add a `[[lean_lib]]` table with `name = "Verified"` to generated `lakefile.toml` so Lake recognizes this additional module root. Inspect the executable target name (4.35.0 generates `verifieddemo`), then run `lake --wfail build +Verified verifieddemo`; do not assume the default graph includes every file.
4. Run the configured executable with `0`, `12`, `nope`, and no arguments. Require respectively `count=0`/exit 0, `count=12`/exit 0, stderr `expected a natural number`/exit 1, and usage/exit 2. Confirm the list-count append theorem and axiom report from the same fixture.
5. Mathlib project -> use the compatible Mathlib revision/toolchain/cache branch in `references/proofs-mathlib-trust.md`; exercise `assets/MathlibProof.lean` there. Do not install Mathlib merely for examples covered by core/Std.

Gate: real Lean elaborates the proof fixture, native compilation completes, and the program's success/error paths execute as specified.

## Step 3: Implement the selected branch

1. Programming or elaboration problems -> read `references/programming-debugging.md`. Reuse imported data types and APIs, preserve totality and dependent invariants, separate pure logic from IO, and inspect concrete types before changing coercions/instances.
2. Proofs/Mathlib -> read `references/proofs-mathlib-trust.md`. Search existing declarations, check names/types/imports under the actual pin, inspect each goal and local context, then use term proofs or tactics appropriate to its structure.
3. Add small named intermediate lemmas when they clarify an invariant or induction hypothesis. Keep namespace/import/visibility conventions; narrow simplification sets where proof stability matters. Close every branch without `sorry`, `admit`, custom proof-bypass axioms or kernel-check disabling.
4. Recursion/metaprogramming/program verification -> follow the relevant versioned reference linked from the selected branch. Prove termination where required; keep `partial`, `unsafe`, native evaluation and experimental `vcgen` assumptions explicit rather than treating them as total kernel reduction.
5. Fix the first actual diagnostic at its source. Reduce ambiguous terms to explicit annotations or a minimal local example. Scope resource-limit changes to a justified computation; preserve theorem semantics and warnings.

Gate: every changed declaration elaborates with the intended type and all proof goals closed; executable cases and error behavior remain correct.

## Step 4: Check coverage, axioms and behavior

1. Build every changed module explicitly, then the repository's configured aggregate targets/test drivers. `lake env lean` supplies dependency search paths but does not build imports; a successful unrelated/default target cannot certify an omitted file.
2. Audit each delivered theorem's **transitive** assumptions with `#print axioms`. For reviewed projects using ordinary qualified identifiers, run the bundled helper:
   ```bash
   python3 scripts/check-axioms.py --project path/to/package \
     --module Verified --theorem SkillDemo.count_append --json
   ```
   It builds the specified modules, queries Lean, and rejects assumptions outside the standard policy. Read its `--help` for limits. This is ordinary build/axiom evidence, **not** a sandbox, independent checker, or proof of statement intent.
3. Lean 4.35+ higher-assurance route -> use `lake check` for default-target export/kernel/axiom validation; use `lake comparator` against a trusted challenge when the exact theorem identity matters. Follow the trust reference for coverage, external checkers, platform prerequisites and exit statuses. A blocked check is not a rejected theorem or an accepted proof; keep the sandbox enabled.
4. Execute changed programs with meaningful positive, boundary and error inputs; observe stdout/stderr/exit codes. Check runtime behavior separately from theorem checking. Keep consumer tests only where they protect a real invariant or plausible bug.
5. Copy `assets/validation-report.md`; report exact toolchain/imports/targets, theorem statements, axiom sets, executed cases, checker results and remaining assumptions. Distinguish formal proof, runtime observation, and unverified external correspondence.

## Error Handling

- Wrong version/missing command -> inspect PATH, ELAN_HOME, project pin and overrides; follow installation reference before upgrading anything.
- Unknown import or incompatible `.olean` -> check root, exact module case, dependency versions and explicit import build; retain the manifest.
- Typeclass/coercion/metavariable errors -> use annotations, `#check`, `#print`, `#synth` and the current goal/context; repair the missing fact rather than broadening global instances.
- Unsolved goals/tactic failure -> inspect the first remaining goal, rewrite direction and induction generalization. Preserve the statement and use a proof-producing tactic supported by the imported environment.
- `sorryAx` or unexpected axiom -> inspect transitive dependencies and native/custom assumptions. Remove the incomplete proof or report the changed trust policy; warning suppression does not repair it.
- Checker unavailable, sandbox denied, timeout or native link failure -> report the exact environment failure and completed checks; do not disable isolation or label a load-only result as verified.
