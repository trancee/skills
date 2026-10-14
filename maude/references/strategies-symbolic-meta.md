# Strategies, symbolic analysis, reflection, and SMT

Read only the section for the selected analysis branch. Baseline: Core Maude 3.5.1, manual July 2025, release commit `7269fc720072a2cd8b7222736721ba26dd3752b2`. Preserve the executable's matching libraries. Each branch changes the operational relation or supported theory; record that boundary before interpreting a result.

## Strategies: control execution without changing the theory

1. Keep transition rules in a system module and control in an `smod ... endsm` importing that module. Declare `strat name : ArgumentSorts @ SubjectSort .` (zero arguments: `strat name : @ SubjectSort .`), then `sd name(arguments) := expression .`; use `csd ... if ... .` for conditional definitions.
2. Invoke `srewrite [n] in MODULE : term using expression .`; `n` limits returned solutions, not execution time or rewrite depth. `srewrite` explores alternatives fairly; `dsrewrite` explores depth-first and can starve another branch on an infinite path. Bound wall-clock time externally.
3. Select rule labels and control deliberately:

   | Expression | Semantics / risk |
   | --- | --- |
   | `label` | Apply that rule; enumerate possible matches/positions. |
   | `top(label)` | Restrict the rule application to the root. |
   | `label[X <- value]` | Constrain a rule variable; use declarations from the actual module. |
   | `alpha ; beta` | Apply beta to each alpha result. |
   | `alpha \| beta` | Explore both alternatives, not a priority choice. |
   | `alpha *`, `alpha +` | Zero-or-more / one-or-more iterations. |
   | `idle`, `fail` | Return the original term / produce no result. |
   | `alpha ? beta : gamma` | On alpha's results, run beta; if alpha fails, run gamma on the original term. |
   | `alpha or-else beta` | Run beta only if alpha produces no result. |
   | `alpha !` | Iterate until alpha cannot apply; may diverge. |
   | `try(alpha)`, `test(alpha)` | Try and retain the original on failure / test existence while preserving the original. |
   | `one(alpha)` | Retain only the first found result; intentionally discard alternatives. |

4. Use `match pattern s.t. condition` for a root test, `amatch` for a subterm test, and `matchrew pattern by X using alpha` to rewrite selected matched components. Read §10.1.2 before introducing nested scopes or the `xmatchrew`/`amatchrew` variants. A test returns its original subject when successful; it does not perform the state change of a rule.
5. Explicit rule-label application can execute `nonexec` rules. The `all` strategy excludes them, external objects, and implicit rules. Audit these distinctions rather than treating strategic execution as ordinary rewrite/search.
6. After loading `assets/finite-state.maude`, run:

   ```maude
   srewrite [1] in COUNTER-STRATEGY : q0 using reach-two .
   ```

   Expected result: `CounterState: q2`. This proves the chosen sequence executes; it does not prove every unrestricted run reaches q2 (the retry loop is a counterexample).

Ordinary `modelCheck` analyzes the underlying rewrite theory, not the named strategy. Strategy-aware model checking needs its own verified tool/encoding, version, and preservation argument. Do not erase unwanted rules to disguise a strategy restriction.

