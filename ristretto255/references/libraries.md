# Maintained ristretto255 libraries

Read this reference when selecting or integrating a library. Confirm current versions and APIs from each project's documentation before editing code.

## Rust: curve25519-dalek

Use [`curve25519-dalek::ristretto`](https://docs.rs/curve25519-dalek/latest/curve25519_dalek/ristretto/).

- Use `CompressedRistretto` for 32-byte wire data.
- Use `RistrettoPoint` for validated elements.
- Parse by constructing the compressed value and calling `decompress()`.
- Encode with `compress()`.
- Parse received scalars with `Scalar::from_canonical_bytes()`.
- Reduce 64 uniform bytes with `Scalar::from_bytes_mod_order_wide()`.
- Map 64 uniform bytes with `RistrettoPoint::from_uniform_bytes()`.
- Use `MultiscalarMul` for secret-dependent work.
- Use `VartimeMultiscalarMul` only for public verification inputs.

Check feature flags for randomness, digest integration, serialization, precomputed tables, and zeroization. Deserializing `CompressedRistretto` yields bytes, not a validated element; call `decompress()` before use.

## C and bindings: libsodium

Use [libsodium's ristretto255 API](https://doc.libsodium.org/advanced/point-arithmetic/ristretto).

- Validate received encodings with `crypto_core_ristretto255_is_valid_point()`.
- Map 64 uniform bytes with `crypto_core_ristretto255_from_hash()`.
- Add/subtract with `crypto_core_ristretto255_add()` and `crypto_core_ristretto255_sub()`.
- Multiply with `crypto_scalarmult_ristretto255()` or `crypto_scalarmult_ristretto255_base()`.
- Generate nonzero random scalars with `crypto_core_ristretto255_scalar_random()`.
- Reduce a 64-byte wide scalar with `crypto_core_ristretto255_scalar_reduce()`.
- Check every return code.

libsodium's scalar multiplication reports an error for an identity result. Treat that as an API policy and map it to the invoking protocol's identity rule.

## Go

Use [`github.com/gtank/ristretto255`](https://pkg.go.dev/github.com/gtank/ristretto255), which implements RFC 9496 Sections 4.3 and 4.4. Confirm the installed module version and current method names before integration.

## Selection checks

Select a library only when it provides:

- a dedicated opaque ristretto255 element type;
- strict canonical decoding;
- canonical scalar parsing and wide reduction;
- constant-time secret scalar multiplication;
- a 64-byte uniform element map;
- RFC 9496 Appendix A coverage;
- maintained release and security processes suitable for the project.

Reject an integration based only on generic Edwards25519, Ed25519, or X25519 APIs.
