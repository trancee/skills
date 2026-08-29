# Protocol use of ristretto255

Read this reference when designing or reviewing a protocol that consumes ristretto255. Ristretto supplies a prime-order group abstraction; it does not supply a complete protocol.

## Element boundaries

Strictly decode every external 32-byte element. Apply identity restrictions after successful decoding according to the protocol. The identity is a valid group element; it is neither globally forbidden nor globally acceptable.

Build transcripts from canonical element encodings. Bind protocol and ciphersuite versions, roles, all relevant public elements, associated data, and the operation purpose. Use a specified transcript framework or an unambiguous length-prefixed grammar.

## Hash to group

Use [RFC 9380 Appendix B](https://www.rfc-editor.org/rfc/rfc9380.html#appendix-B) for arbitrary messages:

```text
uniform_bytes = expand_message(msg, DST, 64)
P = ristretto255_map(uniform_bytes)
```

For `expand_message_xmd` with SHA-512, use the required identifier:

```text
ristretto255_XMD:SHA-512_R255MAP_RO_
```

Choose a nonempty protocol-specific domain separation tag. Give distinct logical random oracles distinct tags. Include stable protocol, version, ciphersuite, role/purpose, and operation labels as the protocol requires.

Do not substitute `SHA-512(msg)` for RFC 9380 expansion unless an existing protocol explicitly specifies that legacy construction. Do not hash a message and attempt strict element decoding.

## Random elements and scalars

Generate a random element with a maintained library's random-element API and a CSPRNG, or map 64 uniform random bytes. Do not rejection-sample random 32-byte encodings.

Derive scalars through a protocol-specified, domain-separated expander that produces 64 uniform bytes, then reduce modulo the scalar order. Reject and derive again when a protocol requires nonzero output.

## Shared elements

For a Diffie-Hellman-like construction:

1. Strictly decode the peer element.
2. Apply the protocol's identity check.
3. Perform constant-time scalar multiplication.
4. Encode the shared element canonically.
5. Feed that encoding and the full transcript/context to the protocol's KDF.

Never use the encoded shared element directly as a symmetric key. Specify authentication, contributory behavior, forward secrecy, and key confirmation separately.

## Common substitutions to reject

- Ed25519 or X25519 public bytes used as Ristretto encodings.
- Ed25519 keypairs reused as Ristretto keypairs without protocol-defined derivation.
- Scalars clamped instead of reduced modulo the group order.
- Noncanonical external elements or scalars silently reduced or masked.
- The high bit of an element encoding silently cleared.
- Manual cofactor clearing.
- Variable-time multiplication with secret inputs.
- One domain separation tag reused across distinct protocol roles.
- The many-to-one 64-byte map treated as a digest, commitment, or proof.