Sources: [strategy language §10.1](https://maude.lcc.uma.es/maude-manual/maude-manualch10.html#x78-16500010.1), [strategy modules §10.2](https://maude.lcc.uma.es/maude-manual/maude-manualch10.html#x78-17000010.2), [search policies §10.4](https://maude.lcc.uma.es/maude-manual/maude-manualch10.html#x78-17300010.4).

## Unification versus variants

1. Choose the equality theory:
   - `unify [n] in M : t =? u .` solves order-sorted equality modulo supported operator axioms **Ax**. It ignores ordinary equations, membership axioms, and transition rules; built-in function evaluation is not part of this unification.
   - `variant unify [n] in M : t =? u .` solves modulo eligible equations marked `[variant]` plus Ax. Other equations/rules are not silently included in the symbolic theory.
   - Conjoin several equations with `/\`. Plain unification can return several most-general unifiers even without algebraic attributes because of sort intersections.
2. For Ax unification, check the preregular order-sorted signature and supported attributes in §13.3. Associative and associative-with-identity unification can be incomplete/non-finitary; retain warnings about missed solutions. Unsupported attributes on non-ground terms are not evidence of unsatisfiability. Idempotence is not generally supported directly by Ax unification; an explicitly justified variant-equation encoding is a different theory setup.
3. For variant computation, require unconditional, confluent, terminating, sort-decreasing equations coherent modulo Ax; their left-hand sides cannot be variables. `owise` is inadmissible; `[variant nonexec]` equations are ignored with an advisory. Membership axioms do not guide variant generation. Check ordinary reduction on the chosen binary as well as symbolic computation instead of mechanically duplicating equations from a documentation example.
4. Invoke `get variants [n] in M : t .`; interpret each result as a canonical term **and its substitution**, not merely a reachable value. `get irredundant variants`, `irredundant unify`, and `filtered variant unify` perform global filtering; they may need the complete underlying result set before returning a filtered prefix.
5. Record finite variant property (FVP) evidence where termination/completeness requires it. Convergent equations alone do not imply FVP. Exhausting variants for one term proves no global FVP claim. A bound on requested unifiers does not bound internal variant enumeration; even requesting a second unifier can diverge when only one exists.
6. Preserve generated variables (`#`, `%`, and `@` prefixes) as fresh names; do not submit colliding names. Preserve sort restrictions and compose substitutions without capture. Warnings, timeouts, and capped results are incomplete evidence even when the final line says no more solutions.

Run `assets/symbolic.maude` in a disposable directory. Its bit datatype has `zero`, `one`, and eligible flip equations. Confirm the binding B to `zero` for both unification examples, concrete variants `one` with B=zero and `zero` with B=one, and the one-step narrowing goal. The generic unreduced variant is also valid; do not mistake it for a concrete bit.

Sources: [Ax theories §13.3](https://maude.lcc.uma.es/maude-manual/maude-manualch13.html#x86-19000013.3), [unify §13.4](https://maude.lcc.uma.es/maude-manual/maude-manualch13.html#x86-19100013.4), [variant admissibility §14.3](https://maude.lcc.uma.es/maude-manual/maude-manualch14.html#x92-20200014.3), [variants/unification Ch. 14](https://maude.lcc.uma.es/maude-manual/maude-manualch14.html).

## Narrowing: symbolic reachability

1. Use narrowing when variables in the **initial state** must be instantiated to discover transitions. Ordinary search matches states against a target; `vu-narrow` unifies with both rule left-hand sides and the goal modulo the chosen variant theory.
2. Mark participating unconditional transition rules `[narrowing]`. Rules without that attribute are ignored. Left-hand sides cannot be bare variables; require explicit Ax coherence. Mark extra right-hand-side variables `[nonexec narrowing]` as documented in §15.7, and track fresh-variable scope rather than replacing them with arbitrary constants. Frozen positions remain excluded from narrowing.
3. Select eligible `[variant]` equations as above. Unmarked auxiliary equations can simplify after a step, but the manual explicitly warns that this combined narrowing-plus-simplification procedure is not complete in general. Name the topmost/linearity/normalized-substitution hypotheses used for a completeness argument (§15.3); accepting a module checks none of them.
4. Use:

   ```maude
   vu-narrow [1, 1] in BIT-STEP : cell(B:Bit) =>1 cell(one) .
   ```

   The first bound is requested solutions; the second is maximum narrowing depth. `=>1`, `=>+`, `=>*` retain their one/positive/zero-or-more meanings. `=>!` requires strong irreducibility under **narrowing**, not just an absence of ground rewrites.
5. Capture the resulting symbolic term, accumulated substitution, and **goal unifier**. The fixture returns `cell(flip(@1:Bit))`, accumulated B -> @1:Bit, and goal variant unifier @1:Bit -> zero; composing them yields initial `cell(zero)` and target `cell(one)`. Instantiate the initial state, intermediate states, and target, then replay the concrete rewrite before calling it a witness.
6. Add `{path}` when a narrowing derivation is needed, then use `show path STATE-NUMBER .` on the returned state identifier, not the solution ordinal. `{fold}`/`{vfold}` subsumption and `{filter,delay}` unifier controls have distinct semantics; read §§15.6.3–15.6.5 before selecting them. Folding is not a universal termination or proof guarantee.

Positive symbolic witnesses can establish existential reachability after concretization. A negative bounded result cannot establish global safety; even an exhausted symbolic search needs the theory's completeness assumptions and diagnostic status.

Sources: [completeness §15.3](https://maude.lcc.uma.es/maude-manual/maude-manualch15.html#x96-21600015.3), [admissible theories §15.5](https://maude.lcc.uma.es/maude-manual/maude-manualch15.html#x96-21800015.5), [vu-narrow §15.6](https://maude.lcc.uma.es/maude-manual/maude-manualch15.html#x96-21900015.6), [extra variables §15.7](https://maude.lcc.uma.es/maude-manual/maude-manualch15.html#x96-22600015.7).

## Reflection: inspect before descending

1. Import `META-LEVEL` and the object-level module deliberately. Module/term representations are Maude values, not arbitrary strings. Use `upModule('MODULE, false)` for the module's own statements/imports; true includes imported statements (flattening).
2. `upTerm(t)` returns the representation of t's **canonical form**: object-level normalization can happen before the metalevel operation. Preserve syntax explicitly if analyzing a redex instead of its value.
3. Choose a descent operation matching the task:
   - `metaReduce(Module, Term)` applies equations and returns `ResultPair` with `getTerm` and `getType` selectors.
   - `metaRewrite(Module, Term, Bound)` applies equations and up to Bound rules; `unbounded` has no rewrite bound. Neither bound constrains equation normalization time.
   - `metaSearch(Module, Initial, Target, Condition, Qid, Depth, Index)` enumerates search results; indices are zero-based. Read §17.6.6 for search-arrow encoding/result constructors before iterating.
   - Rule-label, strategy, match, and variant descent operations have separate signatures and return/error types. Read the relevant §17.6 subsection and inspect the installed prelude instead of guessing an overload.
4. Most descent operations are partial. Ill-formed representations can leave an unreduced term in a kind; out-of-band constructors such as `noParse`, `ambiguity`, or failure values must be handled according to the selected API. An unreduced call is not a successful result.
5. `downTerm(metaTerm, fallback)` returns the object's canonical term when valid in the fallback's kind; otherwise it can return the fallback. Choose a distinguishable error sentinel for production conversions and check result types first. A plausible fallback value can conceal an invalid representation.

After loading the finite-state fixture, the `smoke.maude` reflection expression checks a valid up/down round trip and reduction. To exercise reduction of an explicit object-level redex rather than a pre-normalized `upTerm(twice(3))`, run:

```maude
reduce in COUNTER-META :
  downTerm(getTerm(metaReduce(upModule('COUNTER-DATA, false),
    'twice[upTerm(3)])), 0) == 6 .
```

Expected `Bool: true`; inspect the ResultPair/type when adapting this expression to another signature. Reflection alone provides no confluence, termination, model validity, or exhaustive proof.

Sources: [reflection Ch. 17](https://maude.lcc.uma.es/maude-manual/maude-manualch17.html), [up/down §17.6.1](https://maude.lcc.uma.es/maude-manual/maude-manualch17.html#x114-25000017.6.1), [reduction §17.6.2](https://maude.lcc.uma.es/maude-manual/maude-manualch17.html#x114-25100017.6.2), [search §17.6.6](https://maude.lcc.uma.es/maude-manual/maude-manualch17.html#x114-25500017.6.6).

## SMT: verify the solver boundary

1. Inspect the selected binary/build and linked solver, then load its matching `smt.maude`. The 3.5.1 manual describes official binaries linked to Yices2 and a CVC4 source-build branch; do not assume an arbitrary distro binary or standalone solver provides the same interface.
2. Use the SMT modules' distinct sorts: `BOOLEAN`/Boolean, `INTEGER`/Integer, `REAL`/Real, and `REAL-INTEGER`. They are not Maude's Bool/Int/Rat; rational Real constants include a slash. Do not add subsort relationships or arbitrary operators to the supported SMT signatures.
3. Restrict queries to the documented quantifier-free Boolean and linear integer/rational theories. A parser accepting nonlinear syntax is not evidence of supported solver semantics. Invoke `check in MODULE : formula .` and preserve the solver's actual status/diagnostics; the manual warns the interface has limited validation and exception handling.
4. Smoke a satisfiable query and its contradictory conjunction before relying on the integration. Example after loading `smt.maude`:

   ```maude
   check in INTEGER : I:Integer > 0 .
   check in INTEGER : I:Integer > 0 and I:Integer < 0 .
   ```

   Require respectively `sat` and `unsat`. No answer, crash, or unknown status establishes no satisfiability claim. Unsatisfiability of the negation establishes validity only within the correctly encoded supported theory, not an invariant of the entire rewrite system.

Source: [SMT Ch. 16](https://maude.lcc.uma.es/maude-manual/maude-manualch16.html).
