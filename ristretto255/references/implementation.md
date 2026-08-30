# ristretto255 internals

Normative: [RFC 9496](https://www.rfc-editor.org/rfc/rfc9496.html); rationale: [ristretto.group](https://ristretto.group/).

## Constants/types

- `p=2^255-19`
- `l=2^252+27742317777372353535851937790883648493`
- element/scalar encoding: 32B LE; map input: 64B
- generator: `e2f2ae0a6abc4e71a884a961c500515f58e30b6aa582dd8db6a65945e08d2d76`
- identity: 32 zero bytes
- opaque distinct: valid element, compressed bytes, scalar mod `l`, protocol nonzero scalar; Edwards/field private

## Foundation

Reuse CT field arithmetic + complete extended Edwards `(x,y,z,t)`: CT equality/select/neg/abs, canonical encode/decode, sign where negative=least representative odd.
Implement RFC4.2 `SQRT_RATIO_M1(u,v)` exactly for zero/square/nonsquare; nonnegative root+`was_square`; all checks/select CT. Copy constants; verify canonical encodings.

## Decode RFC4.3.1

1. input exactly 32B; LE `s`; reject `s>=p`; no high-bit mask
2. reject negative `s`
3. compute RFC `ss,u1,u2,u2_sqr,v,invsqrt,den_x,den_y,x,y,t`
4. reject nonsquare OR negative `t` OR `y=0`
5. return opaque `(x,y,1,t)` only; no partial result

## Encode RFC4.3.2

Compute `u1,u2,invsqrt,den1,den2,z_inv`; CT rotate via `SQRT_M1`,`INVSQRT_A_MINUS_D`; sign-correct; nonnegative `s`; canonical 32B LE.
Equivalent reps => same bytes. `encode(decode(s))=s` for accepted `s`.

## Equality

`CT_EQ(x1*y2,y1*x2) OR CT_EQ(y1*y2,x1*x2)`. Never raw coordinate/Edwards equality. CT canonical encoding compare valid but slower.

## Map RFC4.3.4

1. input exactly 64B; split 32+32
2. `MAP` each half; MAP masks half MSB before field reduction (strict decode does not)
3. add mapped elements

MAP private, many-to-one, no preimage resistance.

## Scalar/ops

- input scalar canonical `0<=s<l`; reject
- derive 64 uniform LE bytes mod `l`; retry zero iff protocol requires
- never clamp
- addition/sub/neg/mul via complete Edwards on valid reps
- secret scalar/selection => CT; variable-time MSM only all-public+protocol allows
- no cofactor multiplication

## Proof

RFC9496 Appendix A full: `0B..15B`; all invalids; all 64B maps/collisions; all `SQRT_RATIO_M1`.
Properties: `decode(encode(P))=P`; accepted roundtrip; identity/inverse/zero; `(l-1)P+P=0` without reducing `l`; distributivity/laws; equivalent reps same; arbitrary 32B decode no panic/invalid result.
From-scratch: independent differential, decode/op fuzz, generated-code/side-channel audit for secret-dependent branches/tables.
