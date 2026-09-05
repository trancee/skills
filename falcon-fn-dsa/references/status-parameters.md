# Status, identity, and parameters

## Normative status

Keep these identities separate:

| Name | Authority | Current status |
| --- | --- | --- |
| Falcon | Falcon specification v1.2, 2020-01-10 | NIST round-3 submission selected for standardization |
| Falcon reference API | Corrected Falcon source dated 2021-11-01 | Submission-era API with compressed, padded, and CT formats |
| FN-DSA | Future FIPS 206 | In development according to NIST's page updated 2026-08-05 |

NIST published FIPS 203, 204, and 205 in 2024. NIST has not yet published FIPS 206. Treat `FN-DSA`, FIPS conformance, validation, pure/prehash modes, final encodings, and final parameter names as unavailable until a normative FIPS 206 publication exists.

Refresh before each standards claim:

1. CHECK the [NIST PQC standardization page](https://csrc.nist.gov/projects/post-quantum-cryptography/post-quantum-cryptography-standardization).
2. CHECK the [NIST FIPS publication index](https://csrc.nist.gov/publications/fips) for a published FIPS 206.
3. IF FIPS 206 exists, pin its final publication date/version and replace provisional assumptions with exact algorithms, encodings, tests, and errata.
4. OTHERWISE, call the implementation Falcon v1.2 and document any nonstandard adaptation separately.

NIST IR 8413 selected Falcon while recommending CRYSTALS-Dilithium, now ML-DSA, as the primary signature algorithm to implement. Selection does not itself establish a Falcon deployment profile or FIPS validation.

## Falcon v1.2 parameters

Falcon uses `q = 12289` and `phi = x^n + 1` for power-of-two `n`.

| Parameter set | `n` | `logn` | NIST level | Encoded public key | Padded signature |
| --- | ---: | ---: | ---: | ---: | ---: |
| Falcon-512 | 512 | 9 | 1 | 897 bytes | 666 bytes |
| Falcon-1024 | 1024 | 10 | 5 | 1,793 bytes | 1,280 bytes |

Use these sizes only for the Falcon v1.2 encodings described by the specification/reference API. Compressed signatures are variable length; CT signatures are fixed and larger. Private-key and temporary-buffer sizes come from the exact implementation macros/API, not this table.

The reference API supports `logn` 1 through 10 for research, but values below 9 do not provide the standardized security sets. Reject them in deployed Falcon integrations.

## Falcon signature identity

A Falcon signature encodes:

1. A header identifying degree and encoding family.
2. A random 40-byte salt/nonce.
3. The encoded `s2` polynomial.
4. For padded format, all-zero padding to the exact prescribed size.

Falcon v1.2 tightened decompression to make each polynomial encoding unique. Enforce exact bit length, canonical zero, forbidden coefficient values, zero terminal bits/padding, exact total lengths, and no trailing data.

Bind the following in the containing protocol or key metadata:

- `Falcon-512` versus `Falcon-1024`.
- Falcon v1.2 versus any future FN-DSA version.
- Compressed versus padded versus CT signature encoding.
- Raw-message versus any externally prehashed/custom context construction.

Never infer a complete protocol algorithm solely from key length or signature header.

## Provisional FN-DSA information

The NIST 2025 FIPS 206 status presentation previewed, but did not standardize:

- Separate pure and prehash variants plus a BUFF transform.
- Randomized-only signing.
- NTT-form public keys.
- Private keys containing `f`, `g`, `F`, and a public-key hash rather than seed export.
- Discouraged export of cached FFT basis/LDL tree.
- Explicit LDL leaf checks and modified Gram-Schmidt bound.
- Added signature infinity-norm restriction.
- 79 sampler-randomness bits per coefficient.
- Uniform 40-byte pseudorandom seeds except a 32-byte key-generation seed.

Treat every item as provisional. Do not build a permanent wire format, interoperability claim, or compliance profile from a conference presentation.

## Source map

- Falcon project warning and resources: https://falcon-sign.info/
- Falcon specification v1.2: https://falcon-sign.info/falcon.pdf
- Corrected external API: https://falcon-sign.info/impl/falcon.h.html
- NIST selection report: https://csrc.nist.gov/pubs/ir/8413/upd1/final
- NIST current status: https://csrc.nist.gov/projects/post-quantum-cryptography/post-quantum-cryptography-standardization
- NIST provisional FIPS 206 presentation: https://csrc.nist.gov/csrc/media/presentations/2025/fips-206-fn-dsa-(falcon)/images-media/fips_206-perlner_2.1.pdf
