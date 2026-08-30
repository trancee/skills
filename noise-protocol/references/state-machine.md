# Handshake state and ownership

Normative source: [Noise revision 34 Sections 5–8](https://noiseprotocol.org/noise.html).

State ownership:
- `HandshakeState`: role, remaining patterns, `s/e/rs/re`, one `SymmetricState`
- `SymmetricState`: `ck`, transcript hash `h`, handshake `CipherState`
- `CipherState`: 32-byte key `k` or empty plus 64-bit nonce `n`

Initialization hashes the exact protocol name, then prologue, then pre-message public keys in canonical order. Initiator and responder must provide identical protocol/prologue and role-correct pre-message keys.

Token effects:
- `e`: generate/send fresh ephemeral public key; mix into hash (and key in PSK mode)
- `s`: send local static, encrypted only after a key exists
- `ee/es/se/ss`: role-sensitive DH; mix output into chaining/encryption key and reset handshake cipher nonce
- `psk`: `MixKeyAndHash` a 32-byte PSK
- implicit payload after every message: encrypt-and-hash if a key exists, otherwise cleartext-and-hash

Call `WriteMessage`/`ReadMessage` exactly once per pattern arrow. An AEAD or DH error invalidates the whole handshake state. Never retry a failed message on that state.

`Split()` derives two independent transport states:
1. initiator -> responder
2. responder -> initiator

One-way protocols use only state 1. Delete the handshake state after split, retaining only `h` if the application needs channel binding. Use `h` because it commits to the public transcript; `ck`/traffic keys are secret and are not unique channel-binding identifiers under all invalid-key behaviors.

Static-key authentication has two layers: Noise proves possession according to the pattern; the application maps the received static public key to an acceptable identity.
