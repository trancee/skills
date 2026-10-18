# Lean programming and elaboration debugging

Use the Lean **4.35.0** reference for semantics; *Functional Programming in Lean* currently tests its tutorial examples with **4.33.0**. Keep the consumer's pinned compiler, existing module headers and import/export conventions.

## Model the data and effects

1. Use `def` for computable definitions, `inductive` for alternatives/recursive data, and `structure` for records. Distinguish uniform parameters from indices that vary between constructors; state universe parameters when genuinely polymorphic. Reuse existing library types and instances before defining another representation.
2. Write explicit argument/result types at unclear boundaries. Distinguish `(α : Type u)` explicit parameters, `{α : Type u}` inferred parameters, and `[Class α]` instance parameters. Use `@declaration` and named arguments to inspect/control inferred arguments rather than relying on guessed elaboration.
3. Match constructors exhaustively. In dependent matches, a branch can refine an index/type; use a named discriminant (`match h : value with`) when its equality is needed. When dependent substitution/generalization fails, inspect the precise expected type before altering the indexed family.
4. Keep pure transformations separate from IO. Use `Option α` for absence and `Except ε α` for recoverable errors with a meaningful payload. Match both cases; a default value is correct only if the domain contract permits it.
5. For indexed access, choose a bound proof (`xs[i]'h` or an `if h : i < xs.size` branch) or optional access (`xs[i]?`). Treat `!`/panic-based access as a different runtime contract, not a proof of valid indexing or an ordinary recoverable error.

Sources: [inductive types](https://lean-lang.org/doc/reference/4.35.0/The-Type-System/Inductive-Types/), [pattern matching](https://lean-lang.org/doc/reference/4.35.0/Terms/Pattern-Matching/), [do syntax](https://lean-lang.org/doc/reference/4.35.0/Functors___-Monads-and--do--Notation/Syntax/).

## Justify recursion and isolate execution-only code

| Form | Use and boundary |
| --- | --- |
| Structural recursion | Recurse on strict subterms; `termination_by structural n` explicitly selects the decreasing parameter. |
| Well-founded recursion | Give `termination_by` a decreasing measure; inspect the actual decrease goal and discharge it with local facts/`decreasing_by`. Reduction can involve large proofs; use generated equation theorems for reasoning. |
| `partial_fixpoint` | Separate supported fixed-point construction, with monotonicity/other prerequisites and generated reasoning principles; read its reference before use. It is not the `partial` modifier. |
| `partial` | Kernel-opaque function with a nonempty codomain; can execute without a termination proof. It does not provide the same unfolding/equation reasoning as a total definition. |
| `unsafe` | Exempt from kernel checking, permits low-level/general recursive code; unsafe dependencies propagate. A replacement runtime implementation must agree with its safe model for runtime correspondence. |
| `noncomputable` | Valid specification/proof-level definition exempt from compilation, e.g. data chosen nonconstructively. Not itself a logical inconsistency and not executable by `#eval`. |

On termination failure, inspect the recursive call, branch assumptions and decreasing relation. Supply the missing fact or measure rather than changing a requested total function to `partial`. Do not assume every decrease goal is an inequality of natural numbers.

Sources: [recursive definitions](https://lean-lang.org/doc/reference/4.35.0/Definitions/Recursive-Definitions/), [declaration modifiers](https://lean-lang.org/doc/reference/4.35.0/Definitions/Modifiers/).

## Diagnose the first elaboration obstruction

1. Read the exact goal (`⊢`) and local context at the failing term, not just the tactic name. Reduce to one declaration/input while preserving its imports and types.
2. Use `#check declaration` to inspect its type; `#print declaration` to inspect the definition; `#synth Class Type` to probe an instance. A `#check` result containing metavariables is not a complete implementation.
3. Reveal hidden arguments with scoped `set_option pp.explicit true` and universes with `pp.universes`. Add `(term : ExpectedType)` or `show ExpectedType from term` at the first ambiguous boundary. Close every placeholder/metavariable before delivery.
4. Unknown identifier -> verify namespace, spelling, case-sensitive module path, export visibility and exact API under the pin. Build imports through Lake before checking a dependent file; an editor may have elaborated unsaved/different content.
5. Instance failure -> identify the unresolved type/parameter, inspect local instances and `#synth`, then scope `set_option trace.Meta.synthInstance true` to the reproducer. Fix the missing type, import or appropriate instance; do not install a broad global instance or suppress reducibility warnings to mask it.
6. Coercion/numeral failure -> distinguish the expected type from inferred type and `OfNat` synthesis. A coercion from Nat does not automatically supply a numeral instance for a new type. Prefer explicit conversions at semantic boundaries over ambiguous coercion chains.

Sources: [interaction commands](https://lean-lang.org/doc/reference/4.35.0/Interacting-with-Lean/), [instance synthesis](https://lean-lang.org/doc/reference/4.35.0/Type-Classes/Instance-Synthesis/), [coercions](https://lean-lang.org/doc/reference/4.35.0/Coercions/).

## Run programs separately from checking proofs

- `#eval expression` compiles and executes; it can run IO and partial functions, and erases proofs/types. IO output from **this command** is captured in Lean's message log. It is a runtime observation, not a theorem about all inputs.
- `#reduce expression` computes using definitional reduction, not native execution. Proof-heavy well-founded definitions may reduce slowly; kernel-opaque partial functions do not unfold this way.
- `rfl` proves definitional equality; ordinary `decide` constructs a proof for a decidable proposition. Native evaluation modes add a different trust boundary: audit them through the proof/trust branch instead of equating them with `#eval` or pure kernel reduction.
- `#eval` rejects terms transitively depending on `sorry`; repair incomplete proofs rather than bypassing this with `#eval!`.
- Use `main : IO Unit` for a simple program, or an argument-taking `main : List String → IO UInt32` when command-line parsing and explicit exit codes are needed (as in `assets/Main.lean`). Build/run the configured executable through Lake; its stdout/stderr are actual process streams, not editor messages. Fix a deterministic working directory before interpreting relative file paths.
- In the new module system, compile-time execution can require `meta import`/`public meta import`. The language server can make more definitions available for experimentation than a batch build; require a real terminal build of the selected module.

Gate: definitions have their intended types/termination story, proof checking completes, and native program outputs/error exits match the contract on positive and boundary inputs.

## Profile the compiled hot path

Lean uses reference counting and can update uniquely referenced arrays/strings in place. Retaining an alias of an old value can force a copy. Keep data flow single-owner where practical; avoid adding copies/allocations simply to emulate mutation.

When performance is the task, run a representative **compiled** program. Use `dbgTraceIfShared` for alias diagnosis and scoped `trace.compiler.ir.result` to inspect allocation/reference-count operations. `#eval` sharing can differ from compiled execution; neither source-level mutation syntax nor one benchmark proves allocation-free behavior for all callers. Remove diagnostic traces after measuring.

Source: [reference counting and compiler IR](https://lean-lang.org/doc/reference/4.35.0/Run-Time-Code/Reference-Counting/).