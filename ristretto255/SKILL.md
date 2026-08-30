---
name: ristretto255
description: "Implements, integrates, and reviews ristretto255 safely, including canonical encoding, hash-to-group, scalar handling, constant-time operations, protocol use, and RFC test vectors. Use when working with the ristretto255 group, integrating a maintained library, designing a protocol over it, auditing an implementation, or implementing RFC 9496. Don't use for raw Ed25519/X25519 operations, decaf448, or unrelated elliptic-curve protocol design."
metadata:
  category: "cryptography"
  source: "https://ristretto.group/"
  sourceVersion: "RFC 9496 (December 2023)"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-28T19:45:01+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-30T11:16:59+02:00"
---

# ristretto255 implementation and use

## Procedures

**Step 1: Classify the task**

1. Identify whether the task integrates a maintained library, designs or reviews a protocol, or implements the ristretto255 abstraction.
2. Use [RFC 9496](https://www.rfc-editor.org/rfc/rfc9496.html) as the interoperability specification and [ristretto.group](https://ristretto.group/) for rationale and derivations. Check [RFC 9496 errata](https://www.rfc-editor.org/errata/rfc9496) before implementing formulas.
3. Keep the scope on ristretto255. Treat decaf448, Ed25519, Edwards25519, and X25519 as distinct constructions.
4. Reject underspecified protocol requests until the protocol defines scalar derivation, hash-to-group, identity handling, transcript encoding, and KDF behavior.

**Step 2: Select the implementation path**

1. Prefer a maintained library exposing dedicated ristretto255 element, compressed-element, and scalar types.
2. Read `references/libraries.md` when selecting Rust, C/libsodium, Go, or another implementation.
3. Verify the installed library version, maintenance status, strict decoding, constant-time guarantees, uniform-element map, scalar API, and RFC 9496 vector coverage.
4. Implement from scratch only when the project already owns constant-time Curve25519 field arithmetic and complete Edwards operations, and a concrete platform or interoperability requirement excludes maintained libraries.
5. If implementing or auditing the abstraction, read `references/implementation.md` before editing code. Otherwise, continue to Step 3.

**Step 3: Establish opaque boundaries**

1. Define separate types for validated ristretto255 elements, 32-byte compressed encodings, scalars modulo the group order, and protocol-specific nonzero scalars when needed.
2. Keep Edwards representatives, coordinates, field elements, map internals, and implementation constants private.
3. Construct elements only through strict decoding, the 64-byte element-derivation function, identity/generator constants, or group operations on valid elements.
4. Remove public conversions from arbitrary Edwards25519 points and prevent mixing Ristretto, Ed25519, Edwards25519, and X25519 values.
5. Keep validated opaque elements internal across operations instead of encoding and decoding every intermediate.

**Step 4: Validate external values**

1. Require exactly 32 bytes for an external element encoding.
2. Call strict ristretto255 decoding; reject noncanonical field encodings, negative `s`, nonsquare cases, negative `x*y`, and `y = 0`.
3. Preserve the high bit during validation. Reject it through canonical decoding rather than silently masking it.
4. Apply protocol-specific identity restrictions only after successful decoding. Treat the all-zero identity encoding as a valid group element at the generic group layer.
5. Parse external scalars canonically by accepting only values in `0 <= s < l`; reject noncanonical encodings instead of reducing them.
6. Derive scalars from 64 uniform little-endian bytes reduced modulo `l`. Resample or rederive zero only when the protocol requires a nonzero or invertible scalar.
7. Never clamp ristretto255 scalars.

**Step 5: Derive elements and scalars**

1. Use the library's element-derivation function only with exactly 64 uniform bytes.
2. For arbitrary messages, read `references/protocol-use.md` and implement RFC 9380 `hash_to_ristretto255` with the protocol's exact `expand_message` construction and domain separation tag.
3. Give distinct logical random oracles distinct nonempty domain separation tags.
4. Generate random elements with the library's CSPRNG-backed API or by mapping 64 uniform random bytes. Avoid rejection-sampling random compressed encodings.
5. Treat the 64-byte map as a many-to-one map, not as a digest, commitment, encoding, or one-way proof.

**Step 6: Perform group operations**

1. Use dedicated operations for identity, generator, equality, addition, subtraction, negation, scalar multiplication, fixed-base multiplication, and multiscalar multiplication.
2. Use constant-time algorithms whenever a scalar, point selection, or control value is secret.
3. Use variable-time algorithms only when every value influencing control flow and memory access is public and the protocol permits it.
4. Compare elements with Ristretto equality or a constant-time comparison of canonical encodings. Never compare underlying Edwards coordinates.
5. Omit manual cofactor clearing; Ristretto already supplies the prime-order quotient abstraction.
6. Check every library return code and map library-specific identity errors to the invoking protocol explicitly.

**Step 7: Bind protocol context**

1. Read `references/protocol-use.md` for key exchange, transcripts, challenges, random oracles, or shared-element handling.
2. Encode elements canonically before adding them to a transcript.
3. Bind protocol and ciphersuite versions, roles, public elements, associated data, and operation purpose through an unambiguous transcript grammar.
4. Feed a shared element's canonical encoding and the full transcript/context to the specified KDF. Never use the encoded shared element directly as a symmetric key.
5. Specify authentication, contributory behavior, forward secrecy, key confirmation, and identity rejection at the protocol layer; do not infer them from Ristretto.

**Step 8: Verify interoperability and invariants**

1. Run the repository's existing ristretto255 tests first.
2. Run every RFC 9496 Appendix A vector class: generator multiples, invalid encodings, 64-byte element derivation, and `SQRT_RATIO_M1` when implementing internals.
3. To exercise a black-box implementation, copy the operation shapes from `assets/vector-adapter.json`, implement a tiny JSON-lines adapter, and run:

   ```bash
   python3 scripts/check-vectors.py -- path/to/adapter [args...]
   ```

4. Treat the script as a smoke checker: it covers canonical generator multiples, all RFC invalid encodings, and seven uniform-byte mappings. Retain full Appendix A and implementation-specific tests in the project's suite.
5. Test RFC 9380 Appendix B separately when the protocol hashes arbitrary messages; RFC 9496 uniform-byte vectors do not test the expander or domain separation tag.
6. Add property tests for encode/decode round trips, identity and inverse laws, scalar distributivity, and the group order without reducing `l` to the zero scalar first.
7. Differential-test against an independent maintained implementation and fuzz arbitrary decodes and operation sequences when implementing the abstraction.
8. Inspect secret-dependent paths with platform-appropriate side-channel tooling or generated-code review.

**Step 9: Complete the review**

1. Confirm that external elements and scalars use strict canonical parsing.
2. Confirm that Ristretto, compressed bytes, scalars, Edwards25519, Ed25519, and X25519 remain distinct types.
3. Confirm that every secret-dependent operation uses a constant-time path.
4. Confirm that identity handling is explicit at each protocol boundary.
5. Confirm that hash-to-group, transcripts, and KDF inputs use the specified domain separation and canonical encodings.
6. Confirm that relevant RFC 9496 and RFC 9380 vectors pass and that negative decoding vectors fail.
7. Report the exact tested library/version, operations, vector classes, and any unverified side-channel or protocol assumptions.

## Error Handling

- If metadata, element length, scalar length, algorithm identity, or protocol rules are ambiguous, stop the affected path and obtain the specification rather than guessing.
- If a maintained library lacks strict decoding, canonical scalar parsing, constant-time secret multiplication, or RFC vectors, select another library or isolate and implement the missing boundary with explicit tests.
- If `scripts/check-vectors.py` reports `adapter returned invalid JSON`, emit exactly one JSON object per request on stdout and send diagnostics to stderr.
- If the vector checker reports an accepted invalid encoding, fix strict decoding before debugging higher-level arithmetic.
- If generator multiples fail, check the canonical generator, addition, encoding, and quotient equality in that order.
- If uniform-byte vectors fail while generator multiples pass, inspect the two-map element derivation, field sign convention, and `SQRT_RATIO_M1` semantics.
- If RFC 9380 vectors fail while RFC 9496 uniform vectors pass, inspect `expand_message`, the domain separation tag, and the 64-byte boundary rather than the Ristretto map.
- If only variable-time multiplication is available for secret scalars, treat the implementation as unsuitable for that protocol path.
