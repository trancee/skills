# Modeling and verification decisions

## Choose the representation

### Multiset rewriting rules

CHOOSE rules for explicit facts/transitions/actions/source reasoning:

```text
[ premises ] --[ actions ]-> [ conclusions ]
```

- `In(m)` consumes adversary-controlled network input.
- `Out(m)` exposes output to the adversary-controlled network.
- `Fr(~n)` obtains a unique fresh value.
- `Fact(...)` is linear and consumed when used as a premise.
- `!Fact(...)` is persistent and remains reusable.

### SAPIC+

CHOOSE one top-level SAPIC+ process for sequencing/parallelism/replication/branching/channels/global store. Translation generates rules and restrictions; review `new`, `in`, `out`, `event`, `!P`, `insert`, `lookup`, `delete`, `lock`, `unlock` semantics before use.

MIX process and handwritten rules only after reviewing translation-generated interactions.

## Terms and equations

ENABLE only used built-ins: hashing, asymmetric/symmetric encryption, signing/revealing signing, DH, bilinear pairing, XOR, multisets, natural numbers, reliable channels.

SORTS: quoted constants/`$A` public; `~n` fresh; `%n` natural counter; `#i` temporal. Public constants attacker-known.

CUSTOM equations need external convergence/FVP evidence. Prefer subterm-convergent theories. Tamarin does not check this condition; unsupported equations can silently invalidate results. Do not infer unmodeled implementation algebra.

PRIVATE function symbols block attacker application; neither freshness nor implementation isolation follows.

## State and protocol control

- Keep fact arity, spelling, capitalization, persistence, and multiplicity identical everywhere.
- Use persistent facts for reusable keys/directories and linear facts for session progression or consumed resources.
- Include role, peer, session identifier, transcript/agreed data, and stage in state facts where needed to prevent cross-role or cross-session confusion.
- Model key reveal, state reveal, corruption, erasure, and compromise timing with explicit rules and action facts.
- Use restrictions only for enforceable environmental assumptions. A restriction filters traces globally and can make a property vacuously true.

## Property patterns

### Executability

PROVE honest `exists-trace` paths reaching every claimed completion event; catch disconnected state/over-strong restrictions.

### Secrecy

LABEL claim actions. Schematic secrecy form (replace exception with a guarded formula):

```text
All x #i. Secret(x) @ i ==>
  (not Ex #j. K(x) @ j) | compromise_exception
```

SPECIFY compromise ordering: before | after | any time relative to claim.

### Authentication

USE distinct running/send and commit/receive actions; bind identities, roles, agreed data, prior peer event. Injectivity requires uniqueness.

### Guardedness

- Put universally quantified variables in action constraints immediately under an implication.
- Put existentially quantified variables in action constraints immediately under a conjunction.
- Build formula terms only from allowed quantified variables, public constants, free functions, and pairing.

### Observational equivalence

USE `--diff`, `diff` terms, and documented per-side rule/lemma syntax. Review both sides/restrictions. Sound approximation requires strict one-to-one rule mapping; limited restrictions. Failure can reflect approximation rather than protocol inequivalence.

### Accountability

DEFINE corruption, case-test blamed variables, accountability lemma. VERIFY every generated condition plus replacement property; separate from authentication.

## Proof evidence

For each lemma, record:

- exact theory digest and Tamarin/Maude versions;
- command-line options, preprocessor flags, and heuristic/tactic;
- trace quantifier and formula;
- verified/falsified/inconclusive result;
- proof skeleton or attack trace;
- source/partial-deconstruction status;
- assumptions and restrictions used.

MODEL proof != implementation proof. Compare encoding/parsing/transitions/compromise/acceptance separately.
