# ristretto255 protocol

Ristretto=prime-order group, not complete protocol.

## Boundary/transcript

External element: strict 32B decode, then protocol identity policy. Identity valid generically.
Transcript uses canonical encodings + protocol/ciphersuite versions + roles + all public elements + associated data + purpose; specified framework or unambiguous length-prefix grammar.

## Hash-to-group

RFC9380 Appendix B:
```text
uniform_bytes = expand_message(msg, DST, 64)
P = ristretto255_map(uniform_bytes)
```
XMD SHA-512 id: `ristretto255_XMD:SHA-512_R255MAP_RO_`.
DST nonempty+protocol-specific; distinct logical oracle => distinct DST. Bind stable protocol/version/ciphersuite/role/purpose/operation.
Never substitute `SHA-512(msg)` absent explicit legacy protocol; never hash then strict-decode.

## Random

- element: maintained CSPRNG API OR map 64 uniform bytes; no rejection-sampled 32B encoding
- scalar: protocol DST expander -> 64 uniform bytes -> mod `l`; retry iff nonzero required

## Shared element

1. strict peer decode
2. protocol identity check
3. CT scalar multiplication
4. canonical encode
5. encoded element + full transcript/context -> specified KDF

Never direct symmetric key. Protocol separately specifies authentication, contributory behavior, forward secrecy, key confirmation.

## Reject substitutions

Ed25519/X25519 bytes as Ristretto; reused Ed25519 keypair absent derivation; clamped scalar; reduced/masked external value; cleared high bit; cofactor clearing; variable-time secret mul; reused DST; 64B map as digest/commitment/proof.
