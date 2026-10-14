# Install, model, and execute Core Maude

## Version and environment

Use the [manual 3.5.1, July 2025](https://maude.lcc.uma.es/maude-manual/), [official installation page](https://maude.cs.illinois.edu/get-maude), and [Maude3.5.1 release](https://github.com/maude-lang/Maude/releases/tag/Maude3.5.1). The tag resolves to commit `7269fc720072a2cd8b7222736721ba26dd3752b2`. Check latest stable when installing; keep a consumer's deliberate release pin. Manual versions, Core interpreter, library files, Full Maude and analysis extensions are separate identities.

Release archives cover Linux x86_64, macOS x86_64, and macOS arm64. Windows -> official recommendation is WSL with Linux distribution; separately distributed native Windows/strategy builds are not automatically the same release. Linux arm64 or other hosts -> verify a supported package/source build instead of executing a wrong-architecture binary. Distro packages can lag. Source builds follow the chosen tag's INSTALL/configure requirements, not generic compiler assumptions.

For the Linux 3.5.1 archive `Maude-3.5.1-linux-x86_64.zip`, official asset SHA-256 is `72ed1ca87e3b3d0dfc6ee1436baf154bf04c45ff97d521bec040c5e8dfc8f92c`. Download/verify/extract into an owned tools directory. Preserve the distribution's `prelude.maude`, `model-checker.maude`, and other library files alongside the executable. Do not install a lone binary paired with stale library modules.

```bash
maude --version
maude --help
```

Set MAUDE_LIB to the matching distribution directory when needed. Prelude lookup is MAUDE_LIB, executable directory, then current directory. User `load`/`in` file lookup starts at the current directory, then MAUDE_LIB, then executable directory; relative paths depend on the running interpreter's cwd. File extension inference can try .maude/.fm/.obj, but use explicit names for automation.

Files contain commands as well as modules: review them before loading. They can change working directory, enter loops, quit, invoke system commands, or trigger external IO. Avoid `-trust`, `-allow-files`, `-allow-dir`, `-allow-processes` unless the reviewed task explicitly requires those capabilities. Pure rewriting proofs need none of them. Permissions flags are not an OS sandbox.

Sources: [manual Ch. 2](https://maude.lcc.uma.es/maude-manual/maude-manualch2.html), [Appendix A flags/loading](https://maude.lcc.uma.es/maude-manual/maude-manualap1.html).

## Module and signature design

| Purpose | Core syntax | Meaning |
| --- | --- | --- |
| Pure data/functions | `fmod NAME is ... endfm` | Membership equational theory, executed by simplification |
| State transitions | `mod NAME is ... endm` | Same data/equations plus rewrite rules |
| Strategy control | `smod NAME is ... endsm` | Separate control over rule application; see advanced reference |

Use sorts/subsorts for data domains, `[Sort]` kinds for broader error/partial expressions, and `op name : Domain -> Range .` for operators. Underscores mark arguments of mixfix operators. Declare variables before use or use explicit inline `X:Sort`. End declarations, equations, rules, and analysis commands with a whitespace-separated ` .`; module end keywords and load/quit commands follow their own syntax.

`parse in MODULE : term .` isolates parsing from evaluation. Parentheses and `(term).Sort` disambiguate overloads; `prec` uses lower numbers for tighter binding and `gather` controls association. A kind-level result `[Sort]` rather than intended Sort can indicate an unreduced partial/error term. Resolve missing equations, impossible sorts, overloads, and membership conditions rather than accepting a syntactically parsed term as valid data.

`protecting M .` promises imported data is unchanged (no junk/no confusion); it is a semantic claim, not an automatically checked guard. Use extending/including only with their intended semantics. Preserve the existing module's import ownership; parameterized theories/views require explicit sort/op mappings and semantic obligations. Read [Ch. 7](https://maude.lcc.uma.es/maude-manual/maude-manualch7.html) when composing/instantiating modules rather than copying flattened duplicates.

## Equations, axioms, and transitions

Equations (`eq`) compute canonical data representatives; rules (`rl [label] : lhs => rhs .`) express observable transitions. Changing a transition into an equation collapses intermediate states and can invalidate a reachability/LTL argument. A model-checker wrapper should use including rather than claim it protects a module whose State typing it changes.

Use `[assoc comm id: empty]` for a multiset operator when mathematically intended. Do not orient associativity/commutativity as ordinary equations: commutativity written `eq f(X,Y) = f(Y,X) .` loops. Identity/AC matching can match empty components and unexpected contexts; inspect matches instead of assuming textual structure.

Executable equations/memberships must satisfy variable/admissibility constraints and ground confluence, termination, and sort-decreasingness modulo declared axioms. The interpreter does **not** establish these properties merely by accepting a module. Require separate proof/tool evidence when the analysis claim depends on them; sample reductions are smoke evidence only.

System rules must be admissible and ground coherent with equations modulo axioms: normalization must not remove possible rule transitions. Rules need not terminate/converge; equations still must normalize as assumed. Conditions evaluate left-to-right and may introduce variables through matching/rewrite conditions only under the documented admissibility rules. `nonexec` removes statements from default execution, not from their declarative meaning. `[owise]` applies to equations as fallback, not to rules or arbitrary declaration priority.

`frozen` blocks rule rewriting below selected arguments; it does not freeze ordinary equational simplification. Operator `strat` controls equation evaluation and can alter operational completeness. Keep these attributes in the verification semantics; do not add them merely to hide state explosion or a bad transition.

Sources: [syntax Ch. 3](https://maude.lcc.uma.es/maude-manual/maude-manualch3.html), [functional Ch. 4](https://maude.lcc.uma.es/maude-manual/maude-manualch4.html), [system Ch. 5](https://maude.lcc.uma.es/maude-manual/maude-manualch5.html).

## Commands and diagnostics

| Command | What is actually exercised |
| --- | --- |
| `reduce in M : t .` | Equations/memberships only; ignores transition rules |
| `rewrite [20] in M : t .` | One rule-fair execution; at most 20 rule applications |
| `frewrite [20, 1] in M : t .` | Rule/position-fair execution; not all paths or substitution fairness |
| `search [1, 10] in M : initial =>* pattern .` | Breadth-first reachability; one solution / depth at most 10 |
| `match in M : pattern <=? subject .` | Matcher substitutions; use xmatch for extension when required |
| `show module M .` | Imported/current signature and statements |
| `set trace on .` / `set trace off .` | Equation/rule execution evidence; can be very verbose |

Use `continue n .` only for the compatible preceding computation and record the cumulative exploration; another command can replace the stored context. Inspect `show search graph .` and `show path N .` immediately after the relevant search. State number N is not solution ordinal. Bound the command **and** wall-clock execution; equation loops are not bounded by rewrite-step limits.

A `rewrite` result is one execution, not exhaustive behavior. A stopped result at a bound need not be final. Prefer explicit `in M :` on every command; the implicit current module changes after loads and analysis.

For noninteractive sessions, supply a command file plus quit on stdin, keep `-no-banner -no-ansi-color -no-wrap`, and preserve diagnostics. `-batch` disables Ctrl-C handling; it does not make Maude stop on a malformed command. Observed 3.5.1 parse errors can print Warning while the process exits 0. Also, compilation is lazy: some warnings only appear upon actual reduction/rewrite. Accept neither exit 0 nor load-only as a correctness gate.

Sources: [execution Ch. 5](https://maude.lcc.uma.es/maude-manual/maude-manualch5.html), [Appendix A](https://maude.lcc.uma.es/maude-manual/maude-manualap1.html), [debugging Ch. 21](https://maude.lcc.uma.es/maude-manual/maude-manualch21.html).
