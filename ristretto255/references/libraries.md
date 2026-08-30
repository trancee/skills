# ristretto255 libraries

Confirm current version/API.

## Rust `curve25519-dalek`

[API](https://docs.rs/curve25519-dalek/latest/curve25519_dalek/ristretto/):
- bytes `CompressedRistretto`; element `RistrettoPoint`; validate=`decompress`; encode=`compress`
- scalar input=`from_canonical_bytes`; 64B reduce=`from_bytes_mod_order_wide`
- map=`RistrettoPoint::from_uniform_bytes`
- secret MSM=`MultiscalarMul`; public-only=`VartimeMultiscalarMul`
- check random/digest/serde/precomputed/zeroize features
- deserialized compressed value is unvalidated until `decompress`

## C/bindings `libsodium`

[API](https://doc.libsodium.org/advanced/point-arithmetic/ristretto):
- validate `crypto_core_ristretto255_is_valid_point`
- map `crypto_core_ristretto255_from_hash`
- add/sub `crypto_core_ristretto255_add/sub`
- mul/base `crypto_scalarmult_ristretto255[_base]`
- random scalar `crypto_core_ristretto255_scalar_random`
- reduce `crypto_core_ristretto255_scalar_reduce`
- check all returns; identity-result error is libsodium policy, map to protocol

## Go

[`github.com/gtank/ristretto255`](https://pkg.go.dev/github.com/gtank/ristretto255), RFC9496 4.3/4.4; verify installed version/methods.

## Gate

Require dedicated opaque element, strict decode, canonical scalar+wide reduction, CT secret mul, 64B map, RFC Appendix A coverage, acceptable maintenance/security. Generic Edwards/Ed25519/X25519 API => reject.
