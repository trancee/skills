---
name: ristretto255
description: "Implements/integrates/audits ristretto255: canonical encoding, hash-to-group, scalars, constant-time operations, protocol use, RFC vectors. Use for ristretto255 libraries/protocols/RFC 9496 implementations. Don't use for raw Ed25519/X25519, decaf448, or unrelated curves."
metadata:
  category: "cryptography"
  source: "https://ristretto.group/"
  sourceVersion: "RFC 9496 (December 2023)"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-28T19:45:01+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-30T11:48:01+02:00"
---

# ristretto255

## 1. Route

1. CLASSIFY: library integration | protocol design/review | abstraction implementation/audit.
2. Normative: [RFC 9496](https://www.rfc-editor.org/rfc/rfc9496.html); rationale: [ristretto.group](https://ristretto.group/); check [errata](https://www.rfc-editor.org/errata/rfc9496).
3. Protocol underspecified scalar derivation/hash-to-group/identity/transcript/KDF => STOP.
4. Library selection -> READ `references/libraries.md`.
5. Internals -> READ `references/implementation.md`.
6. Protocol/hash/transcript/shared element -> READ `references/protocol-use.md`.

## 2. Implementation choice

PREFER maintained dedicated API. VERIFY version, maintenance, strict decode, canonical scalar parse, wide reduction, CT secret multiplication, 64-byte map, RFC vectors.
From-scratch only if project owns CT Curve25519 field + complete Edwards ops AND required platform/interoperability excludes libraries.

## 3. Type boundary

Distinct opaque types: validated element | compressed 32B | scalar mod `l` | protocol nonzero scalar.
PRIVATE: Edwards reps/coordinates/field/map/constants.
Construct elements only via strict decode, 64B map, identity/generator, valid group ops.
No public arbitrary-Edwards conversion; no Ristretto/Ed25519/Edwards25519/X25519 mixing. Keep internal elements decoded across ops.

## 4. External parse

- element: exactly 32B; strict decode rejects noncanonical `s`, negative `s`, nonsquare, negative `x*y`, `y=0`; never mask high bit
- identity: valid generic element; protocol restriction after decode
- scalar input: canonical `0 <= s < l`; reject, never reduce
- scalar derivation: 64 uniform LE bytes mod `l`; retry zero iff protocol requires nonzero/invertible
- NEVER clamp ristretto255 scalar

## 5. Derive+operate

- element map input exactly 64 uniform bytes
- arbitrary message => RFC 9380 `hash_to_ristretto255`, exact expander+DST; distinct logical oracle => distinct nonempty DST
- random element => maintained CSPRNG API OR map 64 uniform bytes; never rejection-sample encodings
- 64B map is many-to-one; not digest/commitment/encoding/proof
- use dedicated identity/generator/equality/add/sub/neg/mul/fixed-base/MSM
- secrets/control selections => CT; variable-time only all-public + protocol permits
- equality => Ristretto equality OR CT canonical-byte compare; never Edwards coordinates
- no manual cofactor clearing; check every return code; map library identity policy explicitly

## 6. Protocol binding

Canonical element encodings in unambiguous transcript. Bind protocol+ciphersuite versions, roles, public elements, associated data, purpose.
Shared element -> canonical bytes + full transcript/context -> specified KDF; never direct symmetric key.
Protocol explicitly defines authentication, contributory behavior, forward secrecy, key confirmation, identity rejection.

## 7. Proof

1. Existing tests first.
2. Full RFC 9496 Appendix A: `0B..15B`, all invalid encodings, every 64B map vector, `SQRT_RATIO_M1` for internals.
3. Black-box: implement `assets/vector-adapter.json`; RUN:
   ```bash
   python3 scripts/check-vectors.py -- path/to/adapter [args...]
   ```
   Script=smoke only; retain full RFC+project tests.
4. Arbitrary-message hashing => RFC 9380 Appendix B separately.
5. Properties: encode/decode, identity/inverse, distributivity, order (do not reduce `l` first).
6. From-scratch => independent differential test + decode/op fuzz + side-channel/generated-code inspection.
7. OUT: exact library/version, ops, vector classes, unverified side-channel/protocol assumptions.

## Fail

- ambiguity in metadata/length/algorithm/protocol => STOP for spec
- library missing strict decode/canonical scalar/CT secret mul/RFC vectors => replace OR isolate+test boundary
- adapter invalid JSON => one JSON response/request line; diagnostics stderr
- accepted invalid encoding => fix decode first
- generator failure => generator -> add -> encode -> quotient equality
- map-only failure => two-map derivation/sign/`SQRT_RATIO_M1`
- RFC9380-only failure => expander/DST/64B boundary
- secret scalar only variable-time => unsuitable
