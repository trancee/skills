# Verification plan

## Evidence layers

Keep each claim attached to its evidence:

| Claim | Minimum evidence |
| --- | --- |
| Functional API behavior | Positive/negative tests through the public API |
| Falcon v1.2 algorithm conformance | Official KAT and SamplerZ vectors for every claimed set/path |
| Encoding strictness | Malformed/canonical boundary corpus through the public parser |
| Interoperability | Cross-sign/verify and byte exchange with an independent matching implementation |
| Memory safety | Sanitizers plus coverage-guided fuzzing of parsers and API state transitions |
| Constant-time/side-channel behavior | Exact target/build analysis and measurements tied to threat model |
| FN-DSA/FIPS conformance | Published FIPS 206 plus applicable validation program evidence |

No lower row follows automatically from a higher or lower one.

## Official vectors

Pin the Falcon submission package and record its digest/revision. Run:

- Key-generation/signature Known Answer Tests for Falcon-512 and Falcon-1024 as supported.
- Both clean/reference and each optimized/architecture implementation exposed by the library.
- SamplerZ vectors from `Supporting_Documentation/additional/test-vector-sampler-falcon{512,1024}.txt` for custom sampler code.
- Encoded key/signature outputs through the same adapter that production callers use.

Separate deterministic vector seeding from production builds/APIs. Never expose a caller-controlled vector seed as a production signing option.

When final FIPS 206 and validation vectors become available, create a distinct FN-DSA adapter. Do not reuse Falcon vector expectations unless the standard explicitly does.

## Functional matrix

For every parameter × format × implementation path:

1. Generate a keypair; derive/compare the public key where the API supports it.
2. Sign empty, short, binary, and multi-chunk messages; verify successfully.
3. Sign the same message repeatedly; require valid signatures and fresh salts rather than byte equality.
4. Reject changed message, signature bit, salt, public key, and parameter identifier.
5. Reject truncated and extended keys/signatures at every boundary.
6. Reject invalid headers/degrees, noncanonical zero/coefficient encodings, forbidden coefficient values, malformed unary coding, nonzero terminal bits, partial padding, and nonzero padding.
7. Exercise maximum buffer size, one-byte-short buffer, returned actual length, null/empty inputs allowed by the API, and temporary-buffer size/alignment rules.
8. Force RNG, allocation, internal, cancellation, and parsing failures; confirm no output, no stale success, and required cleanup.
9. Compare one-shot with every relevant streaming chunk split, including zero-length chunks and empty message.
10. Compare dynamic signing with expanded/tree signing; move expanded keys only within documented alignment/lifetime rules.
11. Exercise supported concurrency with distinct contexts and detect accidental shared mutable RNG/scratch state.

If a protocol accepts only one signature format, keep the other formats out of its adapter rather than testing permissive negotiation.

## Interoperability

Build an exchange matrix that records producer, consumer, source revision, parameter, signature format, and message-processing mode.

- Import/export public keys both directions.
- Sign in implementation A and verify in B; reverse direction.
- Exercise compressed/padded/CT only where both peers declare the same format.
- Verify exact bytes for keys and structural encoding; randomized signatures need not match byte-for-byte.
- Reject version/parameter/format mismatches rather than silently transcoding.

Use at least one implementation with independent code lineage when claiming interoperability. Two wrappers around the same PQClean source do not establish independent agreement.

## Fuzzing and sanitizers

Fuzz public key decode, signature decode/verify, streaming state transitions, and size/error paths. Seed with valid objects from both parameter sets and mutate headers, bit lengths, unary runs, coefficients, salt, padding, and trailing data.

Assert:

- No crash, hang, out-of-bounds access, unbounded allocation, or undefined behavior.
- Acceptance only for canonically encoded signatures that verify.
- Stable failure class at the protocol boundary.
- Bounded work for malformed public inputs.

Run address, undefined-behavior, memory, and thread sanitizers supported by the language/toolchain. Do not equate sanitizer success with side-channel safety.

## Side-channel and numerical verification

Record compiler, version, optimization/LTO flags, architecture, CPU features, dispatch path, floating-point mode, and exact binary hash.

- Diff generated assembly for sensitive paths when flags/compiler change.
- Use constant-time analysis suitable for the language and target.
- Measure timing distributions across controlled secret classes and public inputs; account for noise and multiple-comparison errors.
- Use power/EM/fault testing for embedded or adversarial physical threat models.
- Re-run KATs on target hardware, not only cross-compiled host emulation.
- Exercise denormals, FMA availability, rounding mode, and architecture-specific multiply/shift behavior.

A single dudect-style pass or a source annotation is evidence, not proof. Scope the final claim to the tested target/build.

## Reporting

Copy `assets/falcon-review-report.md`. Include exact commands, vector sources/digests, counts, negative classes, interoperability matrix, fuzz duration/corpus, sanitizer configurations, target build hashes, side-channel methods/results, and all unverified claims.
