---
name: csidh-ctidh
description: "Designs, integrates, implements, reviews, and tests CSIDH-family commutative supersingular isogeny group actions and non-interactive key exchange. Use when handling CSIDH, CTIDH, dCSIDH/dCTIDH, public-key validation, parameters, class-group actions, constant-time or fault-resistant implementations, KDF/transcript binding, or high-security evidence. Don't use for SIDH/SIKE, generic isogeny mathematics, SQISign or other isogeny signatures, standardized KEM migration, or certification claims."
compatibility: "Covers research CSIDH-family proposals and implementations available 2026-09-10. No CSIDH/CTIDH variant is a NIST or IETF standard. Exact parameters, software, CPU features, attack estimates, and maintenance status must be refreshed and pinned. Inspector requires Python 3.11+."
metadata:
  category: "cryptography"
  source: "https://isogeny.org/"
  sourceVersion: "CSIDH, CTIDH, quantum evaluation, velusqrt, high-security CSIDH, dCTIDH, and sina1777/CSIDH@770d2a198e109f30014af87ae38502f03c61203a inspected 2026-09-10"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-09-10T21:24:48+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-09-10T21:36:15+02:00"
---

# CSIDH and CTIDH

## Step 1: Fix the construction and security contract

1. CLASSIFY CSIDH | CTIDH | dCSIDH/dCTIDH | class-group action | NIKE integration | parameter review | constant-time implementation | fault-hardening | optimization study.
2. IDENTIFY exact paper/specification revision, source commit/archive, parameter set and prime, secret-exponent distribution, public-key encoding, action algorithm, validation algorithm, attack model, protocol role, target platforms, and claimed classical/quantum security.
3. READ `references/status-parameters.md` before selecting parameters or making security/standardization claims.
4. KEEP CSIDH-family commutative group actions separate from SIDH/SIKE, signature schemes, and generic supersingular-isogeny constructions. SIDH/SIKE breaks neither prove nor disprove CSIDH security.
5. TREAT every CSIDH/CTIDH parameter and implementation as a research artifact unless a separately reviewed deployment profile establishes otherwise; never call it NIST/IETF standardized or certified.
6. STOP when the protocol leaves construction, parameter tuple, public-key validation, transcript/KDF, or attack-cost model implicit.

Completion: every key/action binds one exact construction, implementation revision, parameters, validation algorithm, protocol, and dated security model.

## Step 2: Inspect the project boundary

RUN from the repository root:
```bash
python3 scripts/inspect-project.py --root . --json
```

1. CONFIRM CSIDH/CTIDH/dCTIDH source and parameter pins, public/secret APIs, validation, shared-action callsites, KDF/transcript binding, secret-independent execution, dummy operations, fault tests, RNG, CPU dispatch, CT tooling, custom parameter generation, and SIDH/SIKE naming.
2. TREAT findings as review leads; inspect the complete keygen/validate/action/derive path before conclusions.
3. READ `references/protocol-validation.md` for protocol or public-key handling. READ `references/implementation-security.md` before implementation, optimization, constant-time, or fault-resistance changes.

Completion: all external encodings, secret-action entry points, parameter owners, validation steps, derivation sites, and target implementations are enumerated.

## Step 3: Select parameters and implementation conservatively

1. PIN the exact paper plus source commit/archive and parameter identifier; do not combine constants or claims across CSIDH, CTIDH, dCSIDH/dCTIDH, or independent forks.
2. REJECT the original CSIDH proof-of-concept as production evidence. Treat CTIDH 20210523 and other historical archives as research baselines with their documented CPU/toolchain limits.
3. VERIFY current maintenance and independently review active research repositories before adoption; recent commits do not establish deployment suitability.
4. USE `sina1777/CSIDH@770d2a198e109f30014af87ae38502f03c61203a` `SW/` only as a modified C golden model for that repository's FPGA/ASIC co-verification. Never label it the canonical/official CSIDH reference or production constant-time software.
5. REBUILD that C model from reviewed source; ignore committed `main`/`libcsidh.so` binaries. Resolve missing repository-level license/provenance before copying or redistribution.
6. DOCUMENT prime size, key size, secret space, action cost, validation cost, classical/quantum attack estimates, quantum memory/depth/query assumptions, and estimate date.
7. AVOID treating the original 511/512-bit proposals as a generic “128-bit post-quantum” choice. Use current conservative analysis for the exact construction; high-security proposals can require much larger primes and substantial latency.
8. ADOPT `velusqrt` only as a pinned action-implementation optimization whose formulas, degree/preconditions, constant-time behavior, and target performance are verified; never treat it as a protocol or security upgrade.

Completion: the selected tuple has current evidence, supported target measurements, explicit uncertainty, and no borrowed security label.

## Step 4: Define typed keys and validated actions

1. DEFINE distinct types for encoded public key, decoded curve, validated public key, secret exponent vector, shared curve/action output, and derived session key.
2. PARSE public field/curve values canonically and reject wrong length, out-of-range/noncanonical field elements, singular curves, invalid model points, and parameter mismatch.
3. VALIDATE membership in the expected supersingular isogeny class with the exact selected validation algorithm. A range or nonsingularity check alone is insufficient.
4. APPLY the secret class-group action only to validated public keys; never combine decode, validation, and secret action into a permissive fallback.
5. KEEP CSIDH and CTIDH key spaces/action algorithms coupled to their parameters. Reject cross-variant keys even when encoded lengths or curve models resemble each other.
6. PROPAGATE validation/action/RNG failures without shared-key output. Bound validation and malformed-input work against denial-of-service.

