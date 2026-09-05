# Implementation and side-channel security

## Implementation threshold

Prefer a maintained implementation. Build Falcon internals only when the project can continuously maintain:

- NTRU key generation and exact equation/bound checks.
- NTT/FFT arithmetic and representation conversions.
- Fast Fourier/LDL-tree sampling.
- Exact discrete-Gaussian integer sampler.
- Canonical key/signature encoders and decoders.
- Deterministic vector harnesses separated from production randomness.
- Constant-time and numerical analysis for every supported target/build.
- Independent interoperability, fuzzing, and cryptographic review.

A mathematically correct-looking sampler or FFT is insufficient. Small distributional or numerical deviations during signing can reveal the private lattice basis over many observations.

## Key generation

Enforce the selected specification's complete conditions:

1. Sample `f` and `g` from the required distribution.
2. Solve `fG - gF = q` over the Falcon ring.
3. Verify invertibility and derive `h = g/f mod q` in the required representation.
4. Apply Gram-Schmidt/norm, coefficient, encoding, and any selected-version checks.
5. Reject and resample on any failed condition without releasing partial key material.
6. Validate generated keys independently before use.

Do not compress a private key to a seed unless the selected normative scheme defines deterministic expansion and interoperability. Falcon v1.2's website notes this only as a theoretical tradeoff; the provisional FN-DSA presentation explicitly planned not to export seeds because valid key-generation implementations may differ.

## Signing distribution

Preserve all of these as one invariant:

- Uniform fresh salt/nonce per signature.
- Correct hash-to-point input and rejection behavior.
- Correct FFT basis and LDL tree derived from the same private key.
- Exact Gaussian center/standard deviation and SamplerZ distribution.
- Correct rejection and squared-norm bound before encoding.
- Canonical encoding of the accepted signature.

Never substitute rounded normal-distribution APIs, generic floating random generators, table truncation, fewer random bits, deterministic seeding, or approximate rejection thresholds.

Run official SamplerZ vectors for the low-level implementation. Add statistical tests only as regression diagnostics; passing a statistical test does not establish the required distribution.

## Numerical behavior

Pin and inspect:

- IEEE-754 binary64 or the exact selected fixed-point design.
- Rounding mode, precision, denormal handling, and exception state.
- Operation order and prohibited/allowed fused multiply-add.
- Compiler optimization flags, `fast-math`, link-time optimization, and architecture dispatch.
- Native versus emulated arithmetic and changes across compiler releases.

Test generated artifacts on every supported target. Source equality does not imply identical floating-point or timing behavior.

NIST's 2025 provisional FIPS 206 presentation planned exact KAT matching for signing, explicit operation order, and no fused multiply-add; it allowed more key-generation latitude with explicit validation checks. Treat this as design preview until FIPS 206 is published.

## Timing, power, cache, and fault behavior

Separate claims:

- Secret-key independence of key generation/signing control flow and memory access.
- Signature/message-hash independence, relevant when those values are secret.
- Verification behavior, which uses public inputs but still must resist denial-of-service and parser faults.
- Physical power/EM/fault resistance on embedded targets.

The reference API describes all signature formats as constant-time with respect to the private key and only CT format as additionally protecting signature value/message data timing. Verify that claim for the exact target; wrappers, RNG, allocation, error handling, CPU dispatch, and compiler transformations can reintroduce leakage.

Inspect variable-time integer multiply/divide/shift behavior, lookup tables, rejection loops, branches, cache indexing, floating-point units, FMA contraction, denormal handling, and optimizer-generated calls. Use target-specific tools and traces rather than one desktop timing test.

## Failure and secret lifecycle

- Check allocations and buffer capacities before secret computation.
- Propagate RNG/internal/format/size errors without substituting outputs.
- Zeroize private keys, expanded trees, RNG state, and temporary buffers with an optimization-resistant primitive where the threat model requires it.
- Keep secret-bearing pages out of logs, core dumps, telemetry, serialization, and unsafe swap where feasible.
- Prevent concurrent mutation or reuse of RNG/hash/temporary contexts.
- Define behavior under cancellation, panic/exception, process fork, and hardware reset.

## Incident triggers

Treat any of these as potential key compromise, not a routine functional bug:

- Repeated salt/nonce or repeated randomized-message syndrome under one key.
- Deterministic signatures from independently initialized production calls.
- Vector divergence tied to compiler/architecture/floating behavior.
- Signature distribution or norm anomalies.
- Secret-dependent timing/power/cache correlation.
- Exposure of expanded keys, FFT basis, LDL tree, or signing RNG state.

Stop signing, preserve exact artifacts/build metadata, scope affected keys and signatures, rotate keys according to the protocol, and coordinate cryptographic review before resuming.

## Technical sources

- Falcon specification implementation chapters: https://falcon-sign.info/falcon.pdf
- Corrected reference API: https://falcon-sign.info/impl/falcon.h.html
- Constant-time Falcon: https://eprint.iacr.org/2019/893
- Isochronous Gaussian sampling: https://eprint.iacr.org/2019/1411
- Gram-Schmidt norm leakage: https://eprint.iacr.org/2019/1180
- NIST provisional validation approach: https://csrc.nist.gov/csrc/media/presentations/2025/fips-206-fn-dsa-(falcon)/images-media/fips_206-perlner_2.1.pdf
