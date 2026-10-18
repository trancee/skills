# Proof development, Mathlib, and validation trust

Use Lean **4.35.0** as the standalone baseline; preserve the consumer's actual compiler/dependency pins. The official [Theorem Proving in Lean](https://lean-lang.org/theorem_proving_in_lean4/) tutorial currently targets **4.33.0**. Use the [versioned language reference](https://lean-lang.org/doc/reference/4.35.0/) for current behavior.

## Establish the statement before searching for a proof

1. Translate the informal claim into exact binders/types, quantifiers, hypotheses and conclusion. Check coercions, subtraction on Nat versus Int, empty cases, finiteness/nonzero assumptions, and type-class choices. A statement with an impossible hypothesis may be vacuous; proving a shadowed name or weakened conclusion does not solve the intended problem.
2. Inspect the relevant definitions and fully qualified declaration with `#check`/`#print`. Use a separate small file with the same imports to inspect overloaded notation and instances. Check section variables and the actual exported theorem signature; undeclared variables may become automatic implicit parameters.
3. Search the existing library before constructing a duplicate lemma. Use the project's pinned sources/API docs; the [Mathlib API](https://leanprover-community.github.io/mathlib4_docs/), [Loogle](https://loogle.lean-lang.org/) and [Mathematics in Lean](https://leanprover-community.github.io/mathematics_in_lean/) are discovery aids, not proof that a name/import exists in an older revision. Verify candidate types with the selected compiler and narrow the import once the proof works.

Gate: the elaborated statement and relevant definitions express the requested claim, with intended hypotheses and no accidental name/instance changes.

## Work from the goal structure

1. Inspect the current target and local hypotheses after each failing step. Choose a direct term (`exact`, a lambda, constructor tuple or `calc`) when it expresses the argument clearly; use `by` tactics to build the same kernel-checked term interactively.
2. Introduce universal variables/implications with `intro`; use `apply` when a lemma's conclusion matches the target, then solve every generated premise. Split conjunction/record goals with the appropriate constructor; use `left`/`right` or an explicit constructor for a disjunction rather than an ambiguous `constructor` choice (4.35 warns about this).
3. Destruct a hypothesis/data value with `cases`; use `induction` when a recursive invariant needs an induction hypothesis. Generalize changing parameters **before** induction when the recursive call requires a stronger hypothesis. Keep case labels and solve every branch.
4. Rewrite equalities in the correct direction with `rw [h]` or `rw [← h]`; use `change` only for a definitionally equal target. Use `simp` for normalization by registered rewrite lemmas; narrow to `simp only [lemmas]` when dependency/import changes would otherwise make the proof fragile. Add helper lemmas for meaningful invariants, not a maze of automation wrappers.
5. Choose automation with the actual imports and theory in view:

   | Tool | Appropriate scope / limitation |
   | --- | --- |
   | `rfl` | Definitional equality; not an arbitrary algebraic identity |
   | Ordinary `decide` | Computable decidable proposition; does not prove an arbitrary open mathematical conjecture |
   | `omega` | Nat/Int linear arithmetic and related normalization, not general nonlinear algebra |
   | `grind` | Core equality/congruence, case analysis, instantiation and supported arithmetic reasoning; not a completeness guarantee for every theory |
   | Mathlib `ring` | Polynomial identities in supported algebraic structures |
   | Mathlib `norm_num`, `linarith`, `aesop` | Numerical normalization, suitable linear arithmetic, or proof search; verify imports and inspect residual goals |

