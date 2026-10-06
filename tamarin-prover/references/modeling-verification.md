# Modeling and verification decisions

## Choose the representation

### Multiset rewriting rules

Use rules when exact facts, transitions, action labels, or low-level source reasoning must remain visible. A rule has premises, action facts, and conclusions:

```text
[ premises ] --[ actions ]-> [ conclusions ]
```

- `In(m)` consumes adversary-controlled network input.
- `Out(m)` exposes output to the adversary-controlled network.
- `Fr(~n)` obtains a unique fresh value.
- `Fact(...)` is linear and consumed when used as a premise.
- `!Fact(...)` is persistent and remains reusable.

### SAPIC+

Use one top-level process when sequencing, parallelism, replication, branching, channels, or global store operations are clearer in process syntax. Tamarin translates the process to rules. Use `new`, `in`, `out`, `event`, `!P`, `insert`, `lookup`, `delete`, `lock`, and `unlock` only with their documented semantics.

Avoid combining handwritten rules and a process unless the translation-generated actions/restrictions and their interaction with the rules have been reviewed.

## Terms and equations

Built-ins include hashing, asymmetric/symmetric encryption, signing, revealing signing, Diffie-Hellman, bilinear pairing, XOR, multisets, natural numbers, and reliable channels. Enable only those used by the protocol.

Public constants such as `'label'` are attacker-known. Fresh values model random nonces and keys. Public variables `$A`, fresh variables `~n`, natural variables `%n`, and temporal variables `#i` have different sorts.

Custom equations must be convergent and have the finite variant property. Tamarin does not validate that mathematical requirement. Prefer subterm-convergent equations because unsupported theories can cause non-termination or incorrect results without warning. Never infer implementation-level algebraic properties that are absent from the model.

Private function symbols prevent adversary application; they do not automatically model fresh secret values and do not establish an implementation security boundary.

## State and protocol control

- Keep fact arity, spelling, capitalization, persistence, and multiplicity identical everywhere.
- Use persistent facts for reusable keys/directories and linear facts for session progression or consumed resources.
- Include role, peer, session identifier, transcript/agreed data, and stage in state facts where needed to prevent cross-role or cross-session confusion.
- Model key reveal, state reveal, corruption, erasure, and compromise timing with explicit rules and action facts.
- Use restrictions only for enforceable environmental assumptions. A restriction filters traces globally and can make a property vacuously true.

## Property patterns

### Executability

Prove an `exists-trace` lemma that reaches every claimed completion event under honest conditions. This catches disconnected states and over-strong restrictions.

### Secrecy

Label the claim point, then exclude adversary knowledge except for explicit compromise cases:

```text
All x #i. Secret(x) @ i ==>
  (not Ex #j. K(x) @ j) | compromise_exception
```

Decide whether compromise may occur before, after, or at any time relative to the claim.

### Authentication

Use separate running/sending and commit/receiving actions. Bind identities, roles, and all agreed data. Require the matching peer event before the commit. Add injectivity through uniqueness only when replay/session uniqueness is part of the claim.

### Guardedness

- Put universally quantified variables in action constraints immediately under an implication.
- Put existentially quantified variables in action constraints immediately under a conjunction.
- Build formula terms only from allowed quantified variables, public constants, free functions, and pairing.

### Observational equivalence

Use `diff`, `diff_rule`, and equivalence lemmas only after both sides and restrictions follow the documented diff-mode semantics. Tamarin's observational-equivalence mode soundly approximates equivalence but requires a strict one-to-one rule mapping and has limited restriction support; failure may reflect the approximation.

### Accountability

Define corruption semantics, case tests with free blamed-party variables, and accountability lemmas. Verify every generated condition and the replacement property. Treat this as a separate property branch, not a synonym for authentication.

## Proof evidence

For each lemma, record:

- exact theory digest and Tamarin/Maude versions;
- command-line options, preprocessor flags, and heuristic/tactic;
- trace quantifier and formula;
- verified/falsified/inconclusive result;
- proof skeleton or attack trace;
- source/partial-deconstruction status;
- assumptions and restrictions used.

A verified model is not an implementation proof. Compare serialization, parsing, role transitions, compromise behavior, and acceptance conditions against the implementation separately.