Completion: untrusted bytes reach secret computation only through exact canonical decoding and full selected-parameter validation.

## Step 5: Bind NIKE output to a protocol KDF

READ `references/protocol-validation.md`.

1. SERIALIZE the shared curve/action output canonically; never use an in-memory curve representation or raw coefficient directly as an application key.
2. DERIVE keys with a specified KDF that binds protocol and ciphersuite versions, exact construction/parameter identifier, both canonical public keys, roles/order, shared output, context, and transcript.
3. DEFINE public-key ordering explicitly for the commutative NIKE flow; role labels prevent reflection and unknown-key-share ambiguity.
4. ADD authentication, key confirmation, forward-secrecy story, replay/session binding, and hybrid composition only through a reviewed containing protocol. Bare CSIDH NIKE supplies none automatically.
5. REJECT all-zero/default outputs, validation bypass, action failure, KDF failure, and transcript mismatch before key use.
6. ERASE secret exponents, action intermediates, shared curves, and pre-KDF material according to the target threat model.

Completion: the containing protocol derives context-bound keys from validated peers and states every authentication/session property separately.

## Step 6: Preserve constant-time and fault invariants

READ `references/implementation-security.md`.

1. KEEP secret exponent digits, sign, isogeny selection, point selection, rejection counts, memory indices, and action progress independent of observable timing/cache/branch behavior according to the selected algorithm.
2. VERIFY the exact compiler, flags, architecture, ADX/vector dispatch, integer instructions, RNG, allocator, and generated code. A “constant-time” source name or `timecop` pass is not a cross-target proof.
3. RUN functional tests and constant-time tooling separately; CTIDH's historical build requires a separate `make timecop` path.
4. REVIEW real/dummy action schedules for fault injection. Dummy-based balancing can leak secret information when faults distinguish or skip real work.
5. DEFINE target-specific countermeasures: dummy-free schedule, randomized order/blinding, recomputation/consistency checks, fault detection, physical protections, or explicit absence from the threat model.
6. PREVENT secret-dependent diagnostics, core dumps, traces, performance counters, or retries from exposing the exponent vector.
7. FOR the sina1777 C model, audit/remove diagnostic `printf` paths and hard-coded private vectors before any secret-bearing run; its inspected source explicitly contradicts the repository-level constant-time characterization. Treat `-march=native -O3 -DNDEBUG` as an unreviewed target-specific build, and replace process-exiting RNG behavior with caller-visible failure for integration.

Completion: timing/cache/power/fault claims are scoped to exact binaries and targets with both functional and adversarial evidence.

## Step 7: Verify the full construction

READ `references/verification.md`.

1. RUN exact source vectors/tests for every selected parameter and implementation path, then independently check group-action commutativity and public-key validation.
2. TEST keygen/action agreement, invalid/cross-parameter keys, canonical boundaries, singular/nonsupersingular curves, malformed encodings, RNG failures, and KDF/transcript/role mismatch.
3. CROSS-CHECK compatible outputs with an independent implementation pinned to the same construction/parameters; do not compare CSIDH and CTIDH as interchangeable algorithms.
4. FUZZ decoders and public-key validation with bounded work; run memory/undefined/thread sanitizers where supported.
5. RUN target timing/cache tests and, when physical faults are in scope, fault/power/EM campaigns that exercise real and dummy operations.
6. BENCHMARK keygen, validation, action, complete handshake, memory/stack, code size, and failure paths on the deployment target; report tail latency, not only averages.
7. COPY `assets/isogeny-review-report.md`; record exact tuple, sources, attack model, validation, protocol binding, target evidence, performance, and limitations.

Completion: functional, invalid-input, interoperability, deterministic-build, side-channel/fault, and target performance evidence cover every claimed path.

## Error Handling

- Request says SIKE/SIDH -> stop this workflow and use a retirement/security-migration path; these are distinct and broken constructions.
- Parameter label lacks paper/source commit -> do not infer constants from the bit size or nearby implementation.
- Public-key validation is only range/nonsingularity -> implement the selected supersingularity/class validation before any secret action.
- Shared coefficient is used as a symmetric key -> introduce a transcript-bound KDF and migrate callers.
- CSIDH key is accepted by CTIDH or another parameter set -> add explicit construction/parameter binding and reject before decode/action.
- Constant-time test passes but target differs -> rerun on the exact compiler/CPU path and narrow the claim.
- Fault injection distinguishes real/dummy steps -> disable the vulnerable implementation for that threat model and adopt reviewed countermeasures before reuse.
- sina1777 C model called production/official/constant-time -> reclassify it as a pinned hardware golden-model artifact, rebuild source-only, and require independent CT/fault/licensing evidence.
- Conservative security estimate makes latency unacceptable -> choose a different reviewed primitive/protocol; never restore an obsolete security label for performance.

## Primary sources

- Isogeny portal: https://isogeny.org/
- CSIDH: https://csidh.isogeny.org/
- CTIDH: https://ctidh.isogeny.org/
- Quantum evaluation: https://quantum.isogeny.org/
- VeluSqrt: https://velusqrt.isogeny.org/
- Hardware/C golden model: https://github.com/sina1777/CSIDH/tree/main/SW