6. Preserve the proposition while debugging a tactic. Fix missing facts, import scope, rewrite orientation or induction strength before increasing heartbeats/recursion limits. Re-check the final file rather than accepting a transient editor state or automation suggestion.
7. For custom tactics/macros, read the [metaprogramming-related language sections](https://lean-lang.org/doc/reference/4.35.0/Notations-and-Macros/) and inspect the pinned Lean API. For imperative program verification, 4.35 introduces experimental `vcgen` as the successor to deprecated `mvcgen`; use its [versioned tutorial/reference](https://lean-lang.org/doc/reference/4.35.0/The--vcgen--tactic/) and state program-logic specifications/assumptions explicitly instead of inventing tactic syntax.

Sources: [tactic proofs](https://lean-lang.org/doc/reference/4.35.0/Tactic-Proofs/), [simplifier](https://lean-lang.org/doc/reference/4.35.0/The-Simplifier/), [4.35 release changes](https://lean-lang.org/doc/reference/4.35.0/releases/v4.35.0/).

## Use a compatible Mathlib project and cache

1. Existing project: preserve `lean-toolchain`, declared dependencies, and `lake-manifest.json`. Build the relevant modules under that pin; get matching caches through `lake exe cache get` where needed. This cache executable comes from Mathlib, not an arbitrary Lean installation. Cache retrieval is not theorem validation.
2. New project following **current Mathlib**: the official setup command is:
   ```bash
   lake +leanprover-community/mathlib4:lean-toolchain new MyMathlibProject math
   ```
   This follows Mathlib's development toolchain, **not necessarily stable Lean**. On inspection, master used `v4.36.0-rc1`. Retain the generated compiler pin/manifest; do not overwrite an unrelated project's toolchain with this value.
3. New project deliberately on **stable 4.35.0**: generate a `lib` package with `lake +leanprover/lean4:v4.35.0 new MathDemo lib`, then add this to its TOML configuration:
   ```toml
   [[require]]
   name = "mathlib"
   git = "https://github.com/leanprover-community/mathlib4.git"
   rev = "v4.35.0"
   ```
   This tag resolves to `56a005855ea17e0b0958f73ec801ae140b0a1679`; its `lean-toolchain` matches Lean 4.35.0. In the new package, intentionally resolve with `lake update`. Mathlib's post-update hook may fetch caches; `MATHLIB_NO_CACHE_ON_UPDATE=1` skips that fetch when a targeted cache will be requested separately. Commit/review the resulting pins rather than repeatedly updating to fix imports.
4. Optional stable Mathlib smoke -> copy `assets/MathlibProof.lean` to the package root and add another `[[lean_lib]]` table with `name = "MathlibProof"`. Run:
   ```bash
   lake exe cache get Mathlib.Tactic.Ring
   lake --wfail build +MathlibProof
   ```
   Use a **module name** for a dependency's cache request; `Mathlib/Tactic/Ring.lean` is not an existing relative path in a downstream package root. The fixture's `module` header and `public section` preserve Mathlib's module-system discipline and export `SkillMathDemo.binomialSquare`; its axiom report is `[propext]` at the pinned baseline.
5. Cache miss -> inspect actual revision/toolchain/source edits and the cache CLI help. Rebuild compatible source if no matching cache exists. Do not mix `.olean` versions, disable TLS verification, or switch to an untrusted/`--unsafe` cache scope merely to obtain a green build.

Sources: [official manual setup](https://lean-lang.org/install/manual/), [Mathlib tagged configuration and cache implementation](https://github.com/leanprover-community/mathlib4/tree/56a005855ea17e0b0958f73ec801ae140b0a1679), [Mathlib source API documentation](https://leanprover-community.github.io/mathlib4_docs/).

## Validate at the required trust level

The [official validation guide](https://lean-lang.org/doc/reference/4.35.0/ValidatingProofs/) distinguishes ordinary mistakes from actively misleading proofs. Unreviewed AI-generated imports/build code are untrusted executable inputs. Review/isolate **before** building, not after a suspicious result.

| Level | Evidence established / boundary |
| --- | --- |
| Reviewed development: explicit module build, no errors/warnings | Elaborates the current theorem and checks its proof relative to the environment; no guarantee that dependencies are complete or the informal meaning is correct |
| `#print axioms Fully.Qualified.theorem` | Lists transitive assumptions for that declaration; imported `sorry` may appear even if its current theorem has no warning |
| `lake check` (4.35+) | Builds default targets in the sandbox, exports/replays them through the kernel, rejects non-standard axioms; not an external statement-identity check or coverage of omitted files |
| `lake comparator` with a trusted challenge/configuration | Compares the named solution statements/definitions against the trusted challenge and checks permitted axioms/kernel acceptance |
| `--paranoid` on check/comparator | Requires all bundled external checkers as well; stronger implementation diversity, not elimination of logical/specification assumptions |

For a delivered theorem, permit only the declared policy. Standard Lean axioms are `propext`, `Classical.choice`, `Quot.sound`; an empty list is also valid. `sorryAx` indicates incomplete proof in the theorem or a dependency. A custom axiom makes the result conditional on that assumption; record/review it rather than calling it an unconditional proof.

Native evaluation (`decide +native`, and tactics using it such as `bv_decide`) introduces dedicated `_native` axioms since Lean 4.29. The older `Lean.trustCompiler` machinery is removed in 4.35. Inspect the **actual** axiom list and acknowledge compiler/runtime correspondence assumptions. Ordinary `decide`, `#eval` output and native proof modes are not interchangeable. The helper's standard-axiom policy deliberately rejects native/custom assumptions.

For sandboxed `lake check`/`lake comparator`, require Linux, working `bubblewrap`/user namespaces, a manifest and the intended target graph. Keep isolation enabled. Missing prerequisites or timeout provide no acceptance result; do not downgrade to `--inadvisably-no-sandbox` to get a verdict. Ordinary helper/build commands are not this sandbox.

For comparator, author the challenge independently in a trusted environment and use the pinned release's `lake help comparator`/configuration schema. Its default `comparator.json` selects `challenge_module`, `solution_module`, `theorem_names`, and `permitted_axioms`. The challenge format can intentionally contain unproved statements; those are specifications, never final solution proofs. Check exits: 0 accepted, 1 rejected/build failure/non-permitted axioms, 2 unavailable environment. `--from-export` routes establish acceptance of the supplied export, not that it came from the current workspace source.

Gate: exact statements and definitions are reviewed, every affected module is checked, transitive axioms match the declared policy, required sandbox/checker steps actually completed, and remaining model/external-implementation assumptions are reported.
