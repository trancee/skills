# Reachability, invariants, and LTL

## Establish analysis preconditions

Choose one top-level state sort/kind and initial term. Preserve equations/axioms that identify states, admissible rule conditions, and frozen positions. Equation normalization must be ground Church-Rosser/terminating modulo axioms; rules must be ground coherent with equations. Maude assumes these conditions rather than checking them. Purely equational rule conditions are required by the manual's built-in model-checking setup.

Finite reachable state space is the termination precondition for exhaustive ground exploration/model checking. Bounded natural-number syntax, a finite state datatype, or a quotient is not enough by itself: check that rules, unbounded collections, IO/environment components, and data growth cannot create infinitely many states. Record proof obligations instead of inferring finiteness from a short trace.

Sources: [admissibility/coherence §5.3](https://maude.lcc.uma.es/maude-manual/maude-manualch5.html#x40-670005.3), [invariant analysis Ch. 11](https://maude.lcc.uma.es/maude-manual/maude-manualch11.html), [Kripke structures §12.2](https://maude.lcc.uma.es/maude-manual/maude-manualch12.html#x84-18100012.2).

## Search and witness paths

| Arrow | Reachability target |
| --- | --- |
| `=>1` | exactly one rule-rewrite step |
| `=>+` | one or more rule steps |
| `=>*` | zero or more; includes the initial state |
| `=>!` | canonical state with no enabled further rule transition |
| `=>#` | state with multiple distinct successors |

Use `search [n, m] in MODULE : initial =>* pattern such that condition .`: n caps solutions, m caps depth; `[, m]` sets depth only. Search is breadth-first. Equational simplification is not counted as a rule step, so bounds do not stop an equation loop. Matrix-like enumeration of rewrite paths is not what search returns: canonical states and matching substitutions can merge paths.

Concrete fixture commands, after loading `assets/finite-state.maude`:

```maude
search [1, 5] in FINITE-COUNTER : q0 =>* q2 .
show path 2 .
show path labels 2 .
show path states 2 .
show search graph .
```

The fixture's q2 solution is state 2 with advance-0/advance-1 labels. For another model, use the **state number printed in its solution**, not the solution ordinal or this example's number. Issue path/graph commands before another search replaces the context. `continue 1 .` can resume compatible stored exploration; record the cumulative bounds/results.

A sample `rewrite`/`frewrite` result is one run. Position/rule fairness of an execution command is not an assumption that automatically removes unfair paths from exhaustive search or LTL.

Sources: [search §5.4.3](https://maude.lcc.uma.es/maude-manual/maude-manualch5.html#x40-710005.4.3), [Appendix A search/continue](https://maude.lcc.uma.es/maude-manual/maude-manualap1.html).

## Invariants as negative reachability

Search for any reachable violation, using `=>*` so an initially false invariant is detected. Predicates must reduce correctly for all relevant states. For the finite fixture, a bad-state query is:

```maude
search in FINITE-COUNTER : q0 =>* bad .
```

This terminates with No solution because all three reachable constructors q0/q1/q2 were explored; bad is declared but unreachable. Adding q1 => bad changes this result and invalidates the safety claim. Search for deadlocks with `=>!` and a variable matching the entire state sort/kind; use an explicit inline variable such as `S:CounterState` for this fixture.

Classify the outcome precisely:

- Found witness -> a concrete reachable violation under the model semantics; retrieve/replay its path.
- Completed exhaustive search, no witness, finite reachable graph and executability assumptions -> supports the invariant for the specified initial states/model.
- Depth bound, interruption, resource limit, or incomplete symbolic algorithm -> only a bounded/no-witness observation, not unbounded safety.
- A solution cap alone need not invalidate a negative result: `search [1]` that finds **zero** matches and fully exhausts the graph has not hit its solution cap. If a result cap is reached, enumeration is incomplete.
- Infinite-state unbounded search may not terminate. Don't turn silence or stopped computation into No solution/proof.

## LTL predicates and concrete verdicts

Load `model-checker.maude` with `load`/`in`, then import its modules inside a system wrapper. `SATISFACTION` supplies State, Prop and `_|=_`. The predicate wrapper puts the chosen state sort below State and supplies equations reducing every relevant state/proposition to Bool. Use `ceq ... if ... .` for conditional equations; `eq ... if ...` is invalid.

The packaged fixture contains complete, executable COUNTER-PROPS and COUNTER-CHECK modules. Its safe predicate is false at bad and true elsewhere; at-q2 is true only at q2. Inspect the equations and evaluate them on both positive/negative states before analyzing temporal properties.

```maude
reduce in COUNTER-PROPS : bad |= safe .
reduce in COUNTER-PROPS : q0 |= at-q2 .
reduce in COUNTER-CHECK : modelCheck(q0, [] safe) .
reduce in COUNTER-CHECK : modelCheck(q0, <> at-q2) .
```

Expected: false, false, true, then counterexample. The final formula fails because q0 -> q1 -> q0 can repeat forever without visiting q2. Merely showing that q2 is reachable does not establish that every path eventually reaches it.

| Formula | Path interpretation |
| --- | --- |
| `[] p` | always p |
| `<> p` | eventually p |
| `O p` | p in the next state |
| `p U q` | p until q, with q eventually reached |
| `~ p`, `p /\ q`, `p \/ q`, `p -> q` | negation, conjunction, disjunction, implication |

The built-in modelCheck quantifies over **all** paths of the Kripke structure. Deadlocks receive self-loops to totalize the relation; a deadlocked state is not a finite path that can be ignored. Fairness requirements must be modeled/expressed explicitly, not assumed from the simulation scheduler.

`true` supports the property only for the exact model/initial state and assumptions. A counterexample is `counterexample(Prefix, Loop)`: a finite prefix followed by an infinitely repeated cycle. Each `{State, RuleName}` records a state and outgoing transition; rule labels are quoted identifiers, `nil` is an empty prefix, and deadlock/unlabeled transitions have special names. Replay the listed states/rules/predicates. `show path N` is a **search graph** command, not a direct modelCheck-lasso printer; construct a corresponding search/replay when needed.

Sources: [LTL §12.1](https://maude.lcc.uma.es/maude-manual/maude-manualch12.html#x84-18000012.1), [modelCheck §12.3](https://maude.lcc.uma.es/maude-manual/maude-manualch12.html#x84-18200012.3).

## LTL+ existential witnesses in 3.5.1

MODEL-CHECKER+ includes LTL+ with explicit A_/E_ outer path quantifiers. A returns true or a counterexample; E returns a witness lasso or false, via negation of the corresponding universal check. This is not arbitrary nested CTL/CTL* quantification.

After loading the finite fixture:

```maude
mod COUNTER-WITNESS is
  including COUNTER-PROPS .
  including MODEL-CHECKER+ .
endm
reduce in COUNTER-WITNESS : modelCheck+(q0, E (<> at-q2)) .
reduce in COUNTER-WITNESS : modelCheck+(q0, A ([] safe)) .
```

Observed: witness lasso through q2, then true. Parenthesize the inner formula: released 3.5.1 does not parse the unparenthesized `E <> p` / `A [] p` forms. An existential witness demonstrates one path, not universal liveness.

Sources: [LTL+ §12.6](https://maude.lcc.uma.es/maude-manual/maude-manualch12.html#x84-18500012.6), [released implementation](https://github.com/maude-lang/Maude/tree/7269fc720072a2cd8b7222736721ba26dd3752b2).

## Infinite-state abstraction obligations

A finite equational quotient can support an infinite-state safety claim only with justified abstraction soundness. Added equations must preserve the relevant predicates, protect Bool, normalize consistently, and retain rule coherence. Adding equations just to reduce state count is not a soundness argument.

Under the manual's invariant-preserving quotient obligations, a proved safety invariant on the abstraction transfers to the concrete model; an abstract counterexample may be spurious and must be concretized/refined. This safety transfer does not automatically preserve arbitrary LTL/fairness/next properties. Keep external termination/confluence/sufficient-completeness checker assumptions and tool versions explicit; these tools are not implied by installing Core Maude.

Source: [abstractions §11.4](https://maude.lcc.uma.es/maude-manual/maude-manualch11.html#x81-17800011.4).
