# Proof and model troubleshooting

## Parser and well-formedness failures

| Symptom | Check | Repair |
|---|---|---|
| Error points before the apparent token | Undefined/reserved function symbol or malformed preceding term | Declare the intended symbol or correct the preceding syntax; re-run `--parse-only` |
| Fact arity warning | Same fact name used with different argument counts | Select one fact schema and update every occurrence |
| Fact capitalization warning | Case variants of one intended fact | Normalize spelling; fact names are case-sensitive |
| Fact multiplicity/persistence warning | Both `Fact` and `!Fact` used | Choose linear or persistent semantics and update every occurrence |
| Unbound variable | Action/conclusion variable absent from premises | Bind from input/state or generate fresh data with `Fr`/`new` |
| Free term in formula | Formula variable not quantified/guarded | Quantify it and place it in the required action guard |
| Dependency failure | Wrong/missing `maude` or `dot` on `PATH` | Select compatible binaries and verify versions before retrying |

Treat every well-formedness warning as a failed verification gate. `--quit-on-warning` prevents accidental proof claims from warning-bearing theories.

## Vacuous proofs

If a security lemma verifies but its claim action may be unreachable:

1. Add an `exists-trace` lemma reaching the claim under intended honest conditions.
2. Prove the role sequence and matching message data, not just one early event.
3. Inspect restrictions and state facts for impossible transitions.
4. Re-run executability before all-traces properties.

A falsified executability lemma invalidates security conclusions that depend on that path.

## Partial deconstructions

Run:

```bash
tamarin-prover --quit-on-warning --precompute-only model.spthy
```

Then inspect raw and refined sources in interactive mode.

Repair order:

1. Identify the premise and rule responsible for each open chain.
2. Add enforceable message tags or atomic sorts when the implementation can preserve them.
3. Add public inputs only when the value is genuinely attacker-constructible and prove executability remains intact.
4. Add a `[sources]` lemma stating sound prior origins for the term; prove it against raw sources.
5. Consider `--auto-sources` only as a candidate generator. Inspect and prove `AUTO_typing`, then confirm refined sources close the relevant chains.
6. Use a restriction only when it states a real environmental invariant; add a trace reaching the restricted path.

Never delete the troublesome premise, weaken the property, or filter the attack solely to make automation terminate.

## Non-termination or proof explosion

1. Classify timeout/non-termination as inconclusive.
2. Prove the executability and sources lemmas independently.
3. Inspect loops, repeated state production, AC/Diffie-Hellman/XOR equations, and partial deconstructions.
4. Reduce to one named lemma and retain the same semantics.
5. Open interactive mode and inspect which constraint repeats.
6. Try documented heuristics/tactics only after identifying the repeated constraint; record every option.
7. Minimize a reproducer without removing the behavior needed by the claim.

Heuristic success is proof-search behavior, not evidence that a model change is sound.

## Attack traces

When Tamarin finds a counterexample:

1. Confirm the attack reaches the intended claim action and uses an allowed compromise schedule.
2. Map each rule instance and term to a protocol/implementation step.
3. Distinguish a protocol attack from model over-approximation, missing tag/check, or impossible environment behavior.
4. Repair the protocol or model correspondence, not the lemma.
5. Preserve the attack as a regression target and re-run all lemmas.

## Interactive server

- Local: `tamarin-prover interactive model.spthy`, then `http://127.0.0.1:3001`.
- WSL: run inside WSL; open the loopback URL in the Windows browser.
- Remote: forward with `ssh -L 3001:localhost:3001 SERVERNAME` and keep the server bound to remote loopback.

Start from the intended model directory because the server loads theories from that directory. Avoid public binds and stop the server when the review ends.
