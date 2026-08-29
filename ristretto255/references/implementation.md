# ristretto255 implementation reference

Read this reference only when implementing or auditing the ristretto255 abstraction itself. Treat [RFC 9496](https://www.rfc-editor.org/rfc/rfc9496.html) as normative for interoperability and [ristretto.group](https://ristretto.group/) as rationale and derivation.

## Parameters and types

- Field: `p = 2^255 - 19`.
- Scalar order: `l = 2^252 + 27742317777372353535851937790883648493`.
- Element encoding: exactly 32 bytes, little-endian.
- Scalar encoding: 32 bytes, little-endian.
- Uniform input to the element map: exactly 64 bytes.
- Canonical generator encoding: `e2f2ae0a6abc4e71a884a961c500515f58e30b6aa582dd8db6a65945e08d2d76`.
- Identity encoding: 32 zero bytes.

Keep separate opaque types for a validated element, compressed bytes, a scalar modulo `l`, and any protocol-specific nonzero scalar. Keep Edwards representatives and field elements private.

## Required field foundation

Reuse constant-time field arithmetic and complete extended-Edwards operations `(x, y, z, t)`. Provide constant-time field equality, conditional selection, conditional negation/absolute value, canonical field encoding/decoding, and sign testing. A field element is negative when its least nonnegative representative is odd.

Implement `SQRT_RATIO_M1(u, v)` exactly as RFC 9496 Section 4.2. Preserve its behavior for zero numerator, zero denominator, square ratios, and nonsquare ratios. Return a nonnegative root and `was_square`; implement all equality checks and selections in constant time.

Copy every RFC implementation constant exactly. Verify constants through canonical field encodings rather than reconstructing alternate-sign square roots.

## Decode

Implement RFC 9496 Section 4.3.1 in order:

1. Require exactly 32 bytes.
2. Interpret the input as little-endian `s`; reject `s >= p`. Do not mask the high bit.
3. Reject negative `s`.
4. Compute the RFC values `ss`, `u1`, `u2`, `u2_sqr`, `v`, `invsqrt`, `den_x`, `den_y`, `x`, `y`, and `t`.
5. Reject when the ratio is nonsquare, `t` is negative, or `y` is zero.
6. Return the opaque element represented internally by `(x, y, 1, t)`.

A decode function returns either a valid opaque element or an error. It never returns a partially validated representative.

## Encode

Implement RFC 9496 Section 4.3.2 on a valid representative:

1. Compute `u1`, `u2`, the inverse square root, `den1`, `den2`, and `z_inv`.
2. Apply the specified constant-time conditional rotation using `SQRT_M1` and `INVSQRT_A_MINUS_D`.
3. Apply the specified conditional sign correction.
4. Compute nonnegative `s`.
5. Return canonical 32-byte little-endian `s`.

Encoding equivalent Edwards representatives must produce identical bytes. Decoding a valid encoding and encoding it again must reproduce the input exactly.

## Equality

Compare quotient-group elements with:

```text
CT_EQ(x1*y2, y1*x2) OR CT_EQ(y1*y2, x1*x2)
```

Use constant-time operations. Never compare coordinates or underlying Edwards points directly. A constant-time comparison of canonical encodings is equivalent but less efficient.

## Element derivation

Implement RFC 9496 Section 4.3.4:

1. Require a 64-byte uniform input.
2. Split it into two 32-byte strings.
3. Apply the RFC `MAP` function to each half. The map masks each half's most significant bit before reducing to a field element; this differs deliberately from strict element decoding.
4. Add the two mapped elements.

Keep the map and its constants internal. The map is many-to-one and intentionally lacks preimage resistance.

## Scalar handling

- Parse received canonical scalars by requiring `0 <= s < l`; reject noncanonical encodings.
- Derive scalars by interpreting 64 uniform bytes as a little-endian integer and reducing modulo `l`.
- Sample again when a protocol requires nonzero or invertible scalars and reduction produces zero.
- Never clamp ristretto255 scalars.

## Group operations

Forward addition, subtraction, negation, and scalar multiplication to complete Edwards operations on valid representatives. Use constant-time algorithms whenever scalars or selections are secret. Permit variable-time multiscalar multiplication only when every relevant input is public and the invoking protocol allows it.

Do not multiply by the Curve25519 cofactor. Ristretto is a quotient construction, not a subgroup-validation wrapper.

## Implementation verification

Run RFC 9496 Appendix A in full:

- generator multiples `0B` through `15B`;
- every invalid encoding class;
- every 64-byte element-derivation vector, including colliding map inputs;
- every `SQRT_RATIO_M1` vector.

Add properties:

- `decode(encode(P)) == P`;
- `encode(decode(s)) == s` for accepted encodings;
- `P + 0 == P`, `P + (-P) == 0`, and `0*P == 0`;
- `(l-1)*P + P == 0`, without reducing `l` to a scalar first;
- scalar distributivity and group laws;
- equivalent internal representatives compare equal and encode identically;
- arbitrary 32-byte decode inputs never panic or create an invalid element.

Differential-test against an independent maintained implementation. Fuzz decoding and operation sequences. Audit generated code or use suitable side-channel tooling to check field, scalar, square-root, and multiplication paths for secret-dependent branches or table accesses.
