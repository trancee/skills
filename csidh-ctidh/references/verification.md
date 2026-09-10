# Verification and evidence plan

## Evidence layers

| Claim | Minimum evidence |
| --- | --- |
| Arithmetic/action correctness | Exact source vectors plus independent algebraic/property checks |
| Interoperability | Cross-action agreement with independent matching implementation |
| Public-key safety | Canonical/invalid/wrong-class validation corpus and bounded fuzzing |
| Constant-time | Exact binary/target static and dynamic timing/cache evidence |
| Fault resistance | Threat-model-specific injection/power/EM campaign and countermeasure analysis |
| Security level | Current dated classical/quantum attack estimate with full resource model |
| Deployment suitability | Complete target handshake latency, memory, availability, and protocol review |

One row never implies another. A commutativity test does not validate public keys; `timecop` does not establish fault resistance; a paper estimate does not establish standardization.

## Functional matrix

For each construction × parameter × implementation/dispatch path:

1. Generate valid secret/public key pairs at distribution boundaries.
2. Compute both action orders and require canonical shared-curve equality.
3. Compare field arithmetic, isogenies, action steps, and final public keys to pinned vectors/baseline where available.
4. Encode/decode exact boundary values and reject noncanonical alternates/trailing data.
5. Validate accepted public keys and reject singular, ordinary, wrong-class/nonsupersingular, cross-parameter, and cross-construction keys.
6. Force RNG, allocation, stack/scratch, validation, action, and KDF failure; require no key output and cleanup.
7. Exercise repeated/static and fresh/ephemeral keys according to protocol policy.
8. Test concurrent operations with independent secret/RNG/scratch state.

## Protocol matrix

- Both role/order views derive the same session key.
- Swapped roles, public keys, construction/parameter ID, ciphersuite, version, transcript, or context derive different keys or fail.
- Tampered public keys fail validation before secret action.
- Key confirmation succeeds only for matching transcript/session.
- Replay/downgrade/hybrid-component failure follows the containing protocol.
- Raw shared-curve bytes never reach application cipher APIs.

## Independent interoperability

Record producer, consumer, paper/source commit, parameter constants/digest, encoding, validation, and action algorithm. Exchange public keys both ways and compare canonical action/KDF outputs.

Do not call two wrappers around the same source independent. Do not compare CSIDH and CTIDH or parameter sets based solely on key length.

## Invalid-input fuzzing

Fuzz public-key decoding and validation with bounds on time/work/memory. Seed with valid/noncanonical field elements, singular curves, ordinary/wrong-class curves, parameter boundary values, truncated/extended encodings, and cross-variant keys.

Assert:

- No crash, undefined behavior, hang, unbounded retries, or secret action before validation.
- Acceptance only for canonical fully validated selected-parameter keys.
- Stable protocol-level failure without attacker-useful detail.
- No partial/shared output on failure.

Run memory, undefined-behavior, and thread sanitizers supported by the toolchain. Fuzz optimized and fallback dispatch paths.

## Constant-time and fault testing

For each binary/target:

- Run implementation CT tooling (`timecop` or equivalent) separately from functional tests.
- Inspect generated assembly for secret-dependent branches/table access and unexpected division/helper calls.
- Measure timing/cache distributions over controlled secret classes and public inputs.
- Exercise RNG/rejection/exceptional field paths.
- For physical/fault threats, inject skips/corruptions across real/dummy isogeny operations, validation, final checks, and KDF handoff.
- Verify failures do not reveal whether a secret digit caused real versus dummy work.

Scope every conclusion to compiler, flags, CPU, dispatch path, hardware, measurement method, and statistical power.

## Performance and availability

Measure complete key generation, validation, action, KDF, and protocol confirmation. Include malformed-key load, high percentiles, memory/stack, code size, energy, and concurrent capacity. Compare against a supported alternative using the same target and security assumptions.

If conservative parameters violate latency/resource requirements, report unsuitable rather than weakening validation or reverting to disputed estimates.

## Deterministic provenance

Record source/archive digests, parameter-file digests, compiler/toolchain container, build flags, binary hash, test-vector digest, and commands. Rebuild twice and compare binaries or explain toolchain nondeterminism before side-channel conclusions.

## Reporting

Copy `assets/isogeny-review-report.md`. Keep security estimates, correctness, constant-time, fault resistance, protocol properties, and operational suitability as separate claims with separate evidence.
