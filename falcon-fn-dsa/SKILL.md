---
name: falcon-fn-dsa
description: "Implements, integrates, tests, audits, and migrates Falcon lattice-based signatures and the upcoming Falcon-based FN-DSA standard. Use when handling Falcon-512/1024 or provisional FN-DSA keys, signing, verification, encodings, official vectors, samplers, randomness, side channels, interoperability, or migration planning. Don't use for ML-DSA, SLH-DSA, generic post-quantum migration, unrelated NTRU schemes, certification claims, or unsupported custom signature variants."
compatibility: "Covers Falcon v1.2 and provisional pornin/c-fn-dsa at pinned revisions. FIPS 206 remains in development as of 2026-09-06; c-fn-dsa is a best-guess implementation with no compatibility promise before version 1.0 after final FIPS 206. PQClean is archived. Inspector requires Python 3.11+."
metadata:
  category: "cryptography"
  source: "https://github.com/pornin/c-fn-dsa"
  sourceVersion: "pornin/c-fn-dsa@a5f15894bf1a68017074650d5298cecf9bb29a79; Falcon v1.2; NIST FIPS 206 status and PQClean retirement checked 2026-09-06"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-09-05T15:32:36+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-09-06T11:20:38+02:00"
---

# Falcon and FN-DSA

## Step 1: Fix the algorithm contract

1. CLASSIFY library integration | API/protocol design | Falcon implementation | provisional FN-DSA evaluation | security review | vector harness | Falcon-to-FN-DSA migration.
2. TREAT FN-DSA as an upcoming post-quantum signature scheme currently being defined by NIST and based on Falcon; FIPS 206 is still in development.
3. IDENTIFY the exact scheme/version, parameter set, signature encoding, pure/prehash behavior, context/domain binding, key representation, randomness owner, target platforms, side-channel boundary, and required interoperability peers.
4. READ `references/status-parameters.md` before choosing names, sizes, encodings, or claiming FN-DSA/FIPS behavior.
5. LABEL deployed Falcon v1.2 as Falcon. Label `pornin/c-fn-dsa` output as provisional FN-DSA tied to its exact commit, never as final or FIPS-conformant FN-DSA.
6. STOP when the protocol leaves the algorithm identifier, parameter set, signature format, message preprocessing, or encoding implicit.
7. ROUTE standardized vector acquisition to `nist-cavp`, generic invalid-input corpus work to `wycheproof`, and broad post-quantum migration policy outside this skill.

Completion: every serialized key/signature and signing request binds one exact scheme, version, parameter set, format, and message-processing mode.

## Step 2: Inspect the implementation boundary

RUN from the target repository root:
```bash
python3 scripts/inspect-project.py --root . --json
```

1. CONFIRM library/version provenance, Falcon/FN-DSA identifiers, parameter sets, formats, sign/verify paths, RNG calls, streaming pairs, custom FFT/sampler code, expanded-key handling, secret export/logging, and tests.
2. TREAT findings as review leads; inspect every reported callsite before concluding safety or defect.
3. READ `references/integration-encoding.md` for a library/API integration. READ `references/implementation-security.md` before reviewing or changing key generation, sampling, FFT, floating point, or constant-time code.

Completion: all public entry points, secret-bearing objects, randomness sources, wire encodings, and implementation variants have named owners and provenance.

## Step 3: Select or constrain the implementation

1. FOR provisional FN-DSA work, use [pornin/c-fn-dsa](https://github.com/pornin/c-fn-dsa) at a pinned revision as the active implementation reference.
2. TREAT c-fn-dsa as its author's best guess of future FIPS 206, not a normative implementation. Expect key, signature, encoding, and API compatibility to change until version 1.0 after final FIPS 206.
3. EXCLUDE PQClean from new implementation selection: the repository is archived read-only and no longer maintained. Inventory existing PQClean-derived Falcon code and assign migration or local-maintenance ownership.
4. TREAT the corrected 2021-11-01 Falcon submission API as a historical Falcon v1.2 reference, not the FN-DSA implementation reference or an automatic production endorsement.
5. FOR deployment, require pinned source, explicit scheme/version, vector coverage, supported target evidence, and an actionable security process; c-fn-dsa's active status does not create FIPS validation.
6. IMPLEMENT internals only when the project owns the lattice arithmetic, exact sampler, numerical behavior, constant-time review, target testing, and long-term maintenance.
7. REJECT reduced research degrees (`logn < 9`), changed salts/samplers/bounds, seed-only private-key formats, or custom encodings unless a separate reviewed protocol specifies them; never relabel them Falcon/FN-DSA.

Completion: the chosen implementation and build are pinned, supported for the target, and match the declared algorithm contract without private variants.

## Step 4: Integrate keys, signing, and verification

1. GENERATE keys and signatures only from a failure-reporting OS CSPRNG/approved DRBG path; propagate RNG failure and never emit partial output.
2. USE randomized signing. Keep test-only deterministic seeds unreachable from production entry points.
3. CHOOSE compressed, padded, or CT Falcon signatures explicitly. Pass an explicit expected format to verification; avoid format inference (`sig_type = 0`) because transcoding creates representation malleability.
4. PARSE exact key/signature lengths, headers, degree, coefficients, forbidden values, zero padding, canonical coefficient encodings, and trailing bytes before accepting an object.
5. BIND the protocol algorithm identifier and parameters outside attacker-controlled key/signature bytes. Reject cross-parameter, cross-format, and future-version confusion.
6. KEEP private keys, expanded keys, sampler state, FFT basis, LDL tree, seeds, and temporary signing buffers secret; zeroize according to the language/runtime threat model.
7. PAIR streamed start/update/finish APIs exactly once; bind the generated 40-byte Falcon nonce to the same message stream and final signature.
8. RETURN distinct internal diagnostics for malformed encoding, bad signature, invalid argument, RNG failure, and internal failure while exposing only protocol-appropriate failure behavior.

9. FOR c-fn-dsa, use `fndsa.h`; bind raw/prehash/external-mu mode and context explicitly, accept only standard `logn` 9/10 APIs, store encoded signing keys rather than seeds, and treat seeded signing as a test or reviewed bare-metal entropy path.

Completion: sign/verify operate through one explicit, canonical, randomized contract and every failure closes without output or secret disclosure.

## Step 5: Preserve sampler and side-channel invariants

1. PRESERVE the specified discrete-Gaussian distribution, rejection conditions, signature norm checks, operation order, and numerical bounds exactly.
2. NEVER replace the sampler, FFT/LDL arithmetic, floating-point semantics, or rejection loop with an intuitive equivalent. Match authoritative vectors and target compiler behavior.
3. VERIFY constant-time claims for the exact source, compiler, flags, architecture, CPU features, and signature format. Distinguish secret-key timing from message/signature-value timing.
4. DISABLE unintended fused multiply-add, excess precision, fast-math, undefined overflow, or variable-time target instructions where the selected implementation requires exact behavior.
5. KEEP signing salts unique and unpredictable. Treat reuse of the same randomized message hash or any distribution deviation as a potential key-recovery incident.
6. ISOLATE secret signing material from logs, crash dumps, serialization, swap, telemetry, and cross-tenant memory reuse according to the deployment threat model.

Completion: the target build preserves distribution and timing invariants with evidence stronger than source-level inspection.

## Step 6: Verify behavior and interoperability

READ `references/verification.md`.

1. RUN official Falcon KATs/SamplerZ vectors for Falcon v1.2; run c-fn-dsa's reproducible vectors for its exact pinned revision but label them provisional implementation vectors, not official FN-DSA vectors.
2. TEST positive sign/verify, randomized repeated signing, tampered message/signature/key, wrong parameter/format, truncation, extension, noncanonical encodings, forbidden coefficients, padding, context/hash-identifier mismatch, and RNG failure.
3. TEST one-shot/streaming equivalence where the selected API supports it, buffer boundaries, aliasing rules, error propagation, cleanup, and concurrency.
4. CROSS-VERIFY only implementations that declare the same Falcon version or exact provisional c-fn-dsa contract; Falcon and provisional FN-DSA encodings are not interchangeable.
5. RUN sanitizer, fuzz, fault/error-path, and target-specific timing/power/cache analysis proportional to the threat model.
6. FOR FN-DSA migration, compare published FIPS 206 algorithms and encodings line by line after publication; replace provisional c-fn-dsa assumptions rather than inferring final compatibility from Falcon ancestry.

Completion: vectors, negative tests, interoperability, target execution, and side-channel evidence cover every claimed parameter, format, and API path.

## Step 7: Report claims precisely

1. COPY `assets/falcon-review-report.md` and record scheme/version, provenance, parameters, formats, message processing, RNG, secret lifecycle, tests, target builds, side-channel evidence, and limitations.
2. STATE separately: algorithm conformance, interoperability, implementation hardening, module validation, and deployment approval.
3. CALL Falcon post-quantum only within the cited security model and parameter claim. Never convert test-vector success or library inclusion into FIPS validation or production suitability.
4. RECORD unverified platforms, provisional FN-DSA assumptions, unavailable hardware evidence, and migration triggers.

Completion: every security or standards claim is traceable to a normative source and exact tested artifact.

## Error Handling

- FIPS 206 is absent or still draft -> use c-fn-dsa only for explicitly provisional work pinned to a commit; never invent or claim final FN-DSA encodings.
- c-fn-dsa revision changes -> treat keys/signatures/vectors as potentially incompatible, rerun the complete contract, and migrate stored artifacts explicitly.
- PQClean Falcon is selected -> replace it with a maintained, reviewed path or document local maintenance while migration completes; archive status is not a security fix.
- Legacy Falcon implementation predates 2021-11-01 or provenance is unknown -> replace it or prove the PRNG initialization fix and every downstream modification.
- Declared vectors fail -> stop integration; resolve algorithm/version, byte order, sampler, floating-point, encoding, or adapter mismatch before testing higher layers.
- Signatures repeat a salt/syndrome or deterministic behavior appears unexpectedly -> disable signing, protect keys, preserve evidence, and treat the key as potentially compromised.
- Verification accepts alternate encodings -> enforce the selected contract's canonical format before protocol use.
- Constant-time evidence changes across compiler/CPU -> withdraw the broad claim and constrain the supported build/target matrix.
- RNG, allocation, or temporary-buffer failure occurs -> return failure, emit no signature/key, and clear initialized secret material.

## Primary sources

- Active provisional FN-DSA implementation reference: https://github.com/pornin/c-fn-dsa
- PQClean retirement notice: https://github.com/PQClean/PQClean
- Falcon project and corrected legacy implementation: https://falcon-sign.info/
- Falcon specification v1.2: https://falcon-sign.info/falcon.pdf
- NIST PQC/FIPS 206 status: https://csrc.nist.gov/projects/post-quantum-cryptography/post-quantum-cryptography-standardization
- NIST 2025 FIPS 206 status presentation: https://csrc.nist.gov/csrc/media/presentations/2025/fips-206-fn-dsa-(falcon)/images-media/fips_206-perlner_2.1.pdf
